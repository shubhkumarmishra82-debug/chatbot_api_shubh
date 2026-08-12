import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tools import try_calculate


def test_basic_addition():
    assert try_calculate("2 + 2") == "2 + 2 = 4"


def test_basic_subtraction():
    assert try_calculate("10 - 3") == "10 - 3 = 7"


def test_multiplication():
    assert try_calculate("6 * 7") == "6 * 7 = 42"


def test_division():
    assert try_calculate("10 / 4") == "10 / 4 = 2.5"


def test_integer_result_not_float():
    assert try_calculate("4 / 2") == "4 / 2 = 2"


def test_order_of_operations():
    assert try_calculate("2 + 3 * 4") == "2 + 3 * 4 = 14"


def test_parentheses():
    assert try_calculate("(2 + 3) * 4") == "(2 + 3) * 4 = 20"


def test_negative_numbers():
    assert try_calculate("-5 + 10") == "-5 + 10 = 5"


def test_non_math_text_returns_none():
    assert try_calculate("hello there") is None


def test_empty_string_returns_none():
    assert try_calculate("") is None
    assert try_calculate("   ") is None


def test_no_digits_returns_none():
    assert try_calculate("+ - * /") is None


def test_rejects_code_injection_attempt():
    # must never execute arbitrary code -- the safe pattern rejects
    # anything with letters/underscores before it even gets to ast.parse
    assert try_calculate("__import__('os').system('echo hi')") is None


def test_division_by_zero_handled_gracefully():
    assert try_calculate("5 / 0") is None


def test_mixed_text_and_numbers_returns_none():
    assert try_calculate("what is 2 + 2") is None  # letters present -> not pure math
