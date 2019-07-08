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
  author INTEGER,
  type TEXT,
  link TEXT,
  PRIMARY KEY (ID),
  FOREIGN KEY (author) REFERENCES users(ID)
);

CREATE TABLE tags (
  post INTEGER,
  tag TEXT,
  PRIMARY KEY (post, tag),
  FOREIGN KEY (post) REFERENCES posts(ID)
);

CREATE TABLE categories (
  ID INTEGER,
  name TEXT,
  parent INTEGER,
  PRIMARY KEY (ID),
  FOREIGN KEY (parent) REFERENCES categories(ID)
);

CREATE TABLE post_category (
  post INTEGER,
  category INTEGER,
  PRIMARY KEY (post, category),
  FOREIGN KEY (post) REFERENCES posts(ID),
  FOREIGN KEY (category) REFERENCES categories(ID)
);

CREATE TABLE media (
  ID INTEGER,
  type TEXT,
  date TEXT,
  link TEXT,
  PRIMARY KEY (id)
);
