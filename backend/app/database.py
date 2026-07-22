"""
Database configuration and session management.

This module sets up the SQLAlchemy async engine, session factory, and declarative base.
It provides database session dependencies for FastAPI dependency injection.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings

# Create declarative base for SQLAlchemy models
Base = declarative_base()


def create_engine() -> AsyncEngine:
    """
    Create and configure the async database engine.
    
    Configures connection pooling with the following settings:
    - pool_size: 20 base connections
    - max_overflow: 40 additional connections when pool is exhausted
    - pool_recycle: 3600 seconds (1 hour) - recycle connections to prevent stale connections
    - pool_timeout: 30 seconds - timeout waiting for connection from pool
    - pool_pre_ping: True - verify connections before using them
    - echo: Based on DEBUG setting - log all SQL statements
    
    Returns:
        AsyncEngine: Configured async database engine
    """
    settings = get_settings()
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_recycle=3600,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=settings.DEBUG,  # Echo SQL in debug mode
        future=True,  # Use SQLAlchemy 2.0 behavior
    )
    
    return engine


# Create global engine instance
engine = create_engine()

# Create async session factory
# expire_on_commit=False prevents lazy loading issues after commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI.
    
    Provides an async database session that is automatically closed
    after the request completes. Should be used with FastAPI's
    dependency injection system.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
    
    Yields:
        AsyncSession: Database session for the request
        
    Note:
        The session is automatically closed in the finally block,
        ensuring proper cleanup even if an exception occurs.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This function should only be used in development/testing.
    In production, use Alembic migrations instead.
    
    Note:
        This will not drop existing tables, only create missing ones.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close the database engine and cleanup connections.
    
    Should be called during application shutdown to properly
    close all database connections and release resources.
    """
    await engine.dispose()
