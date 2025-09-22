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
            return func(conn, *args, **kwargs)
        finally:
            try:
                conn.close()
            except Exception:
                pass
    return wrapper


def transactional(func):
    """
    Decorator that wraps DB operations inside a transaction.
    Commits on success, rollbacks on error.
    """
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
    return wrapper


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))


# Example usage
if __name__ == "__main__":
    update_user_email(user_id=1, new_email="Crawford_Cartwright@hotmail.com")
    print("Email updated successfully!")
