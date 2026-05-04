"""
Database configuration and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async():
    """Async database session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.models import (
        user, learner, teacher, parent, school, content,
        progress, bridge, community, analytics
    )
    Base.metadata.create_all(bind=engine)


# Event listeners for updated_at
@event.listens_for(Base, 'before_update', propagate=True)
def update_updated_at(mapper, connection, target):
    """Auto-update updated_at timestamp."""
    if hasattr(target, 'updated_at'):
        from datetime import datetime
        target.updated_at = datetime.utcnow()
