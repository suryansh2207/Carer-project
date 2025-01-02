CREATE DATABASE IF NOT EXISTS articles_db;
USE articles_db;

DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    authors TEXT NOT NULL,
    pub_date DATE NOT NULL,
    abstract TEXT NOT NULL,
    summary TEXT,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pub_date ON articles(pub_date);
CREATE INDEX idx_title ON articles(title);

select * from articles;

