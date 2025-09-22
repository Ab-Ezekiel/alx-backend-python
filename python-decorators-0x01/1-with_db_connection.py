#!/usr/bin/python3
import sqlite3
import functools

def with_db_connection(func):
    """
    Decorator that opens a SQLite connection to 'users.db',
    injects it as the first argument to the wrapped function,
    and ensures the connection is closed after the function returns.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect("users.db")
        try:
            # Call wrapped function with conn injected as first argument
            return func(conn, *args, **kwargs)
        finally:
            # Ensure the connection is always closed
            try:
                conn.close()
            except Exception:
                # swallow close errors (optional: log in real code)
                pass
    return wrapper


@with_db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


# Example usage
if __name__ == "__main__":
    user = get_user_by_id(user_id=1)
    print(user)
