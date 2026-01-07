#!/usr/bin/env python3
"""Initialize SQLite database for the notes app database container.

Creates required tables if they do not exist. This script is intentionally
migration-free: it uses simple CREATE TABLE IF NOT EXISTS statements.

The database file is expected to be located at ./myapp.db (same directory as this script),
consistent with db_connection.txt.
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_NAME = "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency


def utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string.

    We store dates as TEXT per instructions.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


print("Starting SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn_check = sqlite3.connect(DB_NAME)
        conn_check.execute("SELECT 1")
        conn_check.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Recommended in SQLite: keep foreign keys on (not strictly needed here, but safe default)
cursor.execute("PRAGMA foreign_keys = ON")

# Existing helper tables (kept for compatibility with earlier template tooling)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# Required notes schema for the app
# - Dates are TEXT (ISO-8601) per user instruction.
# - deleted_date is NULL for active notes; set to ISO-8601 timestamp to soft-delete.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_date TEXT NOT NULL,
        modified_date TEXT NOT NULL,
        deleted_date TEXT NULL
    )
"""
)

# Insert initial data for app_info (kept from previous behavior)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("project_name", "database"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("version", "0.1.0"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("author", "John Doe"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("description", ""),
)

conn.commit()

# Get database statistics
cursor.execute(
    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
)
table_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM app_info")
record_count = cursor.fetchone()[0]

# Optional: ensure there is at least one note only on brand-new DBs (we will NOT insert sample notes,
# because backend/frontend may expect empty state; also user did not request seed data).

conn.close()

# Save connection information to a file (keep consistent with existing format)
current_dir = os.getcwd()
connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

try:
    with open("db_connection.txt", "w", encoding="utf-8") as f:
        f.write("# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = os.path.abspath(DB_NAME)

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w", encoding="utf-8") as f:
        f.write(f'export SQLITE_DB="{db_path}"\n')
    print("Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database: {DB_NAME}")
print(f"Location: {current_dir}/{DB_NAME}")
print("")

print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")

print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{DB_NAME}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {current_dir}/{DB_NAME}")
print("")

print("Database statistics:")
print(f"  Tables: {table_count}")
print(f"  App info records: {record_count}")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess

    result = subprocess.run(["which", "sqlite3"], capture_output=True, text=True)
    if result.returncode == 0:
        print("")
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {DB_NAME}")
except Exception:
    pass

# Exit successfully
print("\nScript completed successfully.")
