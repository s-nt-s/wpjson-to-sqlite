DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS posts;

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
  type INTEGER,
  PRIMARY KEY (post, tag, type)
);
