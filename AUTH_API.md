# Auth API — Tài liệu cho Frontend

Tất cả API `/admin/*` (trừ `/admin/login`, `/admin/refresh`, `/admin/register`) đều yêu cầu **JWT access token** trong header.

---

## Tổng quan luồng

```
1. Đăng nhập  →  nhận access_token + refresh_token
2. Gọi API    →  gửi access_token trong header Authorization
3. Token hết hạn (30 phút)  →  dùng refresh_token để lấy token mới
4. Refresh token hết hạn (7 ngày)  →  bắt buộc đăng nhập lại
```

---

## Các endpoint xác thực

### 1. Đăng nhập

```
POST /admin/login
Content-Type: application/x-www-form-urlencoded
```

**Request body** (form data, KHÔNG phải JSON):

| Field | Type | Mô tả |
|---|---|---|
| `username` | string | Tên đăng nhập |
| `password` | string | Mật khẩu |

> Lưu ý: endpoint này dùng `application/x-www-form-urlencoded`, không phải `application/json`. Khi dùng `fetch` hoặc `axios` cần set đúng Content-Type.

**Response 200:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response lỗi:**

| HTTP | detail | Nguyên nhân |
|---|---|---|
| 401 | Sai tên đăng nhập hoặc mật khẩu | username/password sai |
| 403 | Tài khoản đã bị vô hiệu hoá | admin bị khoá |

---

### 2. Làm mới token

```
POST /admin/refresh
Content-Type: application/json
```

**Request body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200:** Giống `/admin/login` — trả về cặp `access_token` + `refresh_token` mới.

**Response lỗi:**

| HTTP | detail | Nguyên nhân |
|---|---|---|
| 401 | Token không hợp lệ hoặc đã hết hạn | refresh_token hết hạn hoặc sai |
| 401 | Tài khoản không tồn tại hoặc đã bị vô hiệu hoá | admin bị xoá/khoá |

> Sau khi gọi `/admin/refresh` thành công, **lưu cả 2 token mới** — refresh token cũ không dùng lại được.

---

### 3. Tạo admin đầu tiên

```
POST /admin/register
Content-Type: application/json
```

> Endpoint này chỉ hoạt động khi **chưa có admin nào** trong hệ thống. Sau khi tạo xong sẽ bị khoá vĩnh viễn.

**Request body:**

```json
{
  "username": "admin",
  "password": "matkhau123"
}
```

| Field | Yêu cầu |
|---|---|
| `username` | Tối thiểu 3 ký tự |
| `password` | Tối thiểu 6 ký tự |

**Response 201:**

```json
{
  "message": "Tạo tài khoản admin 'admin' thành công."
}
```

**Response lỗi:**

| HTTP | detail | Nguyên nhân |
|---|---|---|
| 403 | Đã có admin... | Hệ thống đã có admin, không tạo thêm được qua endpoint này |

---

## Gọi các API được bảo vệ

Tất cả endpoint `/admin/*` (trừ login/refresh/register) đều cần header:

```
Authorization: Bearer <access_token>
```

**Response khi thiếu/sai token:**

| HTTP | detail | Nguyên nhân |
|---|---|---|
| 401 | Not authenticated | Không có header Authorization |
| 401 | Token không hợp lệ hoặc đã hết hạn | Token sai hoặc hết 30 phút |
| 401 | Tài khoản không tồn tại hoặc đã bị vô hiệu hoá | Admin bị xoá/khoá |

---

## Ví dụ code Frontend

### Axios — login và lưu token

```js
// api/auth.js
import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

export async function login(username, password) {
  // Dùng URLSearchParams vì endpoint yêu cầu form-data
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)

  const res = await axios.post(`${BASE_URL}/admin/login`, params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

  localStorage.setItem('access_token', res.data.access_token)
  localStorage.setItem('refresh_token', res.data.refresh_token)
  return res.data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}
```

### Axios instance với auto-refresh

```js
// api/axios.js
import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

// Tự động đính kèm access_token vào mỗi request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Tự động refresh khi nhận 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    // Nếu 401 và chưa retry
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // Không có refresh token → về trang login
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const res = await axios.post(`${BASE_URL}/admin/refresh`, {
          refresh_token: refreshToken,
        })

        localStorage.setItem('access_token', res.data.access_token)
        localStorage.setItem('refresh_token', res.data.refresh_token)

        // Retry request gốc với token mới
        original.headers.Authorization = `Bearer ${res.data.access_token}`
        return api(original)
      } catch {
        // Refresh thất bại → về trang login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default api
```

### Sử dụng api instance

```js
// Thay vì axios.get(...), dùng api.get(...)
import api from './api/axios'

// Lấy danh sách giáo viên — token tự động được gắn
const res = await api.get('/admin/teachers')
console.log(res.data)
```

---

## Lưu token ở đâu?

| Cách lưu | Ưu điểm | Nhược điểm |
|---|---|---|
| `localStorage` | Đơn giản, persist qua tab | Dễ bị XSS đọc |
| `sessionStorage` | Mất khi đóng tab | Không persist |
| `httpOnly cookie` | An toàn nhất (JS không đọc được) | Cần backend set cookie |

Hiện tại backend không set cookie → dùng `localStorage` là phù hợp. Nếu muốn nâng cấp bảo mật sau, có thể chuyển sang `httpOnly cookie`.

---

## Thời hạn token

| Token | Thời hạn | Dùng để |
|---|---|---|
| `access_token` | **30 phút** | Gọi tất cả API `/admin/*` |
| `refresh_token` | **7 ngày** | Lấy cặp token mới khi access_token hết hạn |

Khi cả 2 đều hết hạn → bắt buộc đăng nhập lại bằng username/password.
