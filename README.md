# WebCuaMeApplication

Backend **FastAPI** + bot **Telegram** + SQLAlchemy ORM + MySQL. Hệ thống quản lý trường học với 2 kênh tương tác: Admin Web (REST API) và Telegram Bot cho giáo viên/học sinh.

---

## Tài liệu dự án

| File | Nội dung |
|---|---|
| [architect.md](architect.md) | Kiến trúc toàn hệ thống, sơ đồ DB, luồng nghiệp vụ, đánh giá điểm mạnh/yếu |
| [ADMIN_API.md](ADMIN_API.md) | Tất cả REST API `/admin/*` — endpoint, request body, response |
| [errors_fix.md](errors_fix.md) | Các lỗi deploy đã gặp và cách fix (Docker, permissions, cron, backup) |
| [docs/PHAT_TRIEN_BOT.md](docs/PHAT_TRIEN_BOT.md) | Hướng dẫn phát triển Telegram bot — handlers, services, callback_data |
| [ConnectServer.md](ConnectServer.md) | Thông tin kết nối server production |

---

## Yêu cầu

- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose (khuyến nghị cho production)

---

## Chạy bằng Docker Compose (Production)

```bash
# 1. Tạo file .env từ mẫu
cp .env.example .env
# Điền đầy đủ các biến trong .env

# 2. Build và khởi động
docker compose up -d --build

# 3. Kiểm tra log
docker compose logs -f
```

**3 services:**
- `student-management-backend` — FastAPI + Telegram bot (port 8000)
- `student-management-mysql` — MySQL 8.0 (port theo `MYSQL_PORT`)
- `student-management-backup` — Cron backup DB hàng ngày vào `db_backups/`

---

## Chạy local (Development)

```bash
cd WebCuaMeApplication
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

Tạo file `.env`:

```env
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/dbname
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
```

Chạy:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: <http://127.0.0.1:8000/docs>

---

## Biến môi trường

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `DATABASE_URL` | Có | `mysql+pymysql://user:pass@host:port/db` |
| `TELEGRAM_BOT_TOKEN` | Có | Token bot Telegram |
| `OPENAI_API_KEY` | Không | AI chấm bài; nếu thiếu sẽ báo thông báo thay vì crash |
| `MYSQL_ROOT_PASSWORD` | Có (Docker) | Password root MySQL |
| `MYSQL_DATABASE` | Có (Docker) | Tên database |
| `MYSQL_USER` | Có (Docker) | App user MySQL |
| `MYSQL_PASSWORD` | Có (Docker) | Password app user |
| `MYSQL_PORT` | Có (Docker) | Port expose ra host |

---

## Restore database

**Lần đầu deploy** (volume chưa có data) — đặt file `.sql` vào `restore/` trước khi `docker compose up`:

```bash
cp backup.sql ./restore/
docker compose up -d
```

**Restore vào DB đang chạy:**

```bash
docker exec -i student-management-mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" \
  < ./restore/backup.sql
```

---

## Cấu trúc thư mục

```
WebCuaMeApplication/
├── main.py                  # Entrypoint — FastAPI + Telegram bot lifespan
├── models.py                # ORM models (source of truth)
├── database.py              # Engine, SessionLocal, init_db()
├── app/
│   ├── api/admin.py         # Router /admin/*
│   ├── service/admin.py     # Business logic admin
│   └── schemas/admin.py     # Pydantic schemas
├── bot_handlers/
│   ├── bot_handlers.py      # Telegram handlers
│   └── services.py          # Bot business logic (DB queries)
├── AI/
│   ├── grader.py            # Auto-grade PDF via GPT-4.1-mini
│   └── conduct_learning_evaluator.py  # AI đánh giá học lực/hạnh kiểm
├── backup/                  # Script backup & crontab
├── db_backups/              # Output file backup (.sql)
├── uploads/                 # File bài nộp của học sinh
├── exports/                 # File Excel xuất từ bot
└── mysql/init/              # SQL scripts chạy khi khởi tạo DB
```

---

## Lỗi deploy đã gặp

Xem chi tiết tại **[errors_fix.md](errors_fix.md)**. Tóm tắt:

| Lỗi | Nguyên nhân | File sửa |
|---|---|---|
| Backup file không thấy trên host | `umask 077` trong `backup.sh` | `backup/backup.sh` |
| `apt-get: command not found` trong backup container | `mysql:8.0` dùng Oracle Linux, không có apt | `compose.yaml` |
| `crontab: premature EOF` | `crontab.txt` thiếu trailing newline | `backup/crontab.txt` |
| `uploads/exports` không accessible từ host | Dockerfile tạo `appuser` UID 10001 gây UID mismatch | `Dockerfile` + `compose.yaml` |
| MySQL init script không chạy lại | `docker-entrypoint-initdb.d` chỉ chạy 1 lần khi volume trống | Dùng `docker exec` để restore thủ công |
