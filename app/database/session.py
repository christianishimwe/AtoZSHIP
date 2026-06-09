from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import database_settings

engine = create_async_engine(
    url=database_settings.POSTGRES_URL,
    # log sql queries, this is useful for debugging and development, but should be turned off in production
    echo=True,
)


async def get_session():
    # session has a context manager, so we can use it with a with statement
    """
    with AsyncSession(bind=engine) as session:
        yield session
    """
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
