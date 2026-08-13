import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.migrations import split_statements, MIGRATIONS


def test_split_statements_basic():
    sql = "CREATE TABLE a (x INT); CREATE TABLE b (y INT);"
    result = split_statements(sql)
    assert result == ["CREATE TABLE a (x INT)", "CREATE TABLE b (y INT)"]


def test_split_statements_ignores_empty_parts():
    sql = "SELECT 1;;   ;SELECT 2;"
    result = split_statements(sql)
    assert result == ["SELECT 1", "SELECT 2"]


def test_split_statements_single_statement_no_trailing_semicolon():
    assert split_statements("SELECT 1") == ["SELECT 1"]


def test_migration_versions_are_unique():
    versions = [v for v, _ in MIGRATIONS]
    assert len(versions) == len(set(versions))


def test_migrations_list_not_empty():
    assert len(MIGRATIONS) > 0


def test_every_migration_has_nonempty_sql():
    for version, sql in MIGRATIONS:
        assert isinstance(version, str) and version
        assert isinstance(sql, str) and sql.strip()
