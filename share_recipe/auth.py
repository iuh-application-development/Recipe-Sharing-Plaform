import functools
import secrets

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from share_recipe.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        phone = request.form['phone']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not username:
            error = 'Username is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, password, username, gender, birthdate, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (email, generate_password_hash(password), username, gender, birthdate, phone),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

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