import os
from typing import Optional, Tuple

import fitz
from openai import OpenAI


def _read_pdf_text(path: Optional[str], max_chars: int = 12000) -> str:
    if not path:
        return ""
    try:
        with fitz.open(path) as doc:
            chunks = [page.get_text("text") for page in doc]
        text = "\n".join(chunks).strip()
        if len(text) > max_chars:
            return text[:max_chars] + "\n...[truncated]..."
        return text
    except Exception:
        return ""


def grade_submission_with_ai(
    *,
    subject_name: str,
    assignment_title: str,
    assignment_instruction: str,
    assignment_file_path: Optional[str],
    submission_file_path: str,
) -> Tuple[str, Optional[float]]:
    """Return feedback, score for a submission."""
    assignment_file_text = _read_pdf_text(assignment_file_path)
    submission_text = _read_pdf_text(submission_file_path)

    # Nếu bot không trích xuất được nội dung bài làm (thường do PDF là scan/ảnh),
    # trả token để bot xử lý theo luồng "chờ giáo viên chấm" (không cập nhật ai_score/ai_feedback).
    if not submission_text or len(submission_text.strip()) < 20:
        return ("__AI_READ_FAILED__", None)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return (
            "Tôi đã nhận bài của em. Hiện hệ thống AI chưa sẵn sàng nên chưa chấm tự động được. Em chờ giáo viên xem chi tiết giúp em nhé.",
            None,
        )

    client = OpenAI(api_key=api_key)
    prompt = (
        "Em là học sinh, người chấm xưng 'tôi' và gọi học sinh là 'em'. "
        "Hãy chấm bài theo đúng yêu cầu đề bài và đúng ngữ cảnh môn học.\n\n"
        f"Môn học: {subject_name}\n"
        f"Tiêu đề đề bài: {assignment_title}\n"
        f"Hướng dẫn đề bài: {assignment_instruction}\n"
        f"Nội dung đề từ file (nếu có):\n{assignment_file_text}\n\n"
        f"Nội dung bài làm của em (trích từ file nộp):\n{submission_text}\n\n"
        "Yêu cầu đầu ra:\n"
        "1) Nhận xét ngắn gọn mức độ đáp ứng đề.\n"
        "2) Chỉ ra lỗi/thiếu sót chính (nếu có).\n"
        "3) Gợi ý cụ thể để em cải thiện.\n"
        "4) Nếu bài làm lệch yêu cầu đề, nêu rõ và hướng dẫn em làm đúng.\n"
        "5) Cho điểm tham khảo thang 10.\n"
        "Trả kết quả theo đúng định dạng:\n"
        "SCORE: <so_diem_tu_0_den_10_hoac_NA>\n"
        "FEEDBACK:\n"
        "<noi_dung nhan xet>"
    )

    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            temperature=0.2,
        )
        content = (resp.output_text or "").strip()
    except Exception:
        return (
            "Tôi đã nhận bài của em nhưng tạm thời không chấm AI được lúc này. Em thử nộp lại sau hoặc chờ giáo viên phản hồi nhé.",
            None,
        )

    score: Optional[float] = None
    feedback = content
    lines = content.splitlines()
    if lines and lines[0].startswith("SCORE:"):
        raw = lines[0].replace("SCORE:", "").strip()
        if raw.upper() != "NA":
            try:
                score = float(raw)
            except ValueError:
                score = None
        if len(lines) > 1 and lines[1].startswith("FEEDBACK:"):
            feedback = "\n".join(lines[2:]).strip() or content
    return feedback, score
