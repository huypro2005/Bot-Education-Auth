# Errors Fix — Deploy Knowledge Base

Tài liệu ghi lại toàn bộ lỗi phát sinh trong quá trình deploy dự án **WebCuaMeApplication** lên production bằng Docker Compose, nguyên nhân gốc rễ, và cách đã sửa.

---

## 1. Backup files ghi thành công nhưng không thấy trên máy host

**Triệu chứng**
- Container backup chạy không lỗi, log báo `Backup successful`
- Mở thư mục `db_backups/` trên máy host không thấy file nào

**Nguyên nhân**
- File `backup/backup.sh` có dòng `umask 077` ngay sau `set -eu`
- `umask 077` khiến mọi file được tạo có permission `600` (chỉ owner đọc được)
- Khi container chạy với user root (UID 0) bên trong nhưng host user có UID khác → file bị tạo ra với permission quá hạn chế, host không đọc/thấy được

**Fix — `backup/backup.sh`**
```sh
# TRƯỚC (lỗi)
set -eu
umask 077
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# SAU (đã sửa)
set -eu
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
```

**Kiến thức rút ra**
> `umask` trong script shell ảnh hưởng đến permission của tất cả file được tạo sau đó trong cùng process. `umask 077` = chỉ owner có full quyền, group và others không có quyền gì. Trong môi trường Docker bind-mount, user bên trong container và bên ngoài host thường có UID khác nhau, nên file tạo ra bởi container root có thể không accessible từ host.

---

## 2. Container backup báo lỗi `apt-get: command not found`

**Triệu chứng**
```
sh: line 1: apt-get: command not found
sh: line 1: apt-get: command not found
...  (lặp lại liên tục vì restart: always)
```

**Nguyên nhân**
- Service `backup` dùng image `mysql:8.0`
- Từ MySQL 8.0.28 trở đi, Oracle chuyển base image từ **Debian** sang **Oracle Linux 8**
- Oracle Linux dùng package manager `microdnf` / `dnf`, **không có** `apt-get`
- Cron daemon trên Oracle Linux tên là `crond`, **không phải** `cron`

**Fix — `compose.yaml` (backup entrypoint)**
```yaml
# TRƯỚC (lỗi)
entrypoint: >
  sh -c "
  apt-get update &&
  apt-get install -y cron &&
  chmod +x /backup/backup.sh &&
  chmod 755 /db_backups &&
  crontab /backup/crontab.txt &&
  cron &&
  tail -f /dev/null
  "

# SAU (đã sửa)
entrypoint: >
  sh -c "
  microdnf install -y cronie &&
  chmod +x /backup/backup.sh &&
  chmod 755 /db_backups &&
  crontab /backup/crontab.txt &&
  crond -n
  "
```

**Kiến thức rút ra**
> Không nên giả định base OS của một Docker image mà không kiểm tra. Image `mysql:8.x` đã đổi base từ Debian sang Oracle Linux — điều này thay đổi hoàn toàn package manager và tên daemon. `crond -n` chạy cron ở chế độ foreground nên không cần `tail -f /dev/null` thêm vào sau.

| OS / Distro | Package manager | Cron package | Cron daemon |
|---|---|---|---|
| Debian / Ubuntu | `apt-get` | `cron` | `cron -f` |
| Oracle Linux / RHEL / CentOS | `microdnf` / `dnf` | `cronie` | `crond -n` |
| Alpine | `apk` | `cronie` | `crond -f` |

---

## 3. Crontab báo lỗi `premature EOF` — không install được

**Triệu chứng**
```
"/backup/crontab.txt":1: premature EOF
Invalid crontab file, can't install.
Nothing to do.
```

**Nguyên nhân**
- File `backup/crontab.txt` không có **dòng trắng ở cuối file** (trailing newline)
- POSIX yêu cầu mỗi dòng trong crontab phải kết thúc bằng `\n`, bao gồm cả dòng cuối
- Thiếu newline khiến `crontab` parser báo EOF sớm và từ chối cài

**Fix — `backup/crontab.txt`**
```
# TRƯỚC (thiếu newline cuối)
0 2 * * * /backup/backup.sh >> /var/log/backup.log 2>&1[EOF]

# SAU (có newline cuối)
0 2 * * * /backup/backup.sh >> /var/log/backup.log 2>&1
[dòng trắng]
```

**Kiến thức rút ra**
> Crontab là POSIX text file — mọi dòng phải kết thúc bằng `\n`. Hầu hết editor trên Windows (Notepad, VS Code mặc định) không tự thêm trailing newline khi save. Luôn kiểm tra file crontab bằng `cat -A file` — dòng cuối đúng sẽ thấy `$` ở cuối, sai sẽ không có.

---

## 4. File trong `uploads/` và `exports/` không accessible từ host

**Triệu chứng**
- Bot Telegram upload file thành công (không báo lỗi)
- Mở thư mục `uploads/` hoặc `exports/` trên máy host: Permission denied hoặc file owned by unknown UID

**Nguyên nhân**
- `Dockerfile` tạo non-privileged user `appuser` với UID 10001
- Trên Linux host, UID 10001 không map với user nào → file trong bind-mount thuộc về "unknown user"
- `compose.yaml` ban đầu không có volume mount tường minh cho `uploads/` và `exports/`

**Fix — `compose.yaml` (backend service)**
```yaml
# TRƯỚC
backend:
  ...
  # không có volumes cho uploads/exports

# SAU
backend:
  ...
  volumes:
    - ./uploads:/app/uploads
    - ./exports:/app/exports
  command: >
    sh -c "
    chmod -R 777 /app/uploads /app/exports &&
    python main.py
    "
```

**Fix — `Dockerfile`**
```dockerfile
# TRƯỚC — tạo appuser UID 10001, gây UID mismatch trên host
ARG UID=10001
RUN adduser --disabled-password --uid "${UID}" appuser
USER appuser

# SAU — bỏ block appuser, dùng root (kiểm soát qua compose user: "0:0")
# (không còn USER directive)
```

**Kiến thức rút ra**
> Trên Linux, bind-mount volumes kế thừa UID/GID từ process bên trong container. Nếu container chạy với UID không tồn tại trên host, file sẽ xuất hiện với UID số thay vì username, và host user thường không có quyền đọc/ghi. Hai cách giải quyết:
> 1. **Dùng root** (`user: "0:0"` trong compose) + `chmod` directory khi start — đơn giản, phù hợp server cá nhân
> 2. **Đồng bộ UID** giữa container user và host user — phức tạp hơn nhưng an toàn hơn cho môi trường multi-user

---

## 5. MySQL init scripts không chạy lại khi muốn restore

**Triệu chứng**
- Có file `.sql` trong `restore/` nhưng MySQL không import
- Script `mysql/init/01-import.sh` không được thực thi

**Nguyên nhân**
- MySQL Docker image chỉ chạy scripts trong `/docker-entrypoint-initdb.d/` **một lần duy nhất** khi volume `mysql_data` còn trống (lần `docker compose up` đầu tiên)
- Nếu volume đã tồn tại và có data → MySQL bỏ qua toàn bộ init scripts

**Cách restore đúng**

Option A — Xóa volume, chạy lại từ đầu (mất data hiện tại):
```bash
docker compose down
docker volume rm webcuamemeapplication_mysql_data
# đặt file .sql vào restore/
docker compose up -d
```

Option B — Restore vào DB đang chạy (giữ data hiện tại):
```bash
docker exec -i student-management-mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" \
  < ./restore/backup.sql
```

**Kiến thức rút ra**
> `docker-entrypoint-initdb.d` là cơ chế khởi tạo một lần của MySQL image — không phải công cụ restore. Để restore production DB đang chạy, luôn dùng `docker exec` pipe trực tiếp vào `mysql` client, không phụ thuộc vào init scripts.

---

## Tóm tắt các file đã sửa

| File | Thay đổi |
|---|---|
| `backup/backup.sh` | Xóa `umask 077` |
| `backup/crontab.txt` | Thêm trailing newline |
| `compose.yaml` | backup: `apt-get` → `microdnf`, `cron` → `crond -n`; backend: thêm volumes + chmod |
| `Dockerfile` | Bỏ `appuser` UID 10001, không còn `USER appuser` |
