from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from share_recipe.auth import login_required
from share_recipe.db import get_db

bp = Blueprint('blog', __name__)

# Thêm config cho upload ảnh
UPLOAD_FOLDER = 'share_recipe/static/uploads/blog_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=('GET',))
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page

    posts = db.execute(
        'SELECT p.id, p.title, p.created, p.author_id, '
        'u.username, bi.image_path '
        'FROM post p '
        'JOIN user u ON p.author_id = u.id '
        'LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1 '
        'ORDER BY p.created DESC '
        'LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()

    posts = [dict(post) for post in posts]
    total_posts = db.execute('SELECT COUNT(*) FROM post').fetchone()[0]
    total_pages = (total_posts + per_page - 1) // per_page

    return render_template('blog/index.html', 
                         posts=posts, 
                         page=page, 
                         total_pages=total_pages)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        cooking_time = request.form.get('cooking_time', 0)
        servings = request.form.get('servings', 0)
        
        error = None

        if not title:
            error = 'Tiêu đề không được để trống.'
        elif not ingredients:
            error = 'Nguyên liệu không được để trống.'
        elif not instructions:
            error = 'Cách làm không được để trống.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            try:
                # Insert bài viết
                cursor = db.execute(
                    'INSERT INTO post (author_id, title, description, ingredients, instructions, cooking_time, servings) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (g.user['id'], title, description, ingredients, instructions, cooking_time, servings)
                )
                post_id = cursor.lastrowid

                # Xử lý upload ảnh nếu có
                if 'image' in request.files:
                    image = request.files['image']
                    if image and allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        
                        # Tạo thư mục nếu chưa tồn tại
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        
                        # Lưu file
                        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        image.save(image_path)
                        
                        # Lưu thông tin ảnh vào database
                        db.execute(
                            'INSERT INTO blog_images (post_id, image_path, is_main_image) VALUES (?, ?, ?)',
                            (post_id, f'uploads/blog_images/{unique_filename}', 1)
                        )

                db.commit()
                return redirect(url_for('blog.index'))
                
            except Exception as e:
                print(f"Error: {e}")  # In lỗi để debug
                error = "Có lỗi xảy ra khi đăng bài. Vui lòng thử lại."
                flash(error)
                db.rollback()

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.*, u.username '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Bài viết với id {id} không tồn tại.")

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
    try:
        post = get_post(id, check_author=False)
        # Lấy ảnh của bài viết nếu có
        db = get_db()
        image = db.execute(
            'SELECT image_path FROM blog_images WHERE post_id = ? AND is_main_image = 1',
            (id,)
        ).fetchone()
        
        if image:
            post = dict(post)
            post['image_path'] = image['image_path']
            
        return render_template('blog/detail.html', post=post)
    except Exception as e:
        print(f"Error in detail route: {e}")  # For debugging
        abort(500)

@bp.route('/delete_multiple', methods=('GET',))
@login_required
def delete_multiple():
    db = get_db()
    # Lấy TẤT CẢ bài viết
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, email'
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

def save_recipe_image(file, post_id):
    if file and allowed_file(file.filename):
        # Tạo tên file unique
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Tạo đường dẫn lưu file
        upload_folder = os.path.join('share_recipe', 'static', 'uploads', 'recipe_images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Lưu file
        file.save(file_path)
        
        # Lưu thông tin vào database
        db = get_db()
        relative_path = os.path.join('uploads', 'recipe_images', unique_filename)
        db.execute(
            'INSERT INTO blog_images (post_id, image_path, is_main_image) VALUES (?, ?, ?)',
            (post_id, relative_path, 1)
        )
        db.commit()
        
        return relative_path
    return None