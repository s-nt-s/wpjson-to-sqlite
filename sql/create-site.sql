CREATE TABLE users (
  id INTEGER,
  name TEXT,
  description TEXT,
  avatar TEXT,
  link TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE posts (
  id INTEGER,
  title TEXT,
  content TEXT,
  date DATETIME,
  author INTEGER,
  type TEXT,
  link TEXT,
  PRIMARY KEY (id),
  FOREIGN KEY (author) REFERENCES users(id)
);

CREATE TABLE tags (
  post INTEGER,
  tag TEXT,
  PRIMARY KEY (post, tag),
  FOREIGN KEY (post) REFERENCES posts(id)
);

CREATE TABLE categories (
  id INTEGER,
  name TEXT,
  parent INTEGER,
  PRIMARY KEY (id),
  FOREIGN KEY (parent) REFERENCES categories(id)
);

CREATE TABLE post_category (
  post INTEGER,
  category INTEGER,
  PRIMARY KEY (post, category),
  FOREIGN KEY (post) REFERENCES posts(id),
  FOREIGN KEY (category) REFERENCES categories(id)
);

CREATE TABLE media (
  id INTEGER,
  type TEXT,
  date DATETIME,
  link TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE comments (
  id INTEGER,
  post INTEGER,
  type TEXT,
  content TEXT,
  date DATETIME,
  author INTEGER,
  parent INTEGER,
  PRIMARY KEY (id),
  FOREIGN KEY (post) REFERENCES posts(id),
  FOREIGN KEY (author) REFERENCES users(id),
  FOREIGN KEY (parent) REFERENCES comments(id)
);
