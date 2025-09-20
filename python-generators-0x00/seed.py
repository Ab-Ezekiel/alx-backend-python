#!/usr/bin/env python3
"""
seed.py

Provides:
- connect_db()
- create_database(connection)
- connect_to_prodev()
- create_table(connection)
- insert_data(connection, data)
- stream_user_rows(connection)  -> generator that yields rows one by one
"""

import os
import csv
import uuid
from decimal import Decimal
from typing import Optional, Dict, Iterator, Any

import mysql.connector
from mysql.connector import Error


def _db_config():
    """Read DB connection settings from environment with sensible defaults."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),  # set DB_PASSWORD env if needed
        "port": int(os.getenv("DB_PORT", 3306)),
        "autocommit": False,
    }


def connect_db() -> Optional[mysql.connector.connection_cext.CMySQLConnection]:
    """
    Connect to the MySQL server (not a specific database).
    Returns a connection or None on failure.
    """
    cfg = _db_config()
    try:
        conn = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"],
            autocommit=cfg["autocommit"],
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL server: {e}")
        return None


def create_database(connection: mysql.connector.connection_cext.CMySQLConnection) -> None:
    """Create database ALX_prodev if it does not exist."""
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev;")
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"Error creating database: {e}")
        raise


def connect_to_prodev() -> Optional[mysql.connector.connection_cext.CMySQLConnection]:
    """Return a connection to the ALX_prodev database."""
    cfg = _db_config()
    try:
        conn = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"],
            database="ALX_prodev",
            autocommit=cfg["autocommit"],
        )
        return conn
    except Error as e:
        print(f"Error connecting to ALX_prodev: {e}")
        return None


def create_table(connection: mysql.connector.connection_cext.CMySQLConnection) -> None:
    """
    Create user_data table if it does not exist.
    Columns: user_id CHAR(36) PRIMARY KEY, name VARCHAR NOT NULL,
             email VARCHAR NOT NULL, age DECIMAL NOT NULL
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS user_data (
      user_id CHAR(36) NOT NULL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      email VARCHAR(255) NOT NULL,
      age DECIMAL(5,2) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        cursor = connection.cursor()
        cursor.execute(ddl)
        connection.commit()
        cursor.close()
        print("Table user_data created successfully")
    except Error as e:
        print(f"Error creating table: {e}")
        raise


def _parse_age(value: str) -> Decimal:
    """Safely parse age value from CSV into Decimal (fallback to 0)."""
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(value)
    except Exception:
        # try float fallback
        try:
            return Decimal(str(float(value)))
        except Exception:
            return Decimal("0")


def insert_data(connection: mysql.connector.connection_cext.CMySQLConnection, data: str) -> None:
    """
    Insert rows from CSV file `data` into user_data if they don't exist.
    `data` is a path to CSV file. CSV must contain at least columns:
      - user_id (optional)
      - name
      - email
      - age
    """
    if not os.path.exists(data):
        raise FileNotFoundError(f"CSV file not found: {data}")

    insert_sql = """
      INSERT INTO user_data (user_id, name, email, age)
      VALUES (%s, %s, %s, %s)
    """

    select_sql = "SELECT 1 FROM user_data WHERE user_id = %s LIMIT 1"

    try:
        cursor = connection.cursor()
        with open(data, newline="", encoding="utf-8") as csf:
            reader = csv.DictReader(csf)
            batch = []
            count = 0
            for row in reader:
                uid = row.get("user_id") or row.get("id") or ""
                if not uid:
                    uid = str(uuid.uuid4())
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip()
                age = _parse_age(row.get("age") or row.get("Age") or "")

                # check existence
                cursor.execute(select_sql, (uid,))
                exists = cursor.fetchone()
                if exists:
                    continue

                batch.append((uid, name, email, age))

                # commit in small batches
                if len(batch) >= 500:
                    cursor.executemany(insert_sql, batch)
                    connection.commit()
                    count += len(batch)
                    batch = []

            # final flush
            if batch:
                cursor.executemany(insert_sql, batch)
                connection.commit()
                count += len(batch)

        cursor.close()
        print(f"Inserted {count} new rows into user_data (skipped existing).")
    except Error as e:
        print(f"Error inserting data: {e}")
        connection.rollback()
        raise


def stream_user_rows(connection: mysql.connector.connection_cext.CMySQLConnection, fetch_size: int = 500
                     ) -> Iterator[Dict[str, Any]]:
    """
    Generator that streams rows from user_data table in batches and yields one row at a time.
    Usage:
        for row in stream_user_rows(conn):
            process(row)
    """
    query = "SELECT user_id, name, email, age FROM user_data"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    try:
        while True:
            rows = cursor.fetchmany(size=fetch_size)
            if not rows:
                break
            for r in rows:
                yield r
    finally:
        cursor.close()


# If the module is run directly, provide a tiny demo when credentials are available
if __name__ == "__main__":
    conn = connect_db()
    if not conn:
        raise SystemExit("Cannot connect to MySQL server. Set DB_HOST/DB_USER/DB_PASSWORD if needed.")
    create_database(conn)
    conn.close()

    conn = connect_to_prodev()
    if not conn:
        raise SystemExit("Cannot connect to ALX_prodev database.")
    create_table(conn)

    # Example: try to find user_data.csv in current folder
    csv_path = os.getenv("USER_DATA_CSV", "user_data.csv")
    if os.path.exists(csv_path):
        insert_data(conn, csv_path)
    else:
        print(f"No CSV found at {csv_path}; skipping insert demo.")

    # demo generator (print first 3 rows)
    it = stream_user_rows(conn, fetch_size=100)
    for i, row in enumerate(it):
        print(row)
        if i >= 2:
            break
    conn.close()
