#!/usr/bin/env python3
"""
0-databaseconnection.py

Class-based context manager for SQLite DB connections.
Usage:
    with DatabaseConnection("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        ...
"""

import sqlite3
import os


class DatabaseConnection:
    """Context manager that opens a sqlite3 connection and closes it on exit."""

    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        # Open and return the connection (caller can get cursor from it)
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        # Ensure the connection is closed no matter what happened
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            # In a real app you might log this
            pass
        # Returning False lets any exception propagate to the caller
        return False


def _seed_example_db(path="users.db"):
    """Create a small users table with sample data if the DB doesn't exist."""
    if os.path.exists(path):
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT)"
    )
    cur.executemany(
        "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
        [
            (1, "Alice Smith", "alice@example.com"),
            (2, "Bob Jones", "bob@example.com"),
            (3, "Crawford Cartwright", "crawford@example.com"),
        ],
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Create example DB if needed (only for quick local testing)
    _seed_example_db("users.db")

    # Use the context manager to query the users table
    with DatabaseConnection("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

    # Print results outside the 'with' to show connection closed was handled
    print("Users:")
    for row in rows:
        print(row)
