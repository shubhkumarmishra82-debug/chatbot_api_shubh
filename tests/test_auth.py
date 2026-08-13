import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException
from app.auth import enforce_rate_limit


class FakeRow:
    def __init__(self):
        self.rate_limit_window_start = 0.0
        self.rate_limit_count = 0


class FakeDB:
    def commit(self):
        pass


def test_first_request_allowed():
    row = FakeRow()
    enforce_rate_limit(row, FakeDB())
    assert row.rate_limit_count == 1


def test_requests_within_limit_allowed():
    row = FakeRow()
    row.rate_limit_window_start = time.time()
    for _ in range(29):
        enforce_rate_limit(row, FakeDB())
    assert row.rate_limit_count == 29


def test_exceeding_limit_raises_429():
    row = FakeRow()
    row.rate_limit_window_start = time.time()
    row.rate_limit_count = 30  # already at the default limit
    try:
        enforce_rate_limit(row, FakeDB())
        assert False, "expected HTTPException"
    except HTTPException as e:
        assert e.status_code == 429


def test_window_resets_after_60_seconds():
    row = FakeRow()
    row.rate_limit_window_start = time.time() - 61
    row.rate_limit_count = 999  # way over limit, but window is stale
    enforce_rate_limit(row, FakeDB())  # should NOT raise -- window reset
    assert row.rate_limit_count == 1
