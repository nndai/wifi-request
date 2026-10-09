# WiFi Request

<p align="center">
  <img src="icon/app.png" alt="WiFi Request Logo" width="96" height="96">
</p>

<p align="center">
  <b>Công cụ tự động đăng nhập Wi-Fi KTX Khu A ĐHQG-HCM</b><br>
  <i>Giữ kết nối Internet liên tục — Không còn nỗi lo bị ngắt mạng mỗi 15 phút</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/UI-CustomTkinter-blue?style=flat-square" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/Build-PyInstaller-FFD43B?style=flat-square" alt="PyInstaller">
</p>

---

## 📖 Giới thiệu

Tại Ký túc xá Khu A Đại học Quốc gia TP.HCM, mạng **`INET - Free WiFi`** có cơ chế cổng chào (Captive Portal qua hệ thống Awing) tự động ngắt kết nối sau mỗi **15 phút**, buộc sinh viên phải mở trình duyệt web và bấm đăng nhập lại thủ công. Điều này gây gián đoạn rất khó chịu khi học tập, tải tài liệu, họp trực tuyến hoặc chơi game.

**WiFi Request** là tiện ích nhẹ chạy nền trên Windows, liên tục giám sát trạng thái mạng và **tự động xác thực đăng nhập ngay lập tức** khi phiên kết nối vừa hết hạn, mang lại trải nghiệm Internet mượt mà và không gián đoạn.

---

## 🛠️ Yêu cầu môi trường

* **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit).
* **Python:** Phiên bản 3.8 trở lên (nếu chạy từ mã nguồn).

---

## ⚡ Tải về & Sử dụng nhanh

Dành cho người dùng thông thường — **không cần cài đặt Python**:

1. Truy cập mục [**Releases**](https://github.com/nndai/wifi-request/releases) của dự án.
2. Tải về phiên bản mới nhất của file **`wifi_request.exe`**.
3. Lưu file ở một thư mục cố định (ví dụ: `Documents` hoặc thư mục bất kỳ) và nhấp đúp để mở:
   * Ứng dụng sẽ tự động chạy ngầm ở khay hệ thống (System Tray, cạnh đồng hồ).
   * Tự động thêm lối tắt để khởi động cùng Windows mỗi khi bật máy.
   * *(Lưu ý: Nếu Windows SmartScreen hiển thị thông báo, hãy bấm **More info** ➔ **Run anyway**).*

---

## 💻 Chạy từ mã nguồn

### 1. Tải mã nguồn
```bash
git clone https://github.com/nndai/wifi-request.git
cd wifi-request
```

### 2. Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng
```bash
python src_wifi_request.py
```

---

## 📦 Hướng dẫn đóng gói thành file thực thi (.EXE)

Dự án đã chuẩn bị sẵn file cấu hình [`wifi_request.spec`](wifi_request.spec) và siêu dữ liệu phiên bản [`version_wifi_request.txt`](version_wifi_request.txt).

Để đóng gói thành một file `wifi_request.exe` độc lập duy nhất:

```bash
python -m PyInstaller wifi_request.spec
```

File thực thi sẽ nằm tại: **`dist/wifi_request.exe`**


---

## 📂 Cấu trúc thư mục

```text
├── icon/
│   └── app.png               # Icon của ứng dụng
├── dist/
│   └── wifi_request.exe      # File chạy sau khi build (standalone)
├── font_base64.py            # Font JetBrains Mono Bold nhúng base64
├── image_base64.py           # Icon ứng dụng nhúng base64
├── requirements.txt          # Danh sách thư viện phụ thuộc
├── src_wifi_request.py       # Mã nguồn chính của ứng dụng
├── wifi_request.spec         # Cấu hình đóng gói PyInstaller
└── version_wifi_request.txt  # Thông tin phiên bản & bản quyền Windows EXE
```

---

## ⚙️ Cơ chế hoạt động

1. **Nhận diện mạng:** Ứng dụng dùng `netifaces` để xác định Gateway IP hiện tại của router KTX (thường là `192.168.x.x`).
2. **Kiểm tra Internet:** Kiểm tra phản hồi HTTP qua curl/socket định kỳ mỗi 2 giây.
3. **Vượt Captive Portal:** Khi gặp trang chuyển hướng của router hoặc dịch vụ Awing Connect:
   * Tự động phân tích biểu mẫu `authForm` (trích xuất `client_mac`, `client_ip`, `chap_challenge`...).
   * Gửi yêu cầu xác thực ngầm đến máy chủ xác thực và hoàn tất đăng nhập mà không cần tương tác của người dùng.

