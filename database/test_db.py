#!/usr/bin/env python3
"""Verify SQLite notes table basics (CRUD + soft-delete).

This script performs a minimal end-to-end check against the local SQLite database:
- Ensures the `notes` table exists
- Inserts a note
- Selects it back
- Updates it (and modified_date)
- Soft-deletes it by setting deleted_date

Database path usage is consistent with db_connection.txt: it uses ./myapp.db by default.
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone

DB_NAME = "myapp.db"


def utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string (stored as TEXT)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str) -> None:
    """Print a failure message and exit non-zero."""
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    """Print a success message."""
    print(f"OK: {message}")


def main() -> None:
    """Run CRUD verification for the notes schema."""
    if not os.path.exists(DB_NAME):
        fail(f"Database file '{DB_NAME}' not found. Run init_db.py first.")

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        # Verify sqlite is alive
        cursor.execute("SELECT sqlite_version() AS v")
        version = cursor.fetchone()["v"]
        ok(f"SQLite version: {version}")

        # Verify notes table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
        )
        if cursor.fetchone() is None:
            fail("Table 'notes' not found. Run init_db.py to create schema.")
        ok("Table 'notes' exists")

        # Use a transaction so we don't leave test rows around if anything fails mid-way.
        # We'll still commit on success so the test can be inspected, but we clean up at end.
        cursor.execute("BEGIN")

        created = utc_now_iso()
        modified = created

        # INSERT
        cursor.execute(
            """
            INSERT INTO notes (title, content, created_date, modified_date, deleted_date)
            VALUES (?, ?, ?, ?, NULL)
            """,
            ("Test note", "This is a test note content.", created, modified),
        )
        note_id = cursor.lastrowid
        if not note_id:
            fail("Insert did not produce a note id")
        ok(f"Inserted note id={note_id}")

        # SELECT
        cursor.execute(
            """
            SELECT id, title, content, created_date, modified_date, deleted_date
            FROM notes
            WHERE id = ?
            """,
            (note_id,),
        )
        row = cursor.fetchone()
        if row is None:
            fail("Inserted note could not be selected back")
        if row["deleted_date"] is not None:
            fail("Newly inserted note unexpectedly has deleted_date set")
        ok("Selected inserted note successfully")

        # UPDATE
        new_modified = utc_now_iso()
        cursor.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, modified_date = ?
            WHERE id = ?
            """,
            ("Updated title", "Updated content", new_modified, note_id),
        )
        if cursor.rowcount != 1:
            fail(f"Update affected {cursor.rowcount} rows (expected 1)")
        ok("Updated note successfully")

        cursor.execute(
            "SELECT title, content, modified_date FROM notes WHERE id = ?", (note_id,)
        )
        updated = cursor.fetchone()
        if updated is None:
            fail("Updated note could not be re-selected")
        if updated["title"] != "Updated title" or updated["content"] != "Updated content":
            fail("Updated note fields do not match expected values")
        if updated["modified_date"] != new_modified:
            fail("modified_date did not update as expected")
        ok("Verified updated values successfully")

        # SOFT-DELETE (set deleted_date)
        deleted = utc_now_iso()
        cursor.execute(
            """
            UPDATE notes
            SET deleted_date = ?, modified_date = ?
            WHERE id = ?
            """,
            (deleted, deleted, note_id),
        )
        if cursor.rowcount != 1:
            fail(f"Soft-delete affected {cursor.rowcount} rows (expected 1)")
        ok("Soft-deleted note successfully")

        cursor.execute(
            "SELECT deleted_date FROM notes WHERE id = ?",
            (note_id,),
        )
        deleted_row = cursor.fetchone()
        if deleted_row is None or deleted_row["deleted_date"] != deleted:
            fail("deleted_date was not set correctly during soft-delete")
        ok("Verified deleted_date set correctly")

        # Optional: verify active filtering semantics the backend will likely use
        cursor.execute(
            """
            SELECT COUNT(*) AS c
            FROM notes
            WHERE id = ? AND deleted_date IS NULL
            """,
            (note_id,),
        )
        active_count = cursor.fetchone()["c"]
        if active_count != 0:
            fail("Soft-deleted note still appears as active (deleted_date IS NULL)")
        ok("Verified soft-deleted note is not active")

        # Cleanup: remove the test note to keep DB clean for app usage
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        ok("Cleaned up test note row")

        conn.commit()
        ok("All notes CRUD checks passed")
    except sqlite3.Error as e:
        fail(f"SQLite error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
