"""
Lightweight versioned database migrations. Deliberately not using
Alembic -- that needs its own config/CLI/versions-folder tooling that
doesn't fit well into a serverless deploy where there's no persistent
place to "run a command" outside of app startup. Instead: a plain list
of (version, sql) pairs, tracked in a schema_migrations table, applied
once each, safe to re-run on every cold start.

Why this matters concretely: Base.metadata.create_all() only creates
tables that don't exist yet -- it does NOT add new columns to a table
that's already there. When rate-limit/usage columns were added to
ApiKey after the table already existed in production, create_all()
alone would silently never add them, and every request would then fail
with "column does not exist". This file fixes that for good.
"""
import logging

log = logging.getLogger("gms.migrations")

MIGRATIONS = [
    (
        "0001_schema_migrations_table",
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version VARCHAR PRIMARY KEY, applied_at TIMESTAMP DEFAULT now())",
    ),
    (
        "0002_api_key_usage_columns",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rate_limit_window_start FLOAT DEFAULT 0;"
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rate_limit_count INTEGER DEFAULT 0;"
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS total_requests INTEGER DEFAULT 0;"
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;",
    ),
]


def split_statements(sql: str) -> list:
    """Splits a semicolon-separated block of SQL into individual
    non-empty statements. Extracted as a pure function so it's testable
    without a real database connection."""
    return [s.strip() for s in sql.split(";") if s.strip()]


def run_migrations(engine):
    if engine is None:
        return
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text(MIGRATIONS[0][1]))  # ensure the tracking table exists first

        applied = {row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))}

        for version, sql in MIGRATIONS:
            if version in applied:
                continue
            for statement in split_statements(sql):
                conn.execute(text(statement))
            conn.execute(
                text(
                    "INSERT INTO schema_migrations (version) VALUES (:v) "
                    "ON CONFLICT (version) DO NOTHING"
                ),
                {"v": version},
            )
            log.info("Applied migration %s", version)
