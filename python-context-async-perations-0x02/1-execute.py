#!/usr/bin/env python3
"""
1-execute.py

Reusable class-based context manager that:
- Opens a SQLite connection
- Executes a query with parameters
- Returns the result set on __enter__
- Ensures cleanup on __exit__
"""

import sqlite3
import os


class ExecuteQuery:
    """Context manager to execute a SQL query with given parameters."""

    def __init__(self, db_path, query, params=None):
        self.db_path = db_path
        self.query = query
        self.params = params or ()
        self.conn = None
        self.cursor = None
        self.results = None

    def __enter__(self):
        # Open connection and execute query
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.query, self.params)
        self.results = self.cursor.fetchall()
        return self.results

    def __exit__(self, exc_type, exc_value, traceback):
        # Cleanup
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        return False  # propagate any exception


def _seed_example_db(path="users.db"):
    """Create a small users table with 'age' if not exists."""
    if os.path.exists(path):
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, age INTEGER)"
    )
    cur.executemany(
        "INSERT INTO users (id, name, email, age) VALUES (?, ?, ?, ?)",
        [
            (1, "Alice Smith", "alice@example.com", 22),
            (2, "Bob Jones", "bob@example.com", 30),
            (3, "Crawford Cartwright", "crawford@example.com", 45),
        ],
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    _seed_example_db("users.db")

    query = "SELECT * FROM users WHERE age > ?"
    params = (25,)

    with ExecuteQuery("users.db", query, params) as results:
        print("Users older than 25:")
        for row in results:
            print(row)
