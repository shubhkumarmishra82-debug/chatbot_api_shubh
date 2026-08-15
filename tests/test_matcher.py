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


def test_regression_stopword_does_not_cause_false_positive():
    # "i" fuzzy/exact-matching a keyword phrase containing "i" used to
    # cause "i am shubh" to match a totally unrelated "your name" reply.
    replies = [FakeReply("your name,what should i call you", "I'm a bot!")]
    assert find_custom_reply("i am shubh", replies) is None


def test_regression_single_word_overlap_does_not_hijack_phrase():
    # "shubh" alone used to fuzzy-match inside "contact shubh" and fire
    # that reply even in an unrelated sentence introducing yourself.
    replies = [FakeReply("contact,contact info,contact shubh,email", "Contact info here")]
    assert find_custom_reply("i am shubh", replies) is None
    # but the real phrase should still match:
    assert find_custom_reply("how do i contact shubh", replies) == "Contact info here"


def test_regression_contraction_does_not_fuzzy_match_stopword():
    # "whats" fuzzy-matching against the stopword "what" (89% similar)
    # used to make "what is an API" trigger a "what's up" reply.
    replies = [FakeReply("whats up,what's up,wassup", "Not much!")]
    assert find_custom_reply("what is an API", replies) is None
    assert find_custom_reply("whats up", replies) == "Not much!"


def test_regression_generic_word_does_not_hijack_long_question():
    # "please" as a lone trigger word used to match ANY message containing
    # it, hijacking a genuine long question like a distance lookup.
    replies = [FakeReply("please,pls,plz", "Sure thing, go ahead!")]
    assert find_custom_reply(
        "please tell me the exact distance of jamshedpur to warangal", replies
    ) is None
    # but a short message should still trigger it fine:
    assert find_custom_reply("please", replies) == "Sure thing, go ahead!"
    assert find_custom_reply("pls help me", replies) == "Sure thing, go ahead!"


def test_regression_multiword_phrase_does_not_collapse_to_one_word():
    # "what is gms chatbot" reducing to just the single significant word
    # "chatbot" used to match ANY message that mentions "chatbot" at all,
    # including angry complaints that have nothing to do with "what is
    # this bot".
    replies = [FakeReply("what is gms chatbot,about this bot,about you", "GMS info here")]
    assert find_custom_reply(
        "bro you are an ai and also chatbot with user helper function", replies
    ) is None
    # exact phrase should still match:
    assert find_custom_reply("what is gms chatbot", replies) == "GMS info here"
