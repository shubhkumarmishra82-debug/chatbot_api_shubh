"""
Database setup using SQLAlchemy + Postgres (works with Vercel Postgres,
Supabase, Neon, or any standard Postgres connection string).

Vercel Postgres automatically injects a POSTGRES_URL env var once you
attach the integration in your project's Storage tab — nothing else to do.
"""
import os
import ssl
from datetime import datetime
import uuid
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")

# Vercel/Neon give a `postgres://` or `postgresql://` URL, often with a
# `?sslmode=require` query param. We use the pg8000 driver (pure Python,
# no C build step -- more reliable on serverless), so the SQLAlchemy
# dialect must be `postgresql+pg8000://`. pg8000 doesn't understand the
# libpq-style `sslmode` query param the way psycopg2 does -- passing it
# through crashes the connection at startup. So we strip any query string
# and instead enable SSL explicitly via connect_args below.
engine = None
SessionLocal = None

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

    parts = urlsplit(DATABASE_URL)
    clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    # Match the semantics of the `sslmode=require` the URL originally
    # asked for: connection is encrypted, but we don't demand full
    # certificate-chain verification -- Vercel's Python runtime can't
    # always verify Neon/Vercel Postgres's chain, and full "verify-full"
    # was never what was requested in the first place.
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    try:
        engine = create_engine(
            clean_url,
            connect_args={"ssl_context": ssl_context},
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=2,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception:
        # Don't let a bad connection string crash the whole app at import
        # time -- engine stays None, get_db() below raises a clean error
        # only when a route actually tries to use the database.
        engine = None
        SessionLocal = None

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


class Document(Base):
    """
    Your own documents/notes -- the bot's private knowledge base. Split
    into chunks so relevant pieces can be pulled in as context when
    answering a question, without needing any external search or vendor.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    content = Column(Text)
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
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Don't crash the whole app if the DB is unreachable at cold
        # start (wrong creds, network hiccup, etc). Routes that need the
        # DB will surface a clean error when actually called instead.
        pass


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
