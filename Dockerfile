# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13.3
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Tạo user không có đặc quyền và cấp quyền sở hữu cho các thư mục dữ liệu
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/uploads /app/exports \
    && chown -R appuser:appuser /app/uploads /app/exports

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

COPY . .

# Đổi owner cho toàn bộ mã nguồn sang appuser
RUN chown -R appuser:appuser /app

# Chuyển sang user an toàn
USER appuser

EXPOSE 8000

CMD ["python", "main.py"]