import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.matcher import find_custom_reply


class FakeReply:
    def __init__(self, trigger, response):
        self.trigger = trigger
        self.response = response


REPLIES = [
    FakeReply("hi,hello,hey", "Hey there!"),
    FakeReply("who made you,who created you", "Shubh made me!"),
    FakeReply("bye,goodbye", "See you later!"),
]


def test_exact_match():
    assert find_custom_reply("hi there", REPLIES) == "Hey there!"


def test_word_boundary_prevents_false_positive():
    assert find_custom_reply("this is a test", REPLIES) is None
    assert find_custom_reply("history lesson", REPLIES) is None


def test_multi_word_phrase_match():
    assert find_custom_reply("who made you anyway?", REPLIES) == "Shubh made me!"


def test_no_match_returns_none():
    assert find_custom_reply("completely unrelated text", REPLIES) is None


def test_fuzzy_typo_tolerance():
    assert find_custom_reply("helo", REPLIES) == "Hey there!"


def test_empty_message_returns_none():
    assert find_custom_reply("", REPLIES) is None


def test_longest_keyword_wins_when_multiple_match():
    replies = [
        FakeReply("hi", "short match"),
        FakeReply("hi there friend", "long match"),
    ]
    assert find_custom_reply("hi there friend", replies) == "long match"
