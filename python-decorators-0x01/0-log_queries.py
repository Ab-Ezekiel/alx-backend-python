#!/usr/bin/env python3
"""
Task 0: Logging Database Queries
"""

import sqlite3
import functools
from datetime import datetime   # required for logging timestamp


def log_queries(func):
    """Decorator to log SQL queries with timestamp before execution"""
    @functools.wraps(func)
    def wrapper(query, *args, **kwargs):
        print(f"[{datetime.now()}] Executing query: {query}")
        return func(query, *args, **kwargs)
    return wrapper


@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


# fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")
