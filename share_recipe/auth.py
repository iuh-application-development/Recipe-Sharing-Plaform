import functools
import secrets
import os
from werkzeug.utils import secure_filename

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app)
from werkzeug.security import check_password_hash, generate_password_hash

from share_recipe.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        username = request.form['username']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        phone = request.form['phone']
        
        db = get_db()
        error = None

        if not email:
            error = 'Email không được để trống.'
        elif not password:
            error = 'Mật khẩu không được để trống.'
        elif password != confirm_password:
            error = 'Mật khẩu xác nhận không khớp.'
        elif not username:
            error = 'Tên người dùng không được để trống.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, password, username, gender, birthdate, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (email, generate_password_hash(password), username, gender, birthdate, phone),
                )
                db.commit()
                flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
                return redirect(url_for('auth.login'))
            except db.IntegrityError:
                error = f"Email {email} đã được đăng ký."
                flash(error, 'error')

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif user and not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username'] # Lưu username vào session
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

        if user:
            user_dict = dict(user)
            is_blocked = user_dict.get('is_blocked')
            if is_blocked:
                g.user = None
                session.clear()
                flash('Tài khoản đã bị khóa. Mời đăng nhập lại.')
                return redirect(url_for('auth.login'))
            else:
                g.user = user
        else:
            g.user = None
        
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/create_admin', methods=('GET', 'POST'))
def create_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        error = None

        if not email:
            error = 'email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, password, role) VALUES (?, ?, ?)",
                    (email, generate_password_hash(password), 'admin'),  # Gán vai trò admin
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                return redirect(url_for("index"))  # Chuyển hướng đến trang blog

        flash(error)

    return render_template('auth/create_admin.html')  # Tạo template create_admin.html

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/admin/users', methods=('GET',))
@login_required
def admin_users():
    if g.user['role'] != 'admin':
        abort(403)  # Chỉ admin mới có quyền truy cập

    db = get_db()
    users = db.execute('SELECT id, email, role FROM user').fetchall()

    return render_template('admin/users.html', users=users)

@bp.route('/profile')
@login_required
def profile():
    db = get_db()
    # Lấy các bài viết của người dùng
    user_posts = db.execute(
        'SELECT p.*, bi.image_path '
        'FROM post p '
        'LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1 '
        'WHERE p.author_id = ? '
        'ORDER BY p.created DESC',
        (g.user['id'],)
    ).fetchall()

    return render_template('auth/profile.html', user_posts=user_posts)

@bp.route('/profile/edit', methods=('GET', 'POST'))
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form['username']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        phone = request.form['phone']
        
        error = None
        db = get_db()

        if not username:
            error = 'Tên người dùng không được để trống.'

        # Xử lý upload avatar
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Tạo tên file unique
                unique_filename = f"avatar_{g.user['id']}_{filename}"
                # Lưu file
                avatar_path = os.path.join('uploads/avatars', unique_filename)
                file_path = os.path.join(current_app.static_folder, avatar_path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                # Cập nhật đường dẫn trong database
                db.execute(
                    'UPDATE user SET avatar_path = ? WHERE id = ?',
                    (avatar_path, g.user['id'])
                )

        if error is None:
            try:
                db.execute(
                    'UPDATE user SET username = ?, gender = ?, birthdate = ?, phone = ? '
                    'WHERE id = ?',
                    (username, gender, birthdate, phone, g.user['id'])
                )
                db.commit()
                flash('Thông tin đã được cập nhật thành công!', 'success')
                return redirect(url_for('auth.profile'))
            except db.IntegrityError:
                error = f"Tên người dùng {username} đã tồn tại."

        flash(error, 'error')

    return render_template('auth/edit_profile.html')

@bp.route('/profile/change-password', methods=('GET', 'POST'))
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        error = None
        db = get_db()

        if not check_password_hash(g.user['password'], old_password):
            error = 'Mật khẩu hiện tại không đúng.'
        elif new_password != confirm_password:
            error = 'Mật khẩu mới không khớp.'
        
        if error is None:
            db.execute(
                'UPDATE user SET password = ? WHERE id = ?',
                (generate_password_hash(new_password), g.user['id'])
            )
            db.commit()
            flash('Mật khẩu đã được thay đổi thành công!', 'success')
            return redirect(url_for('auth.profile'))
        
        flash(error, 'error')

    return render_template('auth/change_password.html')