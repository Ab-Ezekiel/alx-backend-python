#!/usr/bin/env python3
"""
1-batch_processing.py

Implements:
    - stream_users_in_batches(batch_size)
    - batch_processing(batch_size)

Requirements:
- Fetch rows in batches from the user_data table
- Process/filter users older than 25
- Use yield (generators)
- No more than 3 loops
"""

from typing import List, Dict, Any, Iterator
import seed  # reuse database connection from seed.py


def stream_users_in_batches(batch_size: int) -> Iterator[List[Dict[str, Any]]]:
    """
    Generator: fetches rows from user_data in batches of given size.
    Yields a list of dict rows per batch.
    """
    conn = seed.connect_to_prodev()
    if conn is None:
        return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, name, email, age FROM user_data;")
        while True:  # loop 1
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield rows
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def batch_processing(batch_size: int) -> Iterator[Dict[str, Any]]:
    """
    Generator: processes batches of users and yields only those over age 25.
    """
    for batch in stream_users_in_batches(batch_size):  # loop 2
        for user in batch:  # loop 3
            if user["age"] > 25:
                yield user


# Quick test if run directly
if __name__ == "__main__":
    import sys
    from itertools import islice

    try:
        for u in islice(batch_processing(50), 5):
            print(u, "\n")
    except BrokenPipeError:
        sys.stderr.close()
