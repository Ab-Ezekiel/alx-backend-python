#!/usr/bin/env python3
"""
Task 0: Logging Database Queries
"""

import sqlite3
import functools


def log_queries(func):
    """Decorator to log SQL queries executed by a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get("query") or (args[0] if args else None)
        if query:
            print(f"[LOG] Executing SQL query: {query}")
        else:
            print("[LOG] No SQL query provided.")
        return func(*args, **kwargs)
    return wrapper


@log_queries
def fetch_all_users(query):
    """Fetch all users from database given a query."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    # Example usage
    users = fetch_all_users(query="SELECT * FROM users;")
    print(users)
