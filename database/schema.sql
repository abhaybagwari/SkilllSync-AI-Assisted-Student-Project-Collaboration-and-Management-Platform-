CREATE DATABASE IF NOT EXISTS SkillSync;

USE SkillSync;

CREATE TABLE User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Role ENUM('Team Leader', 'Team Member', 'Mentor', 'Coordinator') NOT NULL,
    Email VARCHAR(200) UNIQUE NOT NULL,
    Password VARCHAR(200) NOT NULL
);

CREATE TABLE Confirmation (
    Confirmation_Password VARCHAR(200) NOT NULL
);

CREATE TABLE Project_Details (
    Project_ID INT AUTO_INCREMENT PRIMARY KEY,
    Project_Name VARCHAR(200) NOT NULL,
    Members_Required INT NOT NULL,
    Skill_Required VARCHAR(200) NOT NULL,
    Submission_Date DATE NOT NULL
);

CREATE TABLE Your_Project (
    Project_ID INT AUTO_INCREMENT PRIMARY KEY,
    Project VARCHAR(200) NOT NULL,
    Members INT NOT NULL,
    Status VARCHAR(200) NOT NULL
);