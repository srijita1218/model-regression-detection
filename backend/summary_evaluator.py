import re


def tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return set(words) #using a set so repeated words arent counted multiple times.


def calculate_summary_score(
    expected: str,
    actual: str,
) -> float:

    expected_words = tokenize(expected) #turns the sentence to words
    actual_words = tokenize(actual)

    if not expected_words and not actual_words:
        return 1.0

    if not expected_words or not actual_words:
        return 0.0

    common_words = expected_words.intersection(actual_words)

    precision = len(common_words) / len(actual_words)

    recall = len(common_words) / len(expected_words)

    if precision + recall == 0:
        return 0.0

    f1 = (
        2 * precision * recall
        / (precision + recall)
    )

    return round(f1, 4)