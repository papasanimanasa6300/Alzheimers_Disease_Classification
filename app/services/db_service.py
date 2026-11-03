"""
Database Service Layer for Alzheimer's Classification System.
Handles connection lifecycle, connection pooling, and secure parameterized queries
for MySQL database 'alzheimers_project'.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling, Error

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "alzheimers_project")

_pool = None


def get_db_pool():
    """Initialize or retrieve MySQL connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="alzheimer_pool",
                pool_size=5,
                pool_reset_session=True,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True
            )
        except Error as e:
            # Fallback to direct connection if pooling error occurs
            return None
    return _pool


def get_connection():
    """Acquire a MySQL connection from pool or direct."""
    pool = get_db_pool()
    if pool:
        try:
            return pool.get_connection()
        except Error:
            pass
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )


# ==========================================
# USER AUTHENTICATION & MANAGEMENT
# ==========================================

def create_user(username, email, password_hash):
    """Create a new user with hashed password."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (username, email, password_hash))
        user_id = cursor.lastrowid
        cursor.close()
        return user_id
    finally:
        conn.close()


def get_user_by_username(username):
    """Retrieve user record by username."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def get_user_by_email(email):
    """Retrieve user record by email."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Retrieve user record by user_id."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id, username, email, created_at FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


# ==========================================
# MRI PREDICTIONS
# ==========================================

def save_mri_prediction(user_id, image_path, predicted_category, confidence):
    """Record an MRI classification prediction."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            INSERT INTO mri_predictions (user_id, image_path, predicted_category, confidence)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, image_path, predicted_category, float(confidence)))
        prediction_id = cursor.lastrowid
        cursor.close()
        return prediction_id
    finally:
        conn.close()


def get_user_mri_predictions(user_id, limit=None):
    """Fetch prediction history for a specific user ordered by date descending."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT prediction_id, user_id, image_path, predicted_category, confidence, prediction_date
            FROM mri_predictions
            WHERE user_id = %s
            ORDER BY prediction_date DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def get_prediction_by_id(prediction_id, user_id):
    """Retrieve single prediction record belonging to user."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM mri_predictions
            WHERE prediction_id = %s AND user_id = %s
        """
        cursor.execute(query, (prediction_id, user_id))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def get_total_mri_count(user_id):
    """Count total MRI predictions for user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mri_predictions WHERE user_id = %s", (user_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    finally:
        conn.close()


def get_latest_mri_prediction(user_id):
    """Fetch most recent MRI prediction for dashboard."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM mri_predictions
            WHERE user_id = %s
            ORDER BY prediction_date DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def delete_mri_prediction(prediction_id, user_id):
    """Delete an MRI prediction record belonging to user."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Verify ownership and get image path for cleanup
        cursor.execute("SELECT * FROM mri_predictions WHERE prediction_id = %s AND user_id = %s", (prediction_id, user_id))
        record = cursor.fetchone()
        if not record:
            cursor.close()
            return False, None

        cursor.execute("DELETE FROM mri_predictions WHERE prediction_id = %s AND user_id = %s", (prediction_id, user_id))
        cursor.close()
        return True, record
    finally:
        conn.close()


# ==========================================
# COGNITIVE ASSESSMENTS
# ==========================================

def save_cognitive_assessment(user_id, total_score, answers_breakdown):
    """
    Save complete cognitive assessment session and granular question responses.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Insert parent assessment
        query_assess = """
            INSERT INTO cognitive_assessments (user_id, total_score)
            VALUES (%s, %s)
        """
        cursor.execute(query_assess, (user_id, int(total_score)))
        assessment_id = cursor.lastrowid

        # 2. Insert granular answers
        query_ans = """
            INSERT INTO assessment_answers (assessment_id, question_id, selected_answer, score)
            VALUES (%s, %s, %s, %s)
        """
        ans_data = [
            (assessment_id, int(ans["question_id"]), str(ans["selected_answer"]), int(ans["score"]))
            for ans in answers_breakdown
        ]
        cursor.executemany(query_ans, ans_data)

        cursor.close()
        return assessment_id
    finally:
        conn.close()


def get_user_cognitive_assessments(user_id, limit=None):
    """Fetch cognitive assessment history for a specific user."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT assessment_id, user_id, total_score, assessment_date
            FROM cognitive_assessments
            WHERE user_id = %s
            ORDER BY assessment_date DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def get_assessment_by_id(assessment_id, user_id):
    """Retrieve single assessment and its individual answers."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM cognitive_assessments
            WHERE assessment_id = %s AND user_id = %s
        """
        cursor.execute(query, (assessment_id, user_id))
        assessment = cursor.fetchone()

        if not assessment:
            cursor.close()
            return None

        # Fetch answers
        query_ans = """
            SELECT * FROM assessment_answers
            WHERE assessment_id = %s
            ORDER BY question_id ASC
        """
        cursor.execute(query_ans, (assessment_id,))
        assessment["answers"] = cursor.fetchall()
        cursor.close()
        return assessment
    finally:
        conn.close()


def get_total_cognitive_count(user_id):
    """Count total cognitive assessments completed by user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cognitive_assessments WHERE user_id = %s", (user_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    finally:
        conn.close()


def get_latest_cognitive_assessment(user_id):
    """Fetch most recent cognitive assessment for dashboard."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM cognitive_assessments
            WHERE user_id = %s
            ORDER BY assessment_date DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def get_previous_cognitive_assessment(user_id, before_assessment_id):
    """Retrieve the assessment immediately preceding the given assessment for progress comparison."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT assessment_id, total_score, assessment_date
            FROM cognitive_assessments
            WHERE user_id = %s AND assessment_id < %s
            ORDER BY assessment_id DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id, before_assessment_id))
        prev = cursor.fetchone()
        cursor.close()
        return prev
    finally:
        conn.close()


def delete_cognitive_assessment(assessment_id, user_id):
    """Delete a cognitive assessment and all associated granular answers belonging to user."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Verify ownership
        cursor.execute("SELECT * FROM cognitive_assessments WHERE assessment_id = %s AND user_id = %s", (assessment_id, user_id))
        record = cursor.fetchone()
        if not record:
            cursor.close()
            return False

        # Delete dependent answers first
        cursor.execute("DELETE FROM assessment_answers WHERE assessment_id = %s", (assessment_id,))
        # Delete parent assessment
        cursor.execute("DELETE FROM cognitive_assessments WHERE assessment_id = %s AND user_id = %s", (assessment_id, user_id))
        cursor.close()
        return True
    finally:
        conn.close()


# ==========================================
# MEDICAL PDF REPORTS
# ==========================================

def save_report(user_id, report_path):
    """Record generated PDF report file."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            INSERT INTO reports (user_id, report_path)
            VALUES (%s, %s)
        """
        cursor.execute(query, (user_id, report_path))
        report_id = cursor.lastrowid
        cursor.close()
        return report_id
    finally:
        conn.close()


def get_user_reports(user_id):
    """Fetch all reports generated for user."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT report_id, user_id, report_path, generated_at
            FROM reports
            WHERE user_id = %s
            ORDER BY generated_at DESC
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()
