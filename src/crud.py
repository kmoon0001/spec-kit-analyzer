from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from . import models
import datetime
from typing import List, Dict, Optional

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()

async def change_user_password(db: AsyncSession, user: models.User, new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user