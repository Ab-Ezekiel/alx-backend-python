#!/usr/bin/python3
import time
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


def retry_on_failure(retries=3, delay=2):
    """
    Decorator factory that retries a function if it raises an exception.
    :param retries: number of attempts before giving up
    :param delay: seconds to wait between retries
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries:
                        time.sleep(delay)
                    else:
                        raise last_exception
        return wrapper
    return decorator


@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


if __name__ == "__main__":
    users = fetch_users_with_retry()
    print(users)
