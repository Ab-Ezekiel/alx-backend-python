#!/usr/bin/python3
seed = __import__('seed')


def paginate_users(page_size, offset):
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
    rows = cursor.fetchall()
    connection.close()
    return rows


def lazy_pagination(page_size):
    """
    Generator that lazily fetches paginated users.
    Uses one loop and yields each page until no more rows.
    """
    offset = 0
    while True:  # one loop
        page = paginate_users(page_size, offset)
        if not page:   # when no more rows
            break
        yield page
        offset += page_size
