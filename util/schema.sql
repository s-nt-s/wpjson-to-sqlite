DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS post_category;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS media;

CREATE TABLE users (
  ID INTEGER,
  name TEXT,
  description TEXT,
  avatar TEXT,
  link TEXT,
  PRIMARY KEY (ID)
);

CREATE TABLE posts (
  ID INTEGER,
  title TEXT,
  content TEXT,
  date DATETIME,
  author INTEGER REFERENCES users(ID),
  type TEXT,
  link TEXT,
  PRIMARY KEY (ID)
);

CREATE TABLE tags (
  post INTEGER REFERENCES posts(ID),
  tag TEXT,
  PRIMARY KEY (post, tag)
);

CREATE TABLE categories (
  ID INTEGER,
  name TEXT,
  parent INTEGER REFERENCES categories(ID),
  PRIMARY KEY (ID)
);

CREATE TABLE post_category (
  post INTEGER REFERENCES posts(ID),
  category INTEGER REFERENCES categories(ID),
  PRIMARY KEY (post, category)
);

/*
CREATE TABLE media (
  ID INTEGER,
  type TEXT,
  date TEXT,
  link TEXT,
  PRIMARY KEY (id)
);
*/
