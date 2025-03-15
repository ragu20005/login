USE scraper_project;

CREATE TABLE IF NOT EXISTS serp_searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    search_type VARCHAR(50) NOT NULL,
    query VARCHAR(255) NOT NULL,
    results JSON,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);