#!/usr/bin/env python3
"""
0-stream_users.py

Provides:
    def stream_users() -> generator
Yields rows from the user_data table one-by-one as dicts:
    {'user_id': ..., 'name': ..., 'email': ..., 'age': ...}

Requirement: use a generator (yield) and at most one loop.
"""
from typing import Iterator, Dict, Any
import seed  # assumes seed.py is in the same package/folder


def stream_users() -> Iterator[Dict[str, Any]]:
    """
    Connect to ALX_prodev (using seed.connect_to_prodev) and stream rows
    from user_data one at a time using a single while loop and cursor.fetchone().
    """
    conn = seed.connect_to_prodev()
    if conn is None:
        return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, name, email, age FROM user_data;")
        # Single loop only
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


# If run directly, print first few rows as a quick test
if __name__ == "__main__":
    from itertools import islice
    for u in islice(stream_users(), 6):
        print(u)
