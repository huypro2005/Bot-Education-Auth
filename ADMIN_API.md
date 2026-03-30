# API quản trị (Admin) — WebCuaMe

Tài liệu cho **frontend** (React/Vue/Svelte…) gọi backend FastAPI.

## Cơ sở

| Mục | Giá trị |
|-----|---------|
| Base URL (dev) | `http://127.0.0.1:8000` |
| Prefix API | `/admin` |
| OpenAPI | `GET /docs` (Swagger), `GET /redoc` |
| Định dạng | JSON, UTF-8 |

**CORS** (đã cấu hình trong `main.py`): `http://localhost:3000`, `http://localhost:5173`, … — chỉnh thêm origin production khi deploy.

**Mô hình dữ liệu:** Giáo viên và học sinh là một bảng `users` (`UserInfo`) phân biệt bằng `role` (`teacher` | `student`). Whitelist Telegram cho GV là bảng `tele_teacher_infos` (`TeleTeacherInfo`).

---

## 1. TeleTeacher ID (whitelist Telegram)

### `POST /admin/tele-teachers`

Thêm một Telegram ID được phép dùng bot với vai trò giáo viên (trước khi GV `/start`).

**Body**

```json
{
  "telegram_id": "123456789",
  "username": "optional_username"
}
```

**201** — `TeleTeacherOut`

```json
{
  "id": 1,
  "telegram_id": "123456789",
  "username": "optional_username"
}
```

**409** — `telegram_id` đã tồn tại.

---

### `GET /admin/tele-teachers`

Danh sách toàn bộ whitelist: **id + telegram_id + username**.

**200** — `TeleTeacherOut[]`

---

### `DELETE /admin/tele-teachers/{record_id}` (tùy chọn)

Xóa một dòng whitelist theo `id`.

**204** — không body.

**404** — không tìm thấy bản ghi.

---

## 2. Giáo viên (`users` có `role = teacher`)

### `GET /admin/teachers`

Danh sách giáo viên: **id, telegram_id, username, full_name, is_active**, và các **lớp chủ nhiệm** (`homeroom_classes` — cùng cấu trúc `ClassOut`).

**200** — `TeacherOut[]`

```json
[
  {
    "id": 1,
    "telegram_id": "123456789",
    "username": "gv01",
    "full_name": "Nguyễn Văn A",
    "is_active": true,
    "homeroom_classes": [
      {
        "id": 1,
        "name": "10A1",
        "total_students": 35,
        "homeroom_teacher_id": 1,
        "homeroom_teacher_name": "Nguyễn Văn A"
      }
    ]
  }
]
```

> Giáo viên xuất hiện ở đây sau khi họ đã tương tác bot và hệ thống tạo `UserInfo` với `role=teacher` (thường kết hợp whitelist + `/start`).

---

## 3. Môn học (`subjects`)

### `POST /admin/subjects`

**Body**

```json
{
  "name": "Toán",
  "description": "Mô tả tùy chọn"
}
```

**201** — `SubjectOut` (`id`, `name`, `description`)

**409** — trùng `name` (unique).

---

### `GET /admin/subjects`

Tất cả môn: **id + name + description**.

**200** — `SubjectOut[]`

---

### `PUT /admin/subjects/{subject_id}` (bổ sung)

Cập nhật tên/mô tả (gửi trường cần đổi).

**Body (tùy chọn từng trường)**

```json
{
  "name": "Toán nâng cao",
  "description": "Cập nhật mô tả"
}
```

**200** — `SubjectOut`

**404** / **409** — không tìm thấy / trùng tên.

---

## 4. Lớp (`classes`)

### `POST /admin/classes`

**Body**

```json
{
  "name": "10A1",
  "homeroom_teacher_id": 1,
}
```

`homeroom_teacher_id` có thể `null`. Phải là **user có `role = teacher`** (`users.id`).

**201** — `ClassOut`

**404** — không có giáo viên với id đó.

**409** — trùng tên lớp.

---

### `GET /admin/classes`

Tất cả lớp. Mỗi phần tử gồm **id, name, total_students, homeroom_teacher_id** và **`homeroom_teacher_name`**: họ tên đầy đủ giáo viên chủ nhiệm (`users.full_name`) khi đã gán GVCN; nếu chưa có GVCN thì `homeroom_teacher_id` / `homeroom_teacher_name` là `null`.

**200** — `ClassOut[]`

```json
[
  {
    "id": 1,
    "name": "10A1",
    "total_students": 35,
    "homeroom_teacher_id": 2,
    "homeroom_teacher_name": "Nguyễn Thị B"
  }
]
```

---

### `PUT /admin/classes/{class_id}/homeroom`

Gán / đổi **giáo viên chủ nhiệm** (hoặc gửi `null` để bỏ).

**Body**

```json
{
  "homeroom_teacher_id": 2
}
```

**200** — `ClassOut`

**404** — lớp hoặc giáo viên không hợp lệ.

---

### `GET /admin/classes/{class_id}/students` (bổ sung)

Học sinh trong lớp (`users` có `role = student`, `class_id` khớp).

**200** — `StudentOut[]`

**404** — không có lớp.

---

## 5. Môn theo lớp (`subject_classes`)

Một dòng = một cặp **(môn, lớp)** + **giáo viên dạy** (tùy chọn).

### `POST /admin/subject-classes`

**Body**

```json
{
  "subject_id": 1,
  "class_id": 1,
  "teacher_id": 3
}
```

`teacher_id` có thể `null`. Nếu có — phải là `users.id` với `role = teacher`.

**201** — `SubjectClassOut`

**404** — thiếu môn/lớp/giáo viên.

**409** — môn đã gán cho lớp này (unique `subject_id` + `class_id`).

---

### `GET /admin/subject-classes?class_id={id}`

- Có `class_id`: tất cả **SubjectClass** của lớp đó.
- Không query: toàn bộ (dùng cẩn thận khi dữ liệu lớn).

**200** — `SubjectClassOut[]`

---

### `GET /admin/classes/{class_id}/subject-classes`

Giống filter theo lớp; **404** nếu `class_id` không tồn tại.

**200** — `SubjectClassOut[]`

---

### `PUT /admin/subject-classes/{subject_class_id}/teacher`

Gán / đổi giáo viên cho dòng SubjectClass (hoặc `null`).

**Body**

```json
{
  "teacher_id": 5
}
```

**200** — `SubjectClassOut`

**404** — không tìm thấy SubjectClass hoặc giáo viên.

---

## Gợi ý thứ tự màn hình admin

1. **Whitelist** — `POST/GET /admin/tele-teachers` (thêm ID GV trước khi họ vào bot).
2. **Môn** — `POST/GET /admin/subjects`.
3. **Lớp** — `POST/GET /admin/classes`, sau đó `PUT .../homeroom` nếu cần.
4. **Danh sách GV** — `GET /admin/teachers` để chọn `homeroom_teacher_id` / `teacher_id`.
5. **Gán môn–lớp–GV** — `POST /admin/subject-classes`, chỉnh bằng `PUT .../subject-classes/{id}/teacher`.
6. **Học sinh theo lớp** — `GET /admin/classes/{id}/students` khi cần.

---

## Lỗi thường gặp

| HTTP | Ý nghĩa |
|------|---------|
| 404 | Không tìm thấy resource (lớp, môn, giáo viên `users.id` không phải `role=teacher`, …) |
| 409 | Vi phạm unique (telegram whitelist, tên môn, tên lớp, cặp môn–lớp) |

---

## Frontend: ví dụ gọi API (fetch)

```ts
const API = "http://127.0.0.1:8000";

export async function getTeleTeachers() {
  const r = await fetch(`${API}/admin/tele-teachers`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function createTeleTeacher(telegram_id: string, username?: string) {
  const r = await fetch(`${API}/admin/tele-teachers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id, username: username ?? null }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
```

Khi có **auth JWT / session** cho admin, thêm header `Authorization` trong mọi request và bảo vệ router phía server.
