#!/usr/bin/env python3
"""
Task 2: Concurrent Asynchronous Database Queries
Objective: Run multiple database queries concurrently using asyncio.gather.
"""

import asyncio
import aiosqlite


async def async_fetch_users(db_name="users.db"):
    """Fetch all users asynchronously"""
    async with aiosqlite.connect(db_name) as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()


async def async_fetch_older_users(db_name="users.db"):
    """Fetch users older than 40 asynchronously"""
    async with aiosqlite.connect(db_name) as db:
        async with db.execute("SELECT * FROM users WHERE age > 40") as cursor:
            return await cursor.fetchall()


async def fetch_concurrently():
    """Run both queries concurrently and print results"""
    users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users(),
    )

    print("\nAll Users:")
    for row in users:
        print(row)

    print("\nUsers older than 40:")
    for row in older_users:
        print(row)


if __name__ == "__main__":
    asyncio.run(fetch_concurrently())
