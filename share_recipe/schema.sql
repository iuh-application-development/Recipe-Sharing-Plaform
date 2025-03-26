DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS blog_images;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS comment_reactions;
DROP TABLE IF EXISTS saved_recipes;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    username TEXT NOT NULL,
    gender TEXT,
    birthdate TEXT,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    is_blocked INTEGER NOT NULL DEFAULT 0,
    avatar_path TEXT
);

CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    description TEXT,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL,
    cooking_time INTEGER,
    servings INTEGER,
    FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE blog_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    is_main_image INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
    UNIQUE(user_id, post_id)
);

CREATE TABLE comment_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    reaction_type TEXT NOT NULL CHECK(reaction_type IN ('like', 'dislike')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE CASCADE,
    UNIQUE(comment_id, user_id)
);

CREATE TABLE saved_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (post_id) REFERENCES post (id)
);