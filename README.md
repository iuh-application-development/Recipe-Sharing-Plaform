# **Recipe Sharing Platform**

## **Thành viên nhóm**
- **Thành viên 1:** Trần Văn Huy - 21130971
- **Thành viên 2:** Nguyễn Thanh Quyền - 21045131
- **Thành viên 3:** Nguyễn Võ Đức - 21061511
- **Thành viên 4:** Huỳnh Long Hồ - 21008411

## **1. Tổng Quan**

**Recipe Sharing Platform** là một nền tảng web toàn diện cho phép người dùng chia sẻ và khám phá các công thức nấu ăn. Hệ thống cho phép:

* Người dùng **tạo và chia sẻ công thức nấu ăn** với cộng đồng
* **Tìm kiếm và lọc công thức** theo nhiều tiêu chí khác nhau
* **Phân loại món ăn** theo nhiều thể loại như món chay, món theo mùa, ẩm thực quốc tế
* **Quản lý hình ảnh** món ăn với khả năng upload và preview

Nền tảng có giao diện thân thiện, dễ sử dụng và tương thích với nhiều thiết bị.

## **2. Công Nghệ Sử Dụng**

* **Backend**: Flask
* **Frontend**: Bootstrap, JavaScript
* **Cơ sở dữ liệu**: SQLite
* **Xác thực**: Flask-Login
* **Upload ảnh**: Pillow
* **Môi trường ảo**: Python venv

## **3. Tính Năng Chính**

### **3.1. Quản lý Tài khoản**

✅ **Đăng ký và đăng nhập**:
* Tạo tài khoản mới
* Đăng nhập vào hệ thống
* Quản lý thông tin cá nhân

✅ **Quản lý công thức**:
* Tạo công thức mới
* Chỉnh sửa công thức đã tạo
* Xóa công thức

### **3.2. Quản lý Công Thức**

✅ **Thông tin công thức**:
* Tiêu đề và mô tả
* Danh sách nguyên liệu
* Các bước thực hiện
* Thời gian nấu và khẩu phần

✅ **Quản lý hình ảnh**:
* Upload ảnh món ăn
* Preview ảnh trước khi đăng
* Tự động xóa ảnh cũ khi cập nhật

### **3.3. Phân Loại và Tìm Kiếm**

✅ **Phân loại món ăn**:
* Món ăn cơ bản (món nước, món xào, món kho...)
* Món chay (món chay từ đậu hũ, rau củ...)
* Món theo dịp (Tết, Trung thu, Giáng sinh...)
* Món ăn kiêng (Keto, Low-carb, Eat clean...)
* Ẩm thực quốc tế (Món Ý, Pháp, Nhật, Hàn...)

✅ **Tìm kiếm**:
* Tìm theo tên món
* Lọc theo loại món ăn
* Kết hợp nhiều tiêu chí tìm kiếm

## **4. Cấu Trúc Cơ Sở Dữ Liệu**

### **4.1. Bảng User**

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| id | Integer | Khóa chính |
| username | Text | Tên đăng nhập |
| password | Text | Mật khẩu đã mã hóa |
| email | Text | Email người dùng |
| created | Timestamp | Thời điểm tạo tài khoản |
| avatar_path | Text | Đường dẫn ảnh đại diện |

### **4.2. Bảng Post**

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| id | Integer | Khóa chính |
| author_id | Integer | ID người tạo |
| title | Text | Tên món ăn |
| description | Text | Mô tả món ăn |
| ingredients | Text | Nguyên liệu |
| instructions | Text | Cách làm |
| cooking_time | Integer | Thời gian nấu |
| servings | Integer | Khẩu phần |

### **4.3. Bảng Tags**

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| id | Integer | Khóa chính |
| name | Text | Tên thẻ |
| created | Timestamp | Thời điểm tạo |

## **5. Cài Đặt và Thiết Lập**

1. Clone repository:
```bash
git clone https://github.com/iuh-application-development/Recipe-Sharing-Plaform.git
cd Recipe-Sharing-Plaform
```

2. Tạo và kích hoạt môi trường ảo:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

4. Khởi tạo database:
```bash
flask init-db
```

5. Chạy ứng dụng:
```bash
flask run
```

## **6. Cấu Trúc Thư Mục**

```
recipe-sharing-platform/
├── share_recipe/
│   ├── __init__.py          # Khởi tạo ứng dụng
│   ├── auth.py              # Xử lý xác thực
│   ├── blog.py              # Xử lý công thức
│   ├── db.py                # Kết nối database
│   ├── schema.sql           # Cấu trúc database
│   ├── static/              # Tài nguyên tĩnh
│   │   ├── style.css        # CSS styles
│   │   └── uploads/         # Thư mục chứa ảnh
│   └── templates/           # Templates
│       ├── auth/            # Templates xác thực
│       ├── blog/            # Templates công thức
│       └── base.html        # Template cơ sở
├── instance/                # Database
├── tests/                   # Unit tests
├── venv/                    # Môi trường ảo
├── .env                     # Biến môi trường
├── .gitignore              # Git ignore
├── README.md               # Tài liệu
└── requirements.txt        # Dependencies
```

