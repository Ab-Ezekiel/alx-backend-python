#!/usr/bin/python3
"""
4-stream_ages.py

Stream user ages from the database using a generator
and compute the average age without loading all rows
into memory.
"""

import seed


def stream_user_ages():
    """
    Generator that yields user ages one by one from user_data table.
    """
    connection = seed.connect_to_prodev()
    if connection is None:
        return  # no DB connection

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT age FROM user_data")

    for row in cursor:  # loop 1
        yield int(row["age"])

    cursor.close()
    connection.close()


def average_age():
    """
    Consume the generator to compute average age.
    """
    total, count = 0, 0
    for age in stream_user_ages():  # loop 2
        total += age
        count += 1
    return (total / count) if count else 0


if __name__ == "__main__":
    avg = average_age()
    print(f"Average age of users: {avg:.2f}")

