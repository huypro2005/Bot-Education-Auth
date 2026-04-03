# Hướng Dẫn Sử Dụng Bot Telegram

> Dành cho **giáo viên** và **học sinh** — không cần biết lập trình, chỉ cần biết dùng Telegram.

---

## Bắt đầu — Ai cũng làm bước này trước

### Bước 1: Mở bot trên Telegram

Tìm kiếm tên bot trên Telegram (hỏi quản trị viên để lấy tên/link bot), sau đó nhấn **Start** hoặc gõ lệnh `/start`.

### Bước 2: Bot nhận dạng bạn là ai

Bot sẽ tự động xác định vai trò của bạn:

- Nếu bạn đã được **quản trị viên thêm vào danh sách giáo viên** trước → bot hiện **menu Giáo viên**
- Nếu không → bot hiện **menu Học sinh**

> Bạn không cần đăng ký, không cần mật khẩu. Bot nhận dạng qua tài khoản Telegram của bạn.

---

## PHẦN 1 — DÀNH CHO HỌC SINH

Sau khi gõ `/start`, bạn sẽ thấy menu với các nút:

| Nút | Chức năng |
|---|---|
| Tham gia lớp học | Gửi yêu cầu vào một lớp |
| Chỉnh sửa thông tin | Đổi tên hiển thị của bạn |
| Tính Năng | Xem thông báo, bài tập, kết quả |
| Thông tin của tôi | Xem tên, lớp hiện tại của bạn |

---

### 1.1 Tham gia lớp học

**Khi nào dùng:** Lần đầu vào bot, bạn chưa thuộc lớp nào.

**Các bước:**

1. Nhấn nút **Tham gia lớp học**
2. Bot hiển thị danh sách các lớp đang có giáo viên chủ nhiệm
3. Nhấn vào tên lớp bạn muốn vào
4. Bot gửi thông báo: *"Đã gửi yêu cầu tham gia lớp... Vui lòng chờ giáo viên chủ nhiệm duyệt."*
5. Chờ giáo viên chủ nhiệm **chấp nhận** — bạn sẽ nhận được tin nhắn thông báo kết quả

**Lưu ý:**
- Mỗi học sinh chỉ được vào **một lớp duy nhất**
- Nếu đã gửi yêu cầu rồi, không thể gửi thêm — hãy chờ giáo viên duyệt
- Chỉ những lớp đã có **giáo viên chủ nhiệm** mới hiển thị trong danh sách

---

### 1.2 Chỉnh sửa thông tin

**Khi nào dùng:** Muốn đổi tên hiển thị để giáo viên nhận ra bạn dễ hơn.

**Các bước:**

1. Nhấn nút **Chỉnh sửa thông tin**
2. Bot hỏi: *"Nhập tên đầy đủ của bạn"*
3. Gõ họ và tên đầy đủ, gửi đi
4. Bot xác nhận đã lưu

> Tên này sẽ hiển thị với giáo viên khi bạn nộp bài hoặc yêu cầu vào lớp.

---

### 1.3 Xem thông báo gần đây

**Khi nào dùng:** Muốn biết giáo viên có thông báo gì mới trong 7 ngày qua.

**Các bước:**

1. Nhấn **Tính Năng**
2. Nhấn **Thông báo gần đây**
3. Bot hiển thị tất cả thông báo của lớp bạn trong 7 ngày gần nhất (mới nhất ở trên)

> Nếu bạn chưa vào lớp, sẽ không có thông báo nào hiện ra.

---

### 1.4 Xem và nộp bài tập

**Khi nào dùng:** Giáo viên đã giao bài, bạn muốn xem và nộp bài.

**Các bước xem bài tập:**

1. Nhấn **Tính Năng**
2. Nhấn **Bài tập**
3. Bot hiển thị danh sách bài tập **còn hạn** của lớp bạn, sắp xếp theo ngày hết hạn gần nhất
4. Nhấn vào tên bài tập để xem chi tiết: đề bài, hướng dẫn, deadline, file đính kèm (nếu có)

**Các bước nộp bài:**

1. Sau khi xem chi tiết bài tập, nhấn **Nộp bài**
2. Gửi file PDF bài làm của bạn lên chat
3. Bot nhận file, AI tự động chấm và phản hồi điểm + nhận xét
4. Nếu file là ảnh scan (không đọc được chữ), bot vẫn lưu file nhưng không có điểm AI — giáo viên sẽ chấm thủ công

**Lưu ý:**
- Chỉ chấp nhận file **PDF**
- Nếu nộp lại, bài cũ sẽ bị **ghi đè** — chỉ giữ bài mới nhất
- Điểm AI chỉ là tham khảo, điểm chính thức do giáo viên chấm

---

### 1.5 Xem kết quả bài tập

**Khi nào dùng:** Muốn xem điểm các bài đã nộp.

**Các bước:**

1. Nhấn **Tính Năng**
2. Nhấn **Xem kết quả bài tập**
3. Bot hiển thị danh sách tất cả bài đã nộp, bao gồm:
   - Tên môn học
   - Tiêu đề bài tập
   - Điểm AI (nếu có)
   - Điểm giáo viên (nếu đã chấm)
   - Thời gian nộp

---

## PHẦN 2 — DÀNH CHO GIÁO VIÊN

> Để được nhận dạng là giáo viên, tài khoản Telegram của bạn phải được **quản trị viên thêm vào danh sách** trước khi bạn gõ `/start`.

Sau khi gõ `/start`, menu Giáo viên gồm các nút:

| Nút | Chức năng |
|---|---|
| Chỉnh sửa thông tin | Đổi tên hiển thị |
| Chấp nhận học sinh | Duyệt yêu cầu vào lớp |
| Thông báo | Gửi thông báo đến lớp |
| Giao bài | Tạo bài tập mới |
| Thông tin của tôi | Xem thông tin cá nhân |
| Các lớp quản lý | Xem danh sách lớp đang dạy/chủ nhiệm |
| Chấm bài | Xem và chấm điểm bài nộp |
| Điểm rèn luyện học sinh | Cộng/trừ điểm rèn luyện |
| Danh sách học sinh lớp chủ nhiệm | Xem danh sách học sinh |
| Xuất Excel quá trình rèn luyện | Xuất báo cáo cuối kỳ |

---

### 2.1 Chỉnh sửa thông tin

Tương tự học sinh — nhấn nút, nhập họ tên đầy đủ, gửi đi.

---

### 2.2 Chấp nhận học sinh vào lớp

**Khi nào dùng:** Học sinh gửi yêu cầu vào lớp bạn chủ nhiệm, bạn cần duyệt.

**Các bước:**

1. Nhấn **Chấp nhận học sinh**
2. Bot hiển thị danh sách học sinh đang chờ duyệt, kèm tên lớp
3. Mỗi học sinh có 2 nút: **Chấp nhận** và **Từ chối**
4. Nhấn để xử lý từng học sinh
5. Học sinh sẽ nhận được tin nhắn thông báo kết quả ngay lập tức

**Lưu ý:**
- Khi **chấp nhận** 1 học sinh vào lớp, tất cả yêu cầu chờ khác của học sinh đó (nếu có) sẽ **tự động bị từ chối**
- Chỉ giáo viên **chủ nhiệm** mới thấy yêu cầu của lớp đó

---

### 2.3 Gửi thông báo đến lớp

**Khi nào dùng:** Muốn nhắn tin thông báo đến toàn bộ học sinh trong lớp.

**Các bước:**

1. Nhấn **Thông báo**
2. Bot hiển thị danh sách lớp bạn đang dạy hoặc chủ nhiệm — nhấn chọn lớp
3. Bot hỏi nội dung thông báo: *"Nhập nội dung thông báo"*
4. Gõ nội dung, gửi đi
5. Bot tự động gửi tin nhắn đến **từng học sinh** trong lớp đó

> Học sinh sẽ thấy thông báo này khi nhấn **Thông báo gần đây** trong vòng 7 ngày.

---

### 2.4 Giao bài tập

**Khi nào dùng:** Muốn giao bài tập cho học sinh một lớp-môn cụ thể.

**Các bước:**

1. Nhấn **Giao bài**
2. Bot hỏi chọn lớp — nhấn chọn lớp muốn giao bài
3. Bot hỏi chọn môn học trong lớp đó — nhấn chọn môn
4. Nhập **tiêu đề** bài tập
5. Nhập **nội dung / hướng dẫn** bài tập
6. Nhập **deadline** (hạn nộp) theo định dạng `DD/MM/YYYY HH:MM` hoặc bỏ qua nếu không có hạn
7. (Tuỳ chọn) Gửi **file đính kèm** nếu có đề bài dạng file
8. Bot xác nhận: *"Đã giao bài thành công"*

**Lưu ý:**
- Chỉ giao được bài cho lớp-môn mà bạn **được phân công dạy**
- Học sinh chỉ thấy bài tập còn trong hạn

---

### 2.5 Chấm bài

**Khi nào dùng:** Học sinh đã nộp bài, bạn muốn xem và cho điểm chính thức.

**Các bước:**

1. Nhấn **Chấm bài**
2. Chọn lớp → chọn môn → chọn bài tập
3. Bot hiển thị danh sách học sinh **đã nộp bài** cho bài tập đó
4. Nhấn vào tên học sinh để xem:
   - File bài làm (tải về để đọc)
   - Điểm AI và nhận xét AI (nếu có)
   - Điểm giáo viên hiện tại (nếu đã chấm trước)
5. Nhập điểm (thang 10), gửi đi
6. Bot xác nhận đã lưu điểm

---

### 2.6 Điểm rèn luyện học sinh

**Khi nào dùng:** Muốn cộng hoặc trừ điểm rèn luyện của một học sinh kèm lý do.

**Các bước:**

1. Nhấn **Điểm rèn luyện học sinh**
2. Chọn lớp
3. Bot hiển thị danh sách học sinh kèm **tổng điểm rèn luyện** hiện tại
4. Nhấn vào tên học sinh muốn điều chỉnh
5. Chọn **Cộng điểm (+1)** hoặc **Trừ điểm (-1)**
6. Nhập lý do (ví dụ: "Đi học muộn", "Tham gia hoạt động tốt")
7. Bot lưu và gửi thông báo đến học sinh đó

**Lưu ý:**
- Mỗi lần chỉ cộng hoặc trừ **1 điểm**
- Hệ thống lưu **lịch sử từng lần** cộng/trừ — không mất dữ liệu

---

### 2.7 Xem danh sách học sinh lớp chủ nhiệm

1. Nhấn **Danh sách học sinh lớp chủ nhiệm**
2. Bot hiển thị danh sách theo từng lớp bạn chủ nhiệm, sắp xếp theo tên

---

### 2.8 Xem các lớp đang quản lý

1. Nhấn **Các lớp quản lý**
2. Bot liệt kê tất cả lớp bạn có liên quan, kèm vai trò:
   - **Chủ nhiệm** — bạn là giáo viên chủ nhiệm của lớp
   - **Dạy: Toán, Văn...** — bạn đang dạy môn đó ở lớp này

---

### 2.9 Xuất Excel báo cáo cuối kỳ

**Khi nào dùng:** Cuối kỳ, muốn xuất báo cáo tổng hợp điểm rèn luyện và học lực của cả lớp, có AI nhận xét từng học sinh.

**Các bước:**

1. Nhấn **Xuất Excel quá trình rèn luyện học sinh lớp đang chủ nhiệm**
2. Bot thu thập dữ liệu: điểm rèn luyện, điểm các môn của từng học sinh
3. AI phân tích và viết nhận xét **học lực** + **hạnh kiểm** cho từng em
4. Bot gửi file Excel trực tiếp vào chat

**File Excel bao gồm:**
- Tên học sinh
- Tổng điểm rèn luyện (số lần được cộng / trừ điểm)
- Điểm từng môn học (điểm giáo viên / điểm AI)
- Nhận xét học lực (do AI tổng hợp)
- Nhận xét hạnh kiểm (do AI tổng hợp)

> Chỉ giáo viên **chủ nhiệm** mới dùng được tính năng này.

---

## Câu hỏi thường gặp

**Q: Tôi gõ /start nhưng thấy menu Học sinh, tôi là giáo viên?**
> Tài khoản Telegram của bạn chưa được quản trị viên thêm vào danh sách giáo viên. Liên hệ quản trị viên để được cấp quyền, sau đó gõ `/start` lại.

**Q: Tôi nhấn "Tham gia lớp học" nhưng không thấy lớp nào?**
> Các lớp cần có giáo viên chủ nhiệm thì mới hiển thị. Quản trị viên cần phân công giáo viên chủ nhiệm trước.

**Q: Tôi đã nộp bài rồi, có nộp lại được không?**
> Được. Nộp lại sẽ **ghi đè** bài cũ. Chỉ giữ bài nộp mới nhất.

**Q: Bot nói "AI không đọc được bài" nghĩa là gì?**
> File PDF bạn gửi là ảnh scan (chụp ảnh bài viết tay rồi lưu PDF). AI không đọc được chữ từ ảnh. Bài vẫn được lưu, giáo viên sẽ chấm thủ công.

**Q: Tôi chờ lâu mà không thấy giáo viên duyệt vào lớp?**
> Liên hệ trực tiếp với giáo viên chủ nhiệm để nhờ duyệt. Giáo viên cần đăng nhập bot và nhấn "Chấp nhận học sinh".
