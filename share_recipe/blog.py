from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from share_recipe.auth import login_required
from share_recipe.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/', methods=('GET',))
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
        ' LIMIT ? OFFSET ?', (per_page, offset)
    ).fetchall()

    # Tính toán total_pages
    total_posts = db.execute('SELECT COUNT(*) FROM post').fetchone()[0]
    total_pages = (total_posts + per_page - 1) // per_page

    return render_template('blog/index.html', posts=posts, page=page, total_pages=total_pages)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/detail', methods=('GET',))
def detail(id):
    
    post = get_post(id, check_author=False) # check_author=False để bỏ qua kiểm tra tác giả
    return render_template('blog/detail.html', post=post)

@bp.route('/delete_multiple', methods=('GET',))
@login_required
def delete_multiple():
    db = get_db()
    # Lấy TẤT CẢ bài viết
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    # Lọc bài viết của người dùng hiện tại
    user_posts = [post for post in posts if post['author_id'] == g.user['id']]

    return render_template('blog/delete_multiple.html', posts=user_posts)

@bp.route('/delete_multiple', methods=('POST',))
@login_required
def delete_multiple_process():
    post_ids = request.form.getlist('post_ids')
    if not post_ids:
        flash('Vui lòng chọn ít nhất một bài viết để xóa.')
        return redirect(url_for('blog.index'))

    db = get_db()
    try:
        for post_id in post_ids:
            # Lấy thông tin bài viết để kiểm tra tác giả
            post = get_post(post_id, check_author=False)  # check_author=False để bỏ qua kiểm tra tác giả ban đầu

            if post is None:  # Bài viết không tồn tại
                flash(f'Bài viết với id {post_id} không tồn tại.')
                continue  # Bỏ qua bài viết này và tiếp tục vòng lặp

            if post['author_id'] != g.user['id']:  # Kiểm tra tác giả
                flash(f'Bạn không có quyền xóa bài viết {post["title"]}.')
                continue  # Bỏ qua bài viết này và tiếp tục vòng lặp

            db.execute('DELETE FROM post WHERE id = ?', (post_id,))  # Xóa bài viết
            flash(f'Đã xóa bài viết {post["title"]}.')

        db.commit()

    except Exception as e:
        db.rollback()
        flash(f'Đã có lỗi xảy ra: {e}')

    return redirect(url_for('blog.index'))