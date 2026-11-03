-- Alzheimer's Disease Classification and Cognitive Assessment Database Schema
-- Database: alzheimers_project

CREATE DATABASE IF NOT EXISTS alzheimers_project
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE alzheimers_project;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. MRI Predictions Table
CREATE TABLE IF NOT EXISTS mri_predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    predicted_category VARCHAR(60) NOT NULL,
    confidence FLOAT NOT NULL,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mri_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. Cognitive Assessments Table
CREATE TABLE IF NOT EXISTS cognitive_assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_score INT NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assessment_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. Assessment Answers Table
CREATE TABLE IF NOT EXISTS assessment_answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_answer VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    CONSTRAINT fk_answer_assessment
        FOREIGN KEY (assessment_id) REFERENCES cognitive_assessments(assessment_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 5. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    report_path VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_report_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Indexes for performance
CREATE INDEX idx_mri_user_date ON mri_predictions(user_id, prediction_date DESC);
CREATE INDEX idx_cog_user_date ON cognitive_assessments(user_id, assessment_date DESC);
CREATE INDEX idx_reports_user_date ON reports(user_id, generated_at DESC);
