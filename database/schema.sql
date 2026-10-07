CREATE DATABASE IF NOT EXISTS SkillSync;
USE SkillSync;

CREATE TABLE User (
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

CREATE TABLE Project_Details (
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

CREATE TABLE Project_Members (
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