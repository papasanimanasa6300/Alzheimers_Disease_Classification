"""
Database Initialization Script for Alzheimer's Project
Creates database and all required tables using MySQL connector.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "alzheimers_project")

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def test_connection():
    """Test connecting to the MySQL server."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print(f"[OK] Connected to MySQL Server at {DB_HOST}:{DB_PORT} as '{DB_USER}'")
        conn.close()
        return True
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print(f"[ERROR] Access denied. Please check DB_USER and DB_PASSWORD in .env file.")
        else:
            print(f"[ERROR] MySQL Connection failed: {err}")
        return False


def initialize_database():
    """Execute schema.sql against MySQL server."""
    if not SCHEMA_FILE.exists():
        print(f"[ERROR] Schema file not found at: {SCHEMA_FILE}")
        return False

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql_commands = f.read()

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Split SQL commands by semicolon and execute each
        statements = [stmt.strip() for stmt in sql_commands.split(";") if stmt.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as err:
                print(f"[WARN] Statement failed: {err.msg}")

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[OK] Database '{DB_NAME}' and tables initialized successfully.")
        return True
    except mysql.connector.Error as err:
        print(f"[ERROR] Failed to initialize database: {err}")
        return False


if __name__ == "__main__":
    print(f"Connecting to MySQL ({DB_HOST}:{DB_PORT}) with user '{DB_USER}'...")
    if test_connection():
        initialize_database()
    else:
        print("[INFO] Please verify MySQL credentials in .env and ensure MySQL service is running.")
        sys.exit(1)
