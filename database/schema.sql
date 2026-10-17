CREATE DATABASE IF NOT EXISTS SkillSync;
USE SkillSync;

-- 1. User Table
CREATE TABLE IF NOT EXISTS User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(200) NOT NULL,
    Role ENUM(
        'Team Leader',
        'Team Member',
        'Mentor',
        'Coordinator'
    ) NOT NULL,
    Email VARCHAR(200) UNIQUE NOT NULL,
    Password VARCHAR(200) NOT NULL
);

-- 2. Project Details Table
CREATE TABLE IF NOT EXISTS Project_Details (
    Project_ID INT AUTO_INCREMENT PRIMARY KEY,
    Project_Name VARCHAR(200) NOT NULL,
    Project_Description TEXT NOT NULL,
    Members_Required INT NOT NULL,
    Skill_Required VARCHAR(200) NOT NULL,
    Submission_Date DATE NOT NULL,
    User_ID INT NOT NULL,

    FOREIGN KEY (User_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE
);

-- 3. Project Members Table
CREATE TABLE IF NOT EXISTS Project_Members (
    Member_ID INT AUTO_INCREMENT PRIMARY KEY,
    Project_ID INT NOT NULL,
    User_ID INT NOT NULL,
    Status ENUM(
        'Pending',
        'Accepted',
        'Rejected'
    ) DEFAULT 'Pending',

    FOREIGN KEY (Project_ID)
        REFERENCES Project_Details(Project_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (User_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    UNIQUE (Project_ID, User_ID)
);

-- 4. Mentor Project Assignment Table
CREATE TABLE IF NOT EXISTS Mentor_Project (
    Mentor_Project_ID INT AUTO_INCREMENT PRIMARY KEY,
    Mentor_ID INT NOT NULL,
    Project_ID INT NOT NULL,
    Assigned_Date DATE DEFAULT (CURRENT_DATE),

    FOREIGN KEY (Mentor_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Project_ID)
        REFERENCES Project_Details(Project_ID)
        ON DELETE CASCADE,

    UNIQUE (Mentor_ID, Project_ID)
);

-- 5. Project Feedback Table
CREATE TABLE IF NOT EXISTS Project_Feedback (
    Feedback_ID INT AUTO_INCREMENT PRIMARY KEY,
    Mentor_ID INT NOT NULL,
    Project_ID INT NOT NULL,
    Rating INT NOT NULL,
    Feedback_Text TEXT,
    Feedback_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (Mentor_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Project_ID)
        REFERENCES Project_Details(Project_ID)
        ON DELETE CASCADE,

    CHECK (Rating BETWEEN 1 AND 5)
);

-- 6. Mentor Interaction Table
CREATE TABLE IF NOT EXISTS Mentor_Interaction (
    Interaction_ID INT AUTO_INCREMENT PRIMARY KEY,
    Mentor_ID INT NOT NULL,
    Project_ID INT NOT NULL,
    Interaction_Title VARCHAR(200) NOT NULL,
    Interaction_Date DATETIME NOT NULL,
    Status ENUM(
        'Pending',
        'Completed',
        'Cancelled'
    ) DEFAULT 'Pending',
    Notes TEXT,

    FOREIGN KEY (Mentor_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Project_ID)
        REFERENCES Project_Details(Project_ID)
        ON DELETE CASCADE
);

-- 7. Interaction Attendance Table
CREATE TABLE IF NOT EXISTS Interaction_Attendance (
    Attendance_ID INT AUTO_INCREMENT PRIMARY KEY,
    Interaction_ID INT NOT NULL,
    Student_ID INT NOT NULL,
    Attendance_Status ENUM(
        'Present',
        'Absent'
    ) DEFAULT 'Absent',

    FOREIGN KEY (Interaction_ID)
        REFERENCES Mentor_Interaction(Interaction_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Student_ID)
        REFERENCES User(User_ID)
        ON DELETE CASCADE,

    UNIQUE (Interaction_ID, Student_ID)
);