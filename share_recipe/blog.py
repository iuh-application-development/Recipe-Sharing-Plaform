from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random

from share_recipe.auth import login_required
from share_recipe.db import get_db

bp = Blueprint('blog', __name__)

# Thêm config cho upload ảnh
UPLOAD_FOLDER = 'share_recipe/static/uploads/blog_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_image_file(image_path):
    """Xóa file ảnh từ hệ thống file"""
    if image_path:
        # Chuyển đổi đường dẫn relative thành absolute
        full_path = os.path.join('share_recipe/static', image_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            print(f"Error deleting image file: {e}")
    return False

@bp.route('/', methods=('GET',))
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page

    posts = db.execute(
        'SELECT p.id, p.title, p.created, p.author_id, '
        'u.username, bi.image_path, '
        '(SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as like_count '
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
        tag = request.form.get('tags', '').strip()  # Chỉ lấy 1 tag
        
        error = None

        if not title:
            error = 'Tiêu đề không được để trống.'
        elif not ingredients:
            error = 'Nguyên liệu không được để trống.'
        elif not instructions:
            error = 'Cách làm không được để trống.'
        elif not tag:
            error = 'Vui lòng chọn loại món ăn.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            try:
                # Generate a unique 3-digit ID
                while True:
                    random_id = random.randint(100, 999)
                    existing_id = db.execute(
                        'SELECT id FROM post WHERE id = ?',
                        (random_id,)
                    ).fetchone()
                    if not existing_id:
                        break

                # Insert bài viết
                cursor = db.execute(
                    'INSERT INTO post (id, author_id, title, description, ingredients, instructions, cooking_time, servings) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (random_id, g.user['id'], title, description, ingredients, instructions, cooking_time, servings)
                )
                post_id = cursor.lastrowid

                # Xử lý tag
                if tag:  # Kiểm tra nếu có tag
                    # Kiểm tra xem tag đã tồn tại chưa
                    tag_row = db.execute(
                        'SELECT id FROM tags WHERE name = ?',
                        (tag,)
                    ).fetchone()
                    
                    if not tag_row:
                        # Tạo tag mới
                        cursor = db.execute(
                            'INSERT INTO tags (name) VALUES (?)',
                            (tag,)
                        )
                        tag_id = cursor.lastrowid
                    else:
                        tag_id = tag_row['id']
                    
                    # Liên kết tag với bài viết
                    db.execute(
                        'INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)',
                        (post_id, tag_id)
                    )

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
                return redirect(url_for('blog.detail', id=post_id))
                
            except Exception as e:
                print(f"Error: {e}")  # In lỗi để debug
                error = "Có lỗi xảy ra khi tạo bài viết. Vui lòng thử lại."
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
    # Convert post to dictionary
    post = dict(post)

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
                # Update bài viết
                db.execute(
                    'UPDATE post SET title = ?, description = ?, ingredients = ?, '
                    'instructions = ?, cooking_time = ?, servings = ? '
                    'WHERE id = ?',
                    (title, description, ingredients, instructions, cooking_time, servings, id)
                )

                # Xử lý upload ảnh nếu có
                if 'image' in request.files:
                    image = request.files['image']
                    if image and allowed_file(image.filename):
                        # Xóa ảnh cũ nếu có
                        old_image = db.execute(
                            'SELECT image_path FROM blog_images WHERE post_id = ? AND is_main_image = 1',
                            (id,)
                        ).fetchone()
                        
                        if old_image:
                            # Xóa file ảnh cũ
                            delete_image_file(old_image['image_path'])
                            
                        # Lưu ảnh mới
                        filename = secure_filename(image.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        
                        # Tạo thư mục nếu chưa tồn tại
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        
                        # Lưu file
                        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        image.save(image_path)
                        
                        if old_image:
                            # Update đường dẫn ảnh trong database
                            db.execute(
                                'UPDATE blog_images SET image_path = ? WHERE post_id = ? AND is_main_image = 1',
                                (f'uploads/blog_images/{unique_filename}', id)
                            )
                        else:
                            # Thêm mới nếu chưa có ảnh
                            db.execute(
                                'INSERT INTO blog_images (post_id, image_path, is_main_image) VALUES (?, ?, ?)',
                                (id, f'uploads/blog_images/{unique_filename}', 1)
                            )

                db.commit()
                return redirect(url_for('blog.detail', id=id))
                
            except Exception as e:
                print(f"Error: {e}")
                error = "Có lỗi xảy ra khi cập nhật bài viết. Vui lòng thử lại."
                flash(error)
                db.rollback()

    # Lấy thông tin ảnh hiện tại
    db = get_db()
    current_image = db.execute(
        'SELECT image_path FROM blog_images WHERE post_id = ? AND is_main_image = 1',
        (id,)
    ).fetchone()
    
    if current_image:
        post['image'] = current_image['image_path']

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    try:
        # Lấy thông tin ảnh trước khi xóa bài viết
        images = db.execute(
            'SELECT image_path FROM blog_images WHERE post_id = ?',
            (id,)
        ).fetchall()
        
        # Xóa bài viết
        db.execute('DELETE FROM post WHERE id = ?', (id,))
        
        # Xóa các file ảnh
        for image in images:
            delete_image_file(image['image_path'])
            
        db.commit()
        flash('Bài viết đã được xóa thành công.')
    except Exception as e:
        print(f"Error deleting post: {e}")
        flash('Có lỗi xảy ra khi xóa bài viết.')
        db.rollback()
        
    return redirect(url_for('blog.index'))

@bp.route('/delete_multiple', methods=['GET', 'POST'])
@login_required
def delete_multiple():
    if request.method == 'GET':
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
        
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        
        if not post_ids:
            return jsonify({'success': False, 'message': 'Không có công thức nào được chọn'})
            
        db = get_db()
        
        # Verify that all posts belong to the current user
        for post_id in post_ids:
            post = get_post(post_id, check_author=True)
            if post['author_id'] != g.user['id']:
                return jsonify({'success': False, 'message': 'Bạn không có quyền xóa công thức này'})
        
        # Delete associated images first
        for post_id in post_ids:
            # Get image paths
            images = db.execute(
                'SELECT image_path FROM blog_images WHERE post_id = ?',
                (post_id,)
            ).fetchall()
            
            # Delete image files
            for image in images:
                delete_image_file(image['image_path'])
            
            # Delete image records
            db.execute('DELETE FROM blog_images WHERE post_id = ?', (post_id,))
        
        # Delete the posts
        for post_id in post_ids:
            db.execute('DELETE FROM post WHERE id = ?', (post_id,))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Xóa công thức thành công'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def convert_utc_to_local(utc_dt):
    """Convert UTC datetime to Vietnam timezone (UTC+7)"""
    if utc_dt is None:
        return None
    local_tz = timedelta(hours=7)
    return utc_dt + local_tz

@bp.route('/<int:id>/detail', methods=('GET', 'POST'))
def detail(id):
    try:
        post = get_post(id, check_author=False)
        if post is None:
            abort(404)
            
        # Convert post to dictionary
        post = dict(post)
        
        db = get_db()
        
        # Get tags for the post
        tags = db.execute(
            'SELECT t.id, t.name FROM tags t '
            'JOIN post_tags pt ON t.id = pt.tag_id '
            'WHERE pt.post_id = ?',
            (id,)
        ).fetchall()
        post['tags'] = [dict(tag) for tag in tags]
        
        # Handle comment submission
        if request.method == 'POST' and g.user:
            content = request.form.get('content')
            if content:
                db.execute(
                    'INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)',
                    (id, g.user['id'], content)
                )
                db.commit()
                return redirect(url_for('blog.detail', id=id))
        
        # Get post image
        image = db.execute(
            'SELECT image_path FROM blog_images WHERE post_id = ? AND is_main_image = 1',
            (id,)
        ).fetchone()
        
        # Get comments with reaction counts and user's reactions
        comments_query = '''
            SELECT c.*, u.username, u.avatar_path,
                (SELECT COUNT(DISTINCT user_id) FROM comment_reactions cr 
                 WHERE cr.comment_id = c.id AND cr.reaction_type = 'like') as likes_count,
                (SELECT COUNT(DISTINCT user_id) FROM comment_reactions cr 
                 WHERE cr.comment_id = c.id AND cr.reaction_type = 'dislike') as dislikes_count
        '''
        
        # Get current user's reaction if logged in
        if g.user:
            comments_query += ''',
                (SELECT reaction_type FROM comment_reactions cr 
                 WHERE cr.comment_id = c.id AND cr.user_id = ?) as user_reaction
            '''
        else:
            comments_query += ', NULL as user_reaction'
        
        comments_query += '''
            FROM comments c JOIN user u ON c.author_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created DESC
        '''
        
        if g.user:
            comments = db.execute(comments_query, (g.user['id'], id)).fetchall()
        else:
            comments = db.execute(comments_query, (id,)).fetchall()
        
        # Convert comments to list of dictionaries and convert timezone
        comments = [dict(comment) for comment in comments]
        for comment in comments:
            comment['created'] = convert_utc_to_local(comment['created'])
        
        # Check if current user has favorited this post
        is_favorite = False
        if g.user:
            favorite = db.execute(
                'SELECT * FROM favorites WHERE user_id = ? AND post_id = ?',
                (g.user['id'], id)
            ).fetchone()
            is_favorite = favorite is not None
        
        if image:
            post['image_path'] = image['image_path']
            
        # Check if current user has saved this post
        is_saved = False
        if g.user:
            saved = db.execute(
                'SELECT * FROM saved_recipes WHERE user_id = ? AND post_id = ?',
                (g.user['id'], id)
            ).fetchone()
            is_saved = saved is not None
        
        return render_template('blog/detail.html', 
                             post=post, 
                             comments=comments,
                             is_favorite=is_favorite,
                             is_saved=is_saved)
    except Exception as e:
        print(f"Error in detail route: {e}")  # For debugging
        abort(500)

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

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    db = get_db()
    # Lấy thông tin comment và kiểm tra quyền xóa
    comment = db.execute(
        'SELECT c.*, p.id as post_id FROM comments c '
        'JOIN post p ON c.post_id = p.id '
        'WHERE c.id = ?',
        (comment_id,)
    ).fetchone()

    if comment is None:
        abort(404, "Bình luận không tồn tại.")
    
    # Chỉ cho phép người viết comment xóa comment của họ
    if comment['author_id'] != g.user['id']:
        abort(403, "Không có quyền xóa bình luận này.")

    db.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    db.commit()
    
    return redirect(url_for('blog.detail', id=comment['post_id']))

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    selected_tag = request.args.get('tag', '')
    sort_by = request.args.get('sort', 'newest')
    
    # Chỉ chuyển hướng nếu không có bất kỳ tiêu chí tìm kiếm nào
    if not query and not selected_tag:
        return redirect(url_for('blog.index'))

    db = get_db()
    
    # Base query
    base_query = '''
        SELECT DISTINCT p.id, p.title, p.description, p.created, p.author_id,
        u.username, bi.image_path,
        (SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as like_count,
        t.name as tag
        FROM post p
        JOIN user u ON p.author_id = u.id
        LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1
        LEFT JOIN post_tags pt ON p.id = pt.post_id
        LEFT JOIN tags t ON pt.tag_id = t.id
    '''
    
    # Build WHERE clause
    conditions = []
    params = []
    
    if query:
        conditions.append('p.title LIKE ?')
        params.append(f'%{query}%')
    
    if selected_tag:
        conditions.append('t.name = ?')
        params.append(selected_tag)
    
    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)
    
    # Add ORDER BY clause based on sort_by
    if sort_by == 'likes':
        base_query += ' ORDER BY like_count DESC'
    else:  # Default to newest
        base_query += ' ORDER BY p.created DESC'
    
    # Execute query
    posts = db.execute(base_query, params).fetchall()
    posts = [dict(post) for post in posts]
    
    return render_template('blog/search.html', 
                         posts=posts, 
                         query=query, 
                         selected_tag=selected_tag,
                         sort_by=sort_by)

@bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    content = request.form.get('content')
    if not content:
        abort(400, "Nội dung bình luận không được để trống")

    db = get_db()
    # Lấy thông tin comment và kiểm tra quyền chỉnh sửa
    comment = db.execute(
        'SELECT c.*, p.id as post_id FROM comments c '
        'JOIN post p ON c.post_id = p.id '
        'WHERE c.id = ?',
        (comment_id,)
    ).fetchone()

    if comment is None:
        abort(404, "Bình luận không tồn tại.")
    
    # Chỉ cho phép người viết comment chỉnh sửa comment của họ
    if comment['author_id'] != g.user['id']:
        abort(403, "Không có quyền chỉnh sửa bình luận này.")

    db.execute(
        'UPDATE comments SET content = ? WHERE id = ?',
        (content, comment_id)
    )
    db.commit()
    
    return redirect(url_for('blog.detail', id=comment['post_id']))

@bp.route('/comment/<int:comment_id>/react', methods=['POST'])
@login_required
def react_to_comment(comment_id):
    reaction_type = request.form.get('reaction_type')
    if reaction_type not in ['like', 'dislike']:
        return jsonify({'success': False, 'error': 'Invalid reaction type'}), 400

    db = get_db()
    try:
        # Check if comment exists
        comment = db.execute(
            'SELECT * FROM comments WHERE id = ?', (comment_id,)
        ).fetchone()
        
        if comment is None:
            return jsonify({'success': False, 'error': 'Comment not found'}), 404

        # Check if user already reacted to this comment
        existing_reaction = db.execute(
            'SELECT * FROM comment_reactions WHERE comment_id = ? AND user_id = ?',
            (comment_id, g.user['id'])
        ).fetchone()

        if existing_reaction:
            if existing_reaction['reaction_type'] == reaction_type:
                # Remove reaction if clicking the same button
                db.execute(
                    'DELETE FROM comment_reactions WHERE id = ?',
                    (existing_reaction['id'],)
                )
                action = 'removed'
            else:
                # Update reaction if changing from like to dislike or vice versa
                db.execute(
                    'UPDATE comment_reactions SET reaction_type = ? WHERE id = ?',
                    (reaction_type, existing_reaction['id'])
                )
                action = 'changed'
        else:
            # Add new reaction
            db.execute(
                'INSERT INTO comment_reactions (comment_id, user_id, reaction_type) VALUES (?, ?, ?)',
                (comment_id, g.user['id'], reaction_type)
            )
            action = 'added'

        db.commit()

        # Get updated counts using DISTINCT to count unique users
        likes = db.execute(
            'SELECT COUNT(DISTINCT user_id) as count FROM comment_reactions WHERE comment_id = ? AND reaction_type = ?',
            (comment_id, 'like')
        ).fetchone()['count']
        
        dislikes = db.execute(
            'SELECT COUNT(DISTINCT user_id) as count FROM comment_reactions WHERE comment_id = ? AND reaction_type = ?',
            (comment_id, 'dislike')
        ).fetchone()['count']

        return jsonify({
            'success': True,
            'action': action,
            'likes': likes,
            'dislikes': dislikes
        })

    except Exception as e:
        print(f"Error in react_to_comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:id>/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite(id):
    """Toggle favorite status for a recipe."""
    db = get_db()
    error = None

    try:
        # Check if post exists
        post = db.execute('SELECT * FROM post WHERE id = ?', (id,)).fetchone()
        if post is None:
            error = 'Công thức không tồn tại.'
        else:
            # Check if already favorited
            favorite = db.execute(
                'SELECT * FROM favorites WHERE user_id = ? AND post_id = ?',
                (g.user['id'], id)
            ).fetchone()

            if favorite is None:
                # Add to favorites
                db.execute(
                    'INSERT INTO favorites (user_id, post_id) VALUES (?, ?)',
                    (g.user['id'], id)
                )
                db.commit()
                message = 'Đã thêm vào yêu thích!'
                is_favorite = True
            else:
                # Remove from favorites
                db.execute(
                    'DELETE FROM favorites WHERE user_id = ? AND post_id = ?',
                    (g.user['id'], id)
                )
                db.commit()
                message = 'Đã xóa khỏi yêu thích!'
                is_favorite = False

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': message, 'is_favorite': is_favorite})
            else:
                flash(message, 'success')
                return redirect(url_for('blog.detail', id=id))

    except Exception as e:
        error = f'Có lỗi xảy ra: {str(e)}'

    if error is not None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': error}), 500
        flash(error, 'error')
    
    return redirect(url_for('blog.detail', id=id))

@bp.route('/favorites')
@login_required
def favorites():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page
    
    # Lấy danh sách bài viết yêu thích
    favorites = db.execute(
        'SELECT p.id, p.title, p.created, p.author_id, '
        'u.username, bi.image_path, '
        '(SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as like_count '
        'FROM favorites f '
        'JOIN post p ON f.post_id = p.id '
        'JOIN user u ON p.author_id = u.id '
        'LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1 '
        'WHERE f.user_id = ? '
        'ORDER BY f.created_at DESC '
        'LIMIT ? OFFSET ?',
        (g.user['id'], per_page, offset)
    ).fetchall()
    
    # Đếm tổng số bài viết yêu thích
    total_favorites = db.execute(
        'SELECT COUNT(*) FROM favorites WHERE user_id = ?',
        (g.user['id'],)
    ).fetchone()[0]
    
    total_pages = (total_favorites + per_page - 1) // per_page
    
    return render_template('blog/favorites.html',
                         favorites=favorites,
                         page=page,
                         total_pages=total_pages)

@bp.route('/<int:id>/toggle_save', methods=['POST'])
@login_required
def toggle_save(id):
    """Toggle save status for a recipe."""
    db = get_db()
    error = None

    try:
        # Check if post exists
        post = db.execute('SELECT * FROM post WHERE id = ?', (id,)).fetchone()
        if post is None:
            error = 'Công thức không tồn tại.'
        else:
            # Check if already saved
            saved = db.execute(
                'SELECT * FROM saved_recipes WHERE user_id = ? AND post_id = ?',
                (g.user['id'], id)
            ).fetchone()

            if saved is None:
                # Save the recipe
                db.execute(
                    'INSERT INTO saved_recipes (user_id, post_id) VALUES (?, ?)',
                    (g.user['id'], id)
                )
                db.commit()
                message = 'Đã lưu công thức!'
                is_saved = True
            else:
                # Unsave the recipe
                db.execute(
                    'DELETE FROM saved_recipes WHERE user_id = ? AND post_id = ?',
                    (g.user['id'], id)
                )
                db.commit()
                message = 'Đã bỏ lưu công thức!'
                is_saved = False

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': message, 'is_saved': is_saved})
            else:
                flash(message, 'success')
                return redirect(url_for('blog.detail', id=id))

    except Exception as e:
        error = f'Có lỗi xảy ra: {str(e)}'

    if error is not None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': error}), 500
        flash(error, 'error')
    
    return redirect(url_for('blog.detail', id=id))

@bp.route('/saved_recipes')
@login_required
def saved_recipes():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page

    # Lấy danh sách công thức đã lưu với phân trang
    saved_recipes = db.execute(
        'SELECT p.*, u.username as author_name, bi.image_path, '
        '(SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as like_count '
        'FROM post p '
        'JOIN saved_recipes sr ON p.id = sr.post_id '
        'JOIN user u ON p.author_id = u.id '
        'LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1 '
        'WHERE sr.user_id = ? '
        'ORDER BY sr.created DESC '
        'LIMIT ? OFFSET ?',
        (g.user['id'], per_page, offset)
    ).fetchall()

    # Đếm tổng số công thức đã lưu
    total_saved = db.execute(
        'SELECT COUNT(*) FROM saved_recipes WHERE user_id = ?',
        (g.user['id'],)
    ).fetchone()[0]

    total_pages = (total_saved + per_page - 1) // per_page

    return render_template('blog/saved_recipes.html',
                         saved_recipes=saved_recipes,
                         page=page,
                         total_pages=total_pages)

def get_saved_status(post_id):
    """Check if current user has saved the post."""
    if g.user:
        db = get_db()
        saved = db.execute(
            'SELECT * FROM saved_recipes WHERE user_id = ? AND post_id = ?',
            (g.user['id'], post_id)
        ).fetchone()
        return saved is not None
    return False

@bp.route('/category/<category>')
def category(category):
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page

    posts = db.execute(
        'SELECT p.id, p.title, p.created, p.author_id, '
        'u.username, bi.image_path, '
        '(SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as like_count '
        'FROM post p '
        'JOIN user u ON p.author_id = u.id '
        'LEFT JOIN blog_images bi ON p.id = bi.post_id AND bi.is_main_image = 1 '
        'JOIN post_tags pt ON p.id = pt.post_id '
        'JOIN tags t ON pt.tag_id = t.id '
        'WHERE t.name = ? '
        'ORDER BY p.created DESC '
        'LIMIT ? OFFSET ?',
        (category, per_page, offset)
    ).fetchall()

    posts = [dict(post) for post in posts]

    # Get total number of posts for pagination
    total_posts = db.execute(
        'SELECT COUNT(*) FROM post p '
        'JOIN post_tags pt ON p.id = pt.post_id '
        'JOIN tags t ON pt.tag_id = t.id '
        'WHERE t.name = ?',
        (category,)
    ).fetchone()[0]

    total_pages = (total_posts + per_page - 1) // per_page

    return render_template('blog/category.html',
                         posts=posts,
                         category=category,
                         page=page,
                         total_pages=total_pages,
                         total_posts=total_posts)