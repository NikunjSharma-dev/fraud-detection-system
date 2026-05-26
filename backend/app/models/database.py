"""
Async PostgreSQL database setup using SQLAlchemy 2.0 + asyncpg.
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://frauduser:fraudpass@localhost:5432/frauddb"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────────────────────
# ORM MODELS
# ──────────────────────────────────────────────────────────────

class TransactionORM(Base):
    __tablename__ = "transactions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id    = Column(String(20), nullable=False)
    amount        = Column(Float, nullable=False)
    status        = Column(String(30), default="Pending")
    is_fraudulent = Column(Boolean, default=False)
    risk_score    = Column(Float, default=0.0)
    latitude      = Column(Float)
    longitude     = Column(Float)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


class AuditLogORM(Base):
    __tablename__ = "audit_log"

    id             = Column(String, primary_key=True)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    event_type     = Column(String(50), nullable=False)
    old_status     = Column(String(30))
    new_status     = Column(String(30))
    notes          = Column(Text)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────────────────────
# DEPENDENCY — yields a DB session per request
# ──────────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Called at startup to verify connection."""
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    print("✅ Database connection established.")