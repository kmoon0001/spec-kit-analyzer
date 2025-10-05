#!/usr/bin/env python3
"""Check if there are any users in the database."""

import asyncio
import sys
sys.path.insert(0, '.')

async def check_users():
    from src.database import init_db, crud
    from src.database.database import get_async_db
    
    print("Initializing database...")
    await init_db()
    
    print("Checking for users...")
    async for db_session in get_async_db():
        users = await crud.get_all_users(db_session)
        print(f"Found {len(users)} users in database:")
        for user in users:
            print(f"  - {user.username} (admin: {user.is_admin})")
        break

if __name__ == "__main__":
    asyncio.run(check_users())