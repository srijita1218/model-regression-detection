import pytest
from backend.summary_evaluator import tokenize, calculate_summary_score


def test_tokenize_lowercases_strips_punctuation_and_dedupes():
    assert tokenize("Payment, payment FAILED!") == {"payment", "failed"}


def test_tokenize_empty_string():
    assert tokenize("") == set()


def test_identical_summaries_score_one():
    s = "Customer reports an incorrect payment"
    assert calculate_summary_score(s, s) == 1.0


def test_no_overlap_scores_zero():
    assert calculate_summary_score("billing issue", "password reset") == 0.0


def test_case_and_punctuation_are_ignored():
    assert calculate_summary_score("Payment failed!", "payment FAILED") == 1.0


def test_repeated_words_do_not_inflate_score():
    assert calculate_summary_score("payment", "payment payment payment") == 1.0


def test_both_empty_scores_one():
    assert calculate_summary_score("", "") == 1.0


def test_one_empty_scores_zero():
    assert calculate_summary_score("something", "") == 0.0
    assert calculate_summary_score("", "something") == 0.0


def test_partial_overlap_f1():
    # 3 of 4 words shared each way: precision = recall = 0.75
    score = calculate_summary_score(
        "customer reports wrong payment",
        "customer says payment wrong",
    )
    assert score == pytest.approx(0.75)


def test_precision_and_recall_both_matter():
    # actual is a strict subset: precision 1.0, recall 0.5, F1 = 0.6667
    assert calculate_summary_score("a b c d", "a b") == pytest.approx(0.6667, abs=1e-4)


def test_score_is_symmetric():
    a, b = "refund not received", "customer never got refund"
    assert calculate_summary_score(a, b) == calculate_summary_score(b, a)