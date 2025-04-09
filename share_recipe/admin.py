import logging
import secrets
import random
import string

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, session
from werkzeug.security import generate_password_hash

from share_recipe.auth import login_required
from share_recipe.db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')

def get_user_by_id(id):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (id,)).fetchone()
    if user:
        user = dict(user)
        user['is_blocked'] = bool(user['is_blocked'])
    return user

@bp.route('/users')
@login_required
def users():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    db = get_db()
    users = db.execute('SELECT * FROM user').fetchall()
    return render_template('admin/users.html', users=users)

@bp.route('/users/create', methods=('GET', 'POST'))
@login_required
def create_user():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        username = request.form['username']

        db = get_db()
        error = None

        if not email:
            error = 'Email là bắt buộc.'
        elif not password:
            error = 'Mật khẩu là bắt buộc.'
        elif not username:
            error = 'Tên người dùng là bắt buộc.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, password, username, role) VALUES (?, ?, ?, ?)",
                    (email, generate_password_hash(password), username, role),
                )
                db.commit()
            except db.IntegrityError:
                error = f"Email {email} đã được đăng ký."
            else:
                return redirect(url_for("admin.users"))

        flash(error)

    return render_template('admin/create_user.html')

@bp.route('/users/<int:id>/block', methods=['POST'])
@login_required
def block_user(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    user = get_user_by_id(id)
    if not user:
        abort(404)

    if user and user['id'] == session.get('user_id'):
        session.clear()
        

    db = get_db()
    db.execute('UPDATE user SET is_blocked = 1 WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/unblock', methods=['POST'])
@login_required
def unblock_user(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    user = get_user_by_id(id)
    if not user:
        abort(404)

    db = get_db()
    db.execute('UPDATE user SET is_blocked = 0 WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/reset_password', methods=['POST'])
@login_required
def reset_password(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    user = get_user_by_id(id)
    if not user:
        abort(404)

    new_password = ''.join(random.choices(string.digits, k=8))
    hashed_password = generate_password_hash(new_password)
    db = get_db()
    db.execute('UPDATE user SET password = ? WHERE id = ?', (hashed_password, id))
    db.commit()

    # Gửi new_password cho người dùng qua email hoặc phương thức an toàn
    flash(f'Mật khẩu mới là: {new_password}')  # XÓA BỎ trong production
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update_user(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    user = get_user_by_id(id)
    if not user:
        abort(404)

    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        error = None

        if not username:
            error = 'Tên người dùng là bắt buộc.'

        if error is None:
            try:
                db = get_db()
                db.execute(
                    'UPDATE user SET username = ?, role = ? WHERE id = ?',
                    (username, role, id)
                )
                db.commit()
                return redirect(url_for('admin.users'))
            except db.IntegrityError:
                error = f"Lỗi khi cập nhật người dùng."

        flash(error)

    return render_template('admin/update_user.html', user=user)

@bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    user = get_user_by_id(id)
    if not user:
        abort(404)

    db = get_db()
    try:
        db.execute('DELETE FROM user WHERE id = ?', (id,))
        db.commit()
    except Exception as e:
        logging.error(f"Lỗi khi xóa người dùng (ID: {id}): {e}")
        flash(f"Lỗi khi xóa người dùng.")
        db.rollback()
    return redirect(url_for('admin.users'))

@bp.route('/')
@login_required
def dashboard():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))
    
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) as count FROM user').fetchone()['count']
    total_posts = db.execute('SELECT COUNT(*) as count FROM post').fetchone()['count']
    recent_posts = db.execute('''
        SELECT p.*, u.email as author_email 
        FROM post p 
        JOIN user u ON p.author_id = u.id 
        ORDER BY p.created DESC 
        LIMIT 5
    ''').fetchall()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_posts=total_posts,
                         recent_posts=recent_posts)

@bp.route('/posts')
@login_required
def posts():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    sort_order = request.args.get('sort', 'newest')
    db = get_db()
    if sort_order == 'oldest':
        posts = db.execute('SELECT * FROM post ORDER BY created ASC').fetchall()
    else:
        posts = db.execute('SELECT * FROM post ORDER BY created DESC').fetchall()
    return render_template('admin/posts.html', posts=posts)

@bp.route('/posts/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))
    
    db = get_db()
    post = db.execute('SELECT * FROM post WHERE id = ?', (id,)).fetchone()
    if not post:
        abort(404)
    
    try:
        db.execute('DELETE FROM post WHERE id = ?', (id,))
        db.commit()
    except Exception as e:
        logging.error(f"Lỗi khi xóa bài viết (ID: {id}): {e}")
        flash(f"Lỗi khi xóa bài viết.")
        db.rollback()
    
    return redirect(url_for('admin.posts'))

@bp.route('/delete_posts', methods=['POST'])
@login_required
def delete_posts():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    ids = request.json.get('ids', [])
    db = get_db()
    try:
        db.executemany('DELETE FROM post WHERE id = ?', [(id,) for id in ids])
        db.commit()
    except Exception as e:
        logging.error(f"Error deleting posts: {e}")
        db.rollback()
        return {'success': False}, 500
    return {'success': True}, 200

@bp.route('/delete_users', methods=['POST'])
@login_required
def delete_users():
    if g.user['role'] != 'admin':
        return redirect(url_for('index'))

    ids = request.json.get('ids', [])
    db = get_db()
    try:
        db.executemany('DELETE FROM user WHERE id = ?', [(id,) for id in ids])
        db.commit()
    except Exception as e:
        logging.error(f"Error deleting users: {e}")
        db.rollback()
        return {'success': False}, 500
    return {'success': True}, 200

def create_default_admin():
    db = get_db()
    admin = db.execute('SELECT * FROM user WHERE role = ?', ('admin',)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO user (email, password, username, role) VALUES (?, ?, ?, ?)",
            ('admin@example.com', generate_password_hash('admin123'), 'admin', 'admin'),
        )
        db.commit()
        print('Tài khoản admin mặc định đã được tạo:')
        print('Email: admin@example.com')
        print('Username: admin')
        print('Password: admin123')