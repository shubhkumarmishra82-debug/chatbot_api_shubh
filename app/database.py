"""
Database setup using SQLAlchemy + Postgres (works with Vercel Postgres,
Supabase, Neon, or any standard Postgres connection string).

Vercel Postgres automatically injects a POSTGRES_URL env var once you
attach the integration in your project's Storage tab — nothing else to do.
"""
import os
from datetime import datetime
import uuid

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")

# Vercel/Neon give a `postgres://` or `postgresql://` URL. We use the
# pg8000 driver (pure Python, no C build step -- more reliable on
# serverless) so the SQLAlchemy dialect must be `postgresql+pg8000://`.
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# IMPORTANT: don't raise/crash here at import time -- that takes down the
# whole serverless function, even for routes that don't need the DB
# (like /health). Instead, the engine is None until a real DB URL is set,
# and get_db() below raises a clean, catchable error only when a route
# actually tries to use the database.
engine = (
    create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=3, max_overflow=2)
    if DATABASE_URL
    else None
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class CustomReply(Base):
    """
    Your own canned replies. `trigger` is a comma-separated list of
    keywords/phrases (case-insensitive substring match against the user's
    message). If any keyword matches, `response` is returned as-is --
    entirely your own content, nothing fetched or rewritten.
    e.g. trigger="hi,hello,hey" -> response="Hi! I'm GMS Chatbot 👋"
    """
    __tablename__ = "custom_replies"

    id = Column(String, primary_key=True, default=generate_uuid)
    trigger = Column(Text)     # comma-separated keywords
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiKey(Base):
    """
    Self-serve API keys. Anyone visiting /api can generate one. Not
    currently required to call /chat (so existing usage keeps working) --
    hook up a dependency check on /chat if you want to start enforcing it.
    """
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryNote(Base):
    """
    'Trainer' notes — persistent facts or instructions you feed the bot
    (e.g. "Always answer in Hindi + English", "The user's name is Shubh",
    "Prefer short answers"). Injected into every conversation's system
    prompt, global by default.
    """
    __tablename__ = "memory_notes"

    id = Column(String, primary_key=True, default=generate_uuid)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    if engine is None:
        return  # no DB configured yet -- skip silently, don't crash startup
    Base.metadata.create_all(bind=engine)


def get_db():
    if SessionLocal is None:
        raise RuntimeError(
            "No database is configured yet. In Vercel: Storage tab -> "
            "Create Database -> Postgres, then redeploy. This sets "
            "POSTGRES_URL automatically."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
