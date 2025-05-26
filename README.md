# Recipe-Sharing-Plaform

## 1. THÔNG TIN NHÓM

- Trần Văn Huy - 95tranvanhuytoky1@gmail.com  
- Nguyễn Thanh Quyền - nguyenthanhquyen145@gmail.com  
- Nguyễn Võ Đức - nvoduc2601@gmail.com  
- Huỳnh Long Hồ - itzkun1609@gmail.com  

## 2. MÔ TẢ ĐỀ TÀI

### 2.1. Mô tả tổng quan

**Tầm nhìn**: Xây dựng một trang web trực tuyến năng động, nơi mọi người có thể dễ dàng chia sẻ, khám phá và thưởng thức những công thức nấu ăn ngon miệng.  

**Điểm độc đáo**:  
- Tập trung vào tính tương tác cao, khuyến khích người dùng chia sẻ kinh nghiệm và mẹo nấu ăn.  
- Tích hợp tính năng đánh giá và nhận xét chi tiết, giúp người dùng lựa chọn công thức phù hợp.  
- Phân loại công thức theo nhiều tiêu chí (món ăn, nguyên liệu, độ khó, v.v.) để dễ dàng tìm kiếm.  

### 2.2. Mục tiêu

- Một trang web cho phép người dùng có thể tự do chia sẻ các công thức nấu ăn.  
- Tạo và đăng ký tài khoản đơn giản.  
- Hệ thống quản lý tốt, bảo mật, nhiều chức năng.  
- Các tính năng tìm kiếm, yêu thích, bình luận đầy đủ.  

## 3. PHÂN TÍCH THIẾT KẾ

### 3.1. Phân tích yêu cầu

**Yêu cầu chức năng**:
- Người dùng có thể đăng tải công thức nấu ăn kèm hình ảnh.  
- Người dùng có thể tìm kiếm công thức theo tên món ăn hoặc nguyên liệu.  
- Hiển thị danh sách các công thức mới nhất và phổ biến nhất.  
- Người dùng có thể lưu lại công thức mình yêu thích.  

**Yêu cầu phi chức năng**:
- Giao diện đơn giản, dễ sử dụng.  

### 3.2. Đặc tả yêu cầu

**Người dùng thông thường (Người xem)**:  
- Đăng nhập / đăng ký / đăng xuất / đổi mật khẩu.  
- Tìm kiếm và xem công thức.  
- Đánh giá và nhận xét công thức.  
- Lưu công thức yêu thích.  
- Chia sẻ công thức qua các nền tảng mạng xã hội.  
- Tạo hồ sơ cá nhân.  
- Theo dõi người dùng khác.  

**Người sáng tạo nội dung**:  
- Đăng tải công thức kèm hình ảnh và video.  
- Chỉnh sửa và xóa công thức đã đăng.  
- Quản lý hồ sơ cá nhân.  

**Quản trị viên**:  
- Quản lý người dùng (thêm, xóa người dùng, đổi mật khẩu).  
- Kiểm duyệt và xóa (có thể ẩn) công thức vi phạm.  
- Phân tích thống kê người dùng và công thức.  

### 3.3. Thiết kế hệ thống

- **Use Case Diagram**  

- **Thiết kế CSDL**  
![Use Case Diagram](image/README/Picture.png)

- **Thiết kế giao diện (screenshot các màn hình chính/wireframe)**  

**Trang chủ**  
![Trang chủ](image/README/Picture2.png)

**Giao diện đăng nhập**  
![Giao diện đăng nhập](image/README/Picture3.png)

**Giao diện đăng ký**  
![Giao diện đăng ký](image/README/Picture4.png)

**Giao diện đăng bài viết**  
![Giao diện đăng bài viết 1](image/README/Picture5.png)  
![Giao diện đăng bài viết 2](image/README/Picture6.png)

**Giao diện người dùng và hồ sơ công thức**  
![Giao diện người dùng](image/README/Picture7.png)
![Giao diện công thưc người dùng](image/README/Picture8.png)

**Giao diện món ăn ưa thích**  
![Giao diện món ăn ưa thích](image/README/Picture9.png)

**Giao diện công thức đã lưu**  
![Giao diện công thức đã lưu](image/README/Picture10.png)

**Giao diện tìm kiếm**  
![Giao diện tìm kiếm 1](image/README/Picture11.png)  
![Giao diện tìm kiếm 2](image/README/Picture12.png)  


## 4. CÔNG CỤ VÀ CÔNG NGHỆ SỬ DỤNG

- Ngôn ngữ lập trình: Python  
- Framework: Flask, Bootstrap  
- Cơ sở dữ liệu: SQL Database  
- IDE: Visual Studio Code  

## 5. TRIỂN KHAI

1. Clone repository:
    ```bash
    git clone https://github.com/iuh-application-development/Recipe-Sharing-Plaform.git
    cd Recipe-Sharing-Plaform
    ```

2. Tạo và kích hoạt môi trường ảo:
    - **Windows**:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    - **Linux/Mac**:
        ```bash
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
    Python run.py hoặc flask --app share_recipe run
    ```

## 6. KIỂM THỬ

- Thực hiện kiểm thử chức năng (Functional Testing)  
- Kiểm thử hiệu năng (Performance Testing)  

## 7. KẾT QUẢ

### 7.1. Kết quả đạt được

- Có thể tạo và đăng nhập tài khoản, sửa đổi thông tin người dùng.  
- Có thể viết và đăng các công thức, gồm các thông tin chi tiết và hình ảnh.  
- Có thể tương tác để yêu thích, like, lưu và bình luận.  
- Có thể tìm kiếm các món ăn một cách đơn giản.  
- Admin có thể quản lý người dùng: thêm, xóa, đổi mật khẩu, khóa tài khoản, xóa bài viết.  

### 7.2. Kết quả chưa đạt được

- Chưa thể chia sẻ lên nhiều nền tảng khác.  
- Chưa thể cho phép người dùng tự đổi mật khẩu.  
- Thiếu các thông tin như: link video, lưu ý khi nấu,...  
- Chưa có gợi ý món ăn dựa trên lịch sử.  
- Chưa có tính năng phê duyệt bài viết từ admin.  
- Chưa có tìm kiếm bằng ảnh.  
- Chưa có gợi ý công thức theo nguyên liệu có sẵn.  
- Chưa có Chatbot gợi ý món ăn.  

### 7.3. Hướng phát triển

- **Nâng cao trải nghiệm người dùng**:
    - Đánh giá công thức bằng sao ⭐  
    - Theo dõi đầu bếp yêu thích  
    - Gợi ý món ăn dựa trên lịch sử  

- **Đa phương tiện**:
    - Upload video hướng dẫn  
    - Nhúng video từ YouTube, TikTok, Instagram  

- **Tích hợp AI**:
    - Gợi ý món ăn, hỗ trợ nấu ăn thông minh  

- **Mở rộng triển khai thực tế**:
    - Tìm kiếm bằng ảnh  
    - Gợi ý theo nguyên liệu  
    - Chatbot hỗ trợ  

## 8. TÀI LIỆU THAM KHẢO

- [https://flutter.dev](https://flutter.dev)  
- [https://dart.dev](https://dart.dev)  
- [https://flask.palletsprojects.com](https://flask.palletsprojects.com)  
