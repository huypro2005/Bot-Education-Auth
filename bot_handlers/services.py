"""
Logic nghiệp vụ bot (DB / user), không phụ thuộc python-telegram-bot handlers.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from telegram import User

from models import (
    Announcement,
    Assignment,
    ClassInfo,
    RequestJoinClass,
    RequestJoinClassStatus,
    Submission,
    StudentPoint,
    SubjectClass,
    SubjectInfo,
    TeleTeacherInfo,
    UserInfo,
    UserRole,
)


def display_name_from_telegram(tg_user: User) -> str:
    """Họ tên hiển thị mặc định từ profile Telegram."""
    parts = [tg_user.first_name or "", tg_user.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    if name:
        return name[:255]
    if tg_user.username:
        return tg_user.username[:255]
    return "Người dùng"


def get_or_create_user(db: Session, tg_user: User) -> UserInfo:
    """
    Whitelist TeleTeacherInfo -> users.role = teacher; không -> student.

    - Nâng HS -> GV: đặt role teacher, bỏ class_id.
    - Đồng bộ username Telegram khi đổi.
    """
    telegram_id = str(tg_user.id)
    username = tg_user.username
    full_name = display_name_from_telegram(tg_user)

    tele = db.query(TeleTeacherInfo).filter(TeleTeacherInfo.telegram_id == telegram_id).first()
    if tele is not None:
        row = db.query(UserInfo).filter(UserInfo.telegram_id == telegram_id).first()
        if row is not None:
            if row.role != UserRole.TEACHER:
                row.role = UserRole.TEACHER
                row.class_id = None
                row.username = username
                db.commit()
                db.refresh(row)
            elif row.username != username:
                row.username = username
                db.commit()
                db.refresh(row)
            return row

        teacher = UserInfo(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=UserRole.TEACHER,
        )
        db.add(teacher)
        try:
            db.commit()
            db.refresh(teacher)
            return teacher
        except IntegrityError:
            db.rollback()
            existing = db.query(UserInfo).filter(UserInfo.telegram_id == telegram_id).first()
            if existing is not None:
                return existing
            raise

    row = db.query(UserInfo).filter(UserInfo.telegram_id == telegram_id).first()
    if row is not None:
        if username is not None and row.username != username:
            row.username = username
            db.commit()
            db.refresh(row)
        return row

    student = UserInfo(
        telegram_id=telegram_id,
        username=username or "",
        full_name=full_name,
        role=UserRole.STUDENT,
    )
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError:
        db.rollback()
        existing = db.query(UserInfo).filter(UserInfo.telegram_id == telegram_id).first()
        if existing is not None:
            return existing
        raise


def update_student_full_name(db: Session, tg_user: User, full_name: str) -> bool:
    user = get_or_create_user(db, tg_user)
    if user.role != UserRole.STUDENT:
        return False
    user.full_name = full_name[:255]
    db.commit()
    return True


def update_teacher_full_name(db: Session, tg_user: User, full_name: str) -> bool:
    user = get_or_create_user(db, tg_user)
    if user.role != UserRole.TEACHER:
        return False
    user.full_name = full_name[:255]
    db.commit()
    return True


# --- Tham gia lớp (RequestJoinClass) ---


def list_classes_with_homeroom(db: Session) -> list[ClassInfo]:
    """Các lớp đã có giáo viên chủ nhiệm."""
    return (
        db.query(ClassInfo)
        .filter(ClassInfo.homeroom_teacher_id.isnot(None))
        .order_by(ClassInfo.name.asc())
        .all()
    )


def student_join_block_reason(db: Session, student: UserInfo) -> str | None:
    """
    Trả về thông báo tiếng Việt nếu không được gửi yêu cầu; None nếu được phép.
    """
    if student.role != UserRole.STUDENT:
        return "Chỉ học sinh mới dùng được chức năng này."
    if student.class_id is not None:
        return "Bạn đã tham gia lớp học rồi."
    pending = (
        db.query(RequestJoinClass)
        .filter(
            RequestJoinClass.student_id == student.id,
            RequestJoinClass.status == RequestJoinClassStatus.PENDING,
        )
        .first()
    )
    if pending is not None:
        return "Bạn đã có yêu cầu đang chờ giáo viên duyệt."
    return None


def create_join_request(db: Session, student: UserInfo, class_id: int) -> tuple[bool, str]:
    """
    Tạo yêu cầu tham gia lớp (pending). Trả (True, thông báo thành công) hoặc (False, lỗi).
    """
    block = student_join_block_reason(db, student)
    if block is not None:
        return False, block

    cls = db.get(ClassInfo, class_id)
    if cls is None or cls.homeroom_teacher_id is None:
        return False, "Lớp không tồn tại hoặc chưa có giáo viên chủ nhiệm."

    dup = (
        db.query(RequestJoinClass)
        .filter(
            RequestJoinClass.student_id == student.id,
            RequestJoinClass.class_id == class_id,
            RequestJoinClass.status == RequestJoinClassStatus.PENDING,
        )
        .first()
    )
    if dup is not None:
        return False, "Bạn đã gửi yêu cầu vào lớp này, vui lòng chờ giáo viên duyệt."

    req = RequestJoinClass(
        student_id=student.id,
        class_id=class_id,
        status=RequestJoinClassStatus.PENDING,
    )
    db.add(req)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False, "Không thể tạo yêu cầu (dữ liệu trùng)."
    return (
        True,
        f"Đã gửi yêu cầu tham gia lớp «{cls.name}». Vui lòng chờ giáo viên chủ nhiệm duyệt.",
    )


def list_pending_join_requests_for_homeroom_teacher(
    db: Session, teacher_user_id: int
) -> list[RequestJoinClass]:
    """Yêu cầu pending mà GV là GVCN của lớp đó."""
    return (
        db.query(RequestJoinClass)
        .join(ClassInfo, RequestJoinClass.class_id == ClassInfo.id)
        .filter(ClassInfo.homeroom_teacher_id == teacher_user_id)
        .filter(RequestJoinClass.status == RequestJoinClassStatus.PENDING)
        .options(
            joinedload(RequestJoinClass.student),
            joinedload(RequestJoinClass.class_info),
        )
        .order_by(RequestJoinClass.created_at.asc())
        .all()
    )


def resolve_join_request(
    db: Session,
    request_id: int,
    teacher_user_id: int,
    approve: bool,
) -> tuple[bool, str, UserInfo | None, ClassInfo | None]:
    """
    GV chủ nhiệm duyệt / từ chối. Trả (ok, message_cho_gv, student, class_info) để gửi thông báo HS.
    """
    req = (
        db.query(RequestJoinClass)
        .options(
            joinedload(RequestJoinClass.student),
            joinedload(RequestJoinClass.class_info),
        )
        .filter(RequestJoinClass.id == request_id)
        .first()
    )
    if req is None or req.status != RequestJoinClassStatus.PENDING:
        return False, "Yêu cầu không tồn tại hoặc đã xử lý.", None, None

    cls = req.class_info
    if cls is None or cls.homeroom_teacher_id != teacher_user_id:
        return False, "Bạn không phải giáo viên chủ nhiệm của lớp này.", None, None

    student = req.student
    if student is None or student.role != UserRole.STUDENT:
        return False, "Tài khoản học sinh không hợp lệ.", None, None

    class_name = cls.name

    if approve:
        if student.class_id is not None:
            return False, "Học sinh đã thuộc một lớp khác.", None, None

        student.class_id = cls.id
        req.status = RequestJoinClassStatus.APPROVED
        cls.total_students = (cls.total_students or 0) + 1

        others = (
            db.query(RequestJoinClass)
            .filter(
                RequestJoinClass.student_id == student.id,
                RequestJoinClass.id != req.id,
                RequestJoinClass.status == RequestJoinClassStatus.PENDING,
            )
            .all()
        )
        for o in others:
            o.status = RequestJoinClassStatus.REJECTED
    else:
        req.status = RequestJoinClassStatus.REJECTED

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False, "Không thể cập nhật (lỗi dữ liệu).", None, None

    db.refresh(req)
    db.refresh(student)
    db.refresh(cls)
    return True, "", student, cls


def list_teacher_managed_classes(db: Session, teacher_user_id: int) -> list[dict]:
    """Danh sách lớp giáo viên quản lý (chủ nhiệm hoặc đang dạy môn)."""
    rows = (
        db.query(ClassInfo)
        .options(joinedload(ClassInfo.subject_classes).joinedload(SubjectClass.subject_info))
        .outerjoin(SubjectClass, SubjectClass.class_id == ClassInfo.id)
        .outerjoin(SubjectInfo, SubjectInfo.id == SubjectClass.subject_id)
        .filter(
            (ClassInfo.homeroom_teacher_id == teacher_user_id)
            | (SubjectClass.teacher_id == teacher_user_id)
        )
        .distinct(ClassInfo.id)
        .order_by(ClassInfo.name.asc())
        .all()
    )

    result: list[dict] = []
    for cls in rows:
        taught_subjects = {
            sc.subject_info.name
            for sc in cls.subject_classes
            if sc.teacher_id == teacher_user_id and sc.subject_info is not None
        }
        result.append(
            {
                "class_id": cls.id,
                "class_name": cls.name,
                "is_homeroom": cls.homeroom_teacher_id == teacher_user_id,
                "subjects": sorted(taught_subjects),
            }
        )
    return result


def list_homeroom_students_for_teacher(db: Session, teacher_user_id: int) -> list[dict]:
    """Danh sách học sinh theo từng lớp mà giáo viên đang chủ nhiệm."""
    classes = (
        db.query(ClassInfo)
        .filter(ClassInfo.homeroom_teacher_id == teacher_user_id)
        .order_by(ClassInfo.name.asc())
        .all()
    )
    result: list[dict] = []
    for cls in classes:
        students = (
            db.query(UserInfo)
            .filter(
                UserInfo.class_id == cls.id,
                UserInfo.role == UserRole.STUDENT,
            )
            .order_by(UserInfo.full_name.asc())
            .all()
        )
        result.append({"class_id": cls.id, "class_name": cls.name, "students": students})
    return result


def list_students_in_class(db: Session, class_id: int) -> list[UserInfo]:
    """Danh sách học sinh đã thuộc lớp (để gửi thông báo)."""
    return (
        db.query(UserInfo)
        .filter(
            UserInfo.class_id == class_id,
            UserInfo.role == UserRole.STUDENT,
        )
        .order_by(UserInfo.full_name.asc())
        .all()
    )


def create_announcement_for_teacher(
    db: Session,
    teacher_user_id: int,
    class_id: int,
    message: str,
) -> tuple[bool, Announcement | None]:
    """Tạo bản ghi Announcement nếu teacher có quyền trên lớp."""
    allowed = (
        db.query(ClassInfo.id)
        .outerjoin(SubjectClass, SubjectClass.class_id == ClassInfo.id)
        .filter(
            ClassInfo.id == class_id,
            (
                (ClassInfo.homeroom_teacher_id == teacher_user_id)
                | (SubjectClass.teacher_id == teacher_user_id)
            ),
        )
        .first()
    )
    if allowed is None:
        return False, None
    row = Announcement(
        class_id=class_id,
        teacher_id=teacher_user_id,
        message=message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return True, row


def list_recent_announcements_for_student(
    db: Session, student: UserInfo, *, days: int = 7
) -> list[Announcement]:
    """Thông báo của lớp học sinh đang học, trong `days` ngày gần nhất (mới nhất trước)."""
    if student.role != UserRole.STUDENT or student.class_id is None:
        return []
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.query(Announcement)
        .options(joinedload(Announcement.teacher_info))
        .filter(
            Announcement.class_id == student.class_id,
            Announcement.created_at >= since,
        )
        .order_by(Announcement.created_at.desc())
        .all()
    )


def list_teacher_subject_classes(db: Session, teacher_user_id: int) -> list[dict]:
    """Danh sách lớp - môn mà giáo viên đang dạy."""
    rows = (
        db.query(SubjectClass)
        .options(
            joinedload(SubjectClass.class_info),
            joinedload(SubjectClass.subject_info),
        )
        .filter(SubjectClass.teacher_id == teacher_user_id)
        .order_by(SubjectClass.class_id.asc(), SubjectClass.subject_id.asc())
        .all()
    )
    result: list[dict] = []
    for row in rows:
        if row.class_info is None or row.subject_info is None:
            continue
        result.append(
            {
                "class_id": row.class_id,
                "class_name": row.class_info.name,
                "subject_id": row.subject_id,
                "subject_name": row.subject_info.name,
                "subject_class_id": row.id,
            }
        )
    return result


def create_assignment_for_teacher(
    db: Session,
    teacher_user_id: int,
    class_id: int,
    subject_id: int,
    title: str,
    instruction_text: str,
    deadline: datetime | None,
    file_path: str | None = None,
) -> tuple[bool, str, int | None]:
    """Tạo assignment cho đúng lớp-môn mà giáo viên được phân công dạy."""
    subject_class = (
        db.query(SubjectClass)
        .filter(
            SubjectClass.class_id == class_id,
            SubjectClass.subject_id == subject_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .first()
    )
    if subject_class is None:
        return False, "Bạn không được phân công dạy môn này cho lớp đã chọn.", None

    row = Assignment(
        title=title[:255],
        instruction_text=instruction_text,
        file_path=file_path,
        deadline=deadline,
        teacher_id=teacher_user_id,
        subject_class_id=subject_class.id,
    )
    db.add(row)
    db.commit()
    return True, "Đã giao bài thành công.", row.id


def create_assignment_for_teacher_by_subject_class(
    db: Session,
    *,
    teacher_user_id: int,
    subject_class_id: int,
    title: str,
    instruction_text: str,
    deadline: datetime | None,
    file_path: str | None = None,
) -> tuple[bool, str, int | None]:
    """Tạo assignment theo `subject_class_id`, chỉ cho phép nếu đúng giáo viên."""
    subject_class = (
        db.query(SubjectClass)
        .filter(
            SubjectClass.id == subject_class_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .first()
    )
    if subject_class is None:
        return False, "Bạn không được phân công môn này cho lớp đã chọn.", None

    row = Assignment(
        title=title[:255],
        instruction_text=instruction_text,
        file_path=file_path,
        deadline=deadline,
        teacher_id=teacher_user_id,
        subject_class_id=subject_class.id,
    )
    db.add(row)
    db.commit()
    return True, "Đã giao bài thành công.", row.id

def get_class_info(db: Session, class_id: int) -> ClassInfo | None:
    return db.query(ClassInfo).filter(ClassInfo.id == class_id).first()

def get_subject_info(db: Session, subject_id: int) -> SubjectInfo | None:
    return db.query(SubjectInfo).filter(SubjectInfo.id == subject_id).first()


def list_active_assignments_for_student(db: Session, student: UserInfo) -> list[dict]:
    """Danh sách bài tập còn hạn của lớp học sinh."""
    if student.role != UserRole.STUDENT or student.class_id is None:
        return []
    now = datetime.now(timezone.utc)
    rows = (
        db.query(Assignment, SubjectInfo.name)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(SubjectInfo, SubjectInfo.id == SubjectClass.subject_id)
        .filter(SubjectClass.class_id == student.class_id)
        .filter(Assignment.deadline.isnot(None), Assignment.deadline >= now)
        .order_by(Assignment.deadline.asc(), Assignment.id.asc())
        .all()
    )
    result: list[dict] = []
    for assignment, subject_name in rows:
        result.append(
            {
                "id": assignment.id,
                "subject_name": subject_name,
                "title": assignment.title,
                "created_at": assignment.created_at,
                "deadline": assignment.deadline,
            }
        )
    return result


def get_assignment_detail_for_student(
    db: Session, student: UserInfo, assignment_id: int
) -> tuple[Assignment | None, str | None]:
    """Chi tiết bài tập nếu thuộc lớp của học sinh."""
    if student.role != UserRole.STUDENT or student.class_id is None:
        return None, None
    row = (
        db.query(Assignment, SubjectInfo.name)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(SubjectInfo, SubjectInfo.id == SubjectClass.subject_id)
        .filter(Assignment.id == assignment_id, SubjectClass.class_id == student.class_id)
        .first()
    )
    if row is None:
        return None, None
    assignment, subject_name = row
    return assignment, subject_name


def list_teacher_assignments_for_subject_class(
    db: Session, teacher_user_id: int, subject_class_id: int
) -> list[dict]:
    """Danh sách assignment của giáo viên theo `subject_class_id`."""
    rows = (
        db.query(Assignment)
        .join(
            SubjectClass, Assignment.subject_class_id == SubjectClass.id
        )
        .filter(
            SubjectClass.id == subject_class_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .order_by(Assignment.deadline.desc(), Assignment.created_at.desc(), Assignment.id.asc())
        .all()
    )
    result: list[dict] = []
    for a in rows:
        result.append(
            {
                "id": a.id,
                "title": a.title,
                "created_at": a.created_at,
                "deadline": a.deadline,
                "file_path": a.file_path,
            }
        )
    return result


def get_teacher_assignment_detail(
    db: Session,
    teacher_user_id: int,
    assignment_id: int,
) -> dict | None:
    """Chi tiết assignment (chỉ khi assignment thuộc subject_class của giáo viên)."""
    row = (
        db.query(Assignment, ClassInfo.name, SubjectInfo.name)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(ClassInfo, ClassInfo.id == SubjectClass.class_id)
        .join(SubjectInfo, SubjectInfo.id == SubjectClass.subject_id)
        .filter(Assignment.id == assignment_id, SubjectClass.teacher_id == teacher_user_id)
        .first()
    )
    if row is None:
        return None
    assignment, class_name, subject_name = row
    return {
        "assignment": assignment,
        "class_name": class_name,
        "subject_name": subject_name,
    }


def list_teacher_submissions_for_assignment(
    db: Session, teacher_user_id: int, assignment_id: int
) -> list[dict]:
    """Danh sách submission của assignment (chỉ nếu teacher có quyền chấm)."""
    rows = (
        db.query(Submission, UserInfo.full_name)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(UserInfo, Submission.student_id == UserInfo.id)
        .filter(
            Assignment.id == assignment_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .order_by(UserInfo.full_name.asc(), Submission.id.asc())
        .all()
    )
    return [{"id": s.id, "student_name": name} for s, name in rows]


def list_student_submissions_results(db: Session, student: UserInfo) -> list[dict]:
    """Kết quả học tập của học sinh: môn, tiêu đề bài, điểm GV/AI, thời gian nộp."""
    if student.role != UserRole.STUDENT:
        return []
    rows = (
        db.query(
            Submission,
            Assignment.title,
            SubjectInfo.name,
        )
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(SubjectInfo, SubjectClass.subject_id == SubjectInfo.id)
        .filter(Submission.student_id == student.id)
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .all()
    )
    result: list[dict] = []
    for sub, assignment_title, subject_name in rows:
        result.append(
            {
                "submission_id": sub.id,
                "subject_name": subject_name,
                "assignment_title": assignment_title,
                "teacher_score": sub.teacher_score,
                "ai_score": sub.ai_score,
                "submitted_at": sub.submitted_at,
            }
        )
    return result


def get_teacher_submission_detail(
    db: Session, teacher_user_id: int, submission_id: int
) -> dict | None:
    """Chi tiết submission (chỉ khi submission thuộc assignment của giáo viên)."""
    row = (
        db.query(
            Submission,
            Assignment,
            UserInfo.full_name,
        )
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(UserInfo, Submission.student_id == UserInfo.id)
        .filter(
            Submission.id == submission_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .first()
    )
    if row is None:
        return None
    submission, assignment, student_name = row
    return {
        "submission": submission,
        "assignment": assignment,
        "student_name": student_name,
    }


def set_teacher_score_for_submission(
    db: Session,
    teacher_user_id: int,
    submission_id: int,
    score: float,
) -> tuple[bool, str]:
    """Cập nhật điểm giáo viên cho submission (teacher chỉ chấm assignment thuộc lớp/môn của mình)."""
    sub = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .filter(
            Submission.id == submission_id,
            SubjectClass.teacher_id == teacher_user_id,
        )
        .first()
    )
    if sub is None:
        return False, "Không tìm thấy submission hoặc bạn không có quyền chấm."

    sub.teacher_score = score
    db.commit()
    return True, f"Đã chấm điểm {score}/10 cho submission {submission_id}."


def list_teacher_classes_for_conduct(db: Session, teacher_user_id: int) -> list[dict]:
    """Danh sách lớp mà GV được phép cộng/trừ điểm rèn luyện (dạy hoặc chủ nhiệm)."""
    rows = list_teacher_managed_classes(db, teacher_user_id)
    # list_teacher_managed_classes đã distinct theo class_id
    return rows


def teacher_can_modify_student_conduct(
    db: Session, teacher_user_id: int, student_id: int
) -> tuple[bool, UserInfo | None]:
    student = (
        db.query(UserInfo)
        .filter(UserInfo.id == student_id, UserInfo.role == UserRole.STUDENT)
        .first()
    )
    if student is None or student.class_id is None:
        return False, None

    cls_id = student.class_id
    allowed = (
        db.query(ClassInfo.id)
        .outerjoin(SubjectClass, SubjectClass.class_id == ClassInfo.id)
        .filter(
            ClassInfo.id == cls_id,
            or_(
                ClassInfo.homeroom_teacher_id == teacher_user_id,
                SubjectClass.teacher_id == teacher_user_id,
            ),
        )
        .first()
    )
    return (allowed is not None), student


def list_students_conduct_points_for_class(
    db: Session, teacher_user_id: int, class_id: int
) -> list[dict]:
    """Danh sách học sinh + tổng điểm rèn luyện của lớp (nếu giáo viên có quyền)."""
    allowed = (
        db.query(ClassInfo.id)
        .outerjoin(SubjectClass, SubjectClass.class_id == ClassInfo.id)
        .filter(
            ClassInfo.id == class_id,
            or_(
                ClassInfo.homeroom_teacher_id == teacher_user_id,
                SubjectClass.teacher_id == teacher_user_id,
            ),
        )
        .first()
    )
    if allowed is None:
        return []

    rows = (
        db.query(
            UserInfo.id,
            UserInfo.full_name,
            UserInfo.telegram_id,
            UserInfo.username,
            func.coalesce(func.sum(StudentPoint.amount), 0).label("total_points"),
        )
        .outerjoin(StudentPoint, StudentPoint.student_id == UserInfo.id)
        .filter(UserInfo.class_id == class_id, UserInfo.role == UserRole.STUDENT)
        .group_by(
            UserInfo.id,
            UserInfo.full_name,
            UserInfo.telegram_id,
            UserInfo.username,
        )
        .order_by(UserInfo.full_name.asc())
        .all()
    )
    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "student_id": row.id,
                "full_name": row.full_name,
                "telegram_id": row.telegram_id,
                "username": row.username,
                "total_points": float(row.total_points),
            }
        )
    return result


def apply_student_conduct_points(
    db: Session,
    *,
    teacher_user_id: int,
    student_id: int,
    delta: int,
    reason: str,
) -> tuple[bool, str, int | None]:
    """Cộng/trừ 1 điểm rèn luyện và nhắn cho học sinh."""
    if delta not in (1, -1):
        return False, "Mỗi lần chỉ được cộng hoặc trừ 1 điểm.", None
    allowed, student = teacher_can_modify_student_conduct(
        db, teacher_user_id, student_id
    )
    if not allowed or student is None:
        return False, "Bạn không có quyền thao tác với học sinh này.", None

    row = StudentPoint(
        student_id=student_id,
        amount=delta,
        reason=reason[:1000],
    )
    db.add(row)
    db.commit()
    return True, "Đã cập nhật điểm rèn luyện.", int(student.telegram_id)


def get_assignment_submission_context(
    db: Session, student: UserInfo, assignment_id: int
) -> dict | None:
    """Lấy ngữ cảnh bài tập để nộp/chấm nếu học sinh thuộc đúng lớp."""
    if student.role != UserRole.STUDENT or student.class_id is None:
        return None
    row = (
        db.query(Assignment, SubjectClass, ClassInfo, SubjectInfo)
        .join(SubjectClass, Assignment.subject_class_id == SubjectClass.id)
        .join(ClassInfo, ClassInfo.id == SubjectClass.class_id)
        .join(SubjectInfo, SubjectInfo.id == SubjectClass.subject_id)
        .filter(Assignment.id == assignment_id, SubjectClass.class_id == student.class_id)
        .first()
    )
    if row is None:
        return None
    assignment, _, class_info, subject_info = row
    return {
        "assignment": assignment,
        "class_name": class_info.name,
        "subject_name": subject_info.name,
        "assignment_title": assignment.title,
        "assignment_instruction": assignment.instruction_text,
        "assignment_file_path": assignment.file_path,
        "deadline": assignment.deadline,
    }


def upsert_submission_for_student(
    db: Session,
    *,
    assignment_id: int,
    student_id: int,
    file_path: str,
    ai_feedback: str,
    ai_score: float | None,
) -> tuple[bool, str]:
    """Ghi đè bài nộp cũ (nếu có) và lưu feedback AI."""
    old = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id,
        )
        .first()
    )
    if old is not None and old.file_path and old.file_path != file_path:
        try:
            if os.path.exists(old.file_path):
                os.remove(old.file_path)
        except OSError:
            pass
        old.file_path = file_path
        old.ai_feedback = ai_feedback
        old.ai_score = ai_score
        old.teacher_score = None
        old.submitted_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Đã cập nhật bài nộp mới."

    if old is not None:
        old.ai_feedback = ai_feedback
        old.ai_score = ai_score
        old.teacher_score = None
        old.submitted_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Đã cập nhật bài nộp."

    row = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        file_path=file_path,
        ai_feedback=ai_feedback,
        ai_score=ai_score,
    )
    db.add(row)
    db.commit()
    return True, "Đã nộp bài thành công."


def upsert_submission_file_only_for_student(
    db: Session,
    *,
    assignment_id: int,
    student_id: int,
    file_path: str,
) -> tuple[bool, str]:
    """
    Chỉ cập nhật file nộp (và thời gian) nhưng KHÔNG thay đổi ai_score/ai_feedback.
    Dùng khi AI không trích xuất được nội dung bài làm.
    """
    old = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id,
        )
        .first()
    )
    if old is not None and old.file_path and old.file_path != file_path:
        try:
            if os.path.exists(old.file_path):
                os.remove(old.file_path)
        except OSError:
            pass
        old.file_path = file_path
        old.submitted_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Đã cập nhật file bài nộp."

    if old is not None:
        old.submitted_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Đã cập nhật bài nộp."

    row = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        file_path=file_path,
    )
    db.add(row)
    db.commit()
    return True, "Đã nộp bài thành công."