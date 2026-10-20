CREATE TABLE IF NOT EXISTS Peer_Review (
    Review_ID INT AUTO_INCREMENT PRIMARY KEY,
    Project_ID INT NOT NULL,
    Reviewer_ID INT NOT NULL,
    Reviewee_ID INT NOT NULL,
    Rating INT NOT NULL,
    Comment TEXT NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Edited_At DATETIME NULL,

    FOREIGN KEY (Project_ID)
        REFERENCES Project_Details(Project_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Reviewer_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Reviewee_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    UNIQUE (Project_ID, Reviewer_ID, Reviewee_ID),

    CHECK (Rating BETWEEN 1 AND 5)
);