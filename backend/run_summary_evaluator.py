from backend.summary_evaluator import calculate_summary_score


expected = (
    "Customer reports being charged twice "
    "for their subscription."
)

actual = (
    "Customer was charged twice "
    "for their subscription."
)


score = calculate_summary_score(
    expected,
    actual,
)


print("Expected:", expected)
print("Actual:", actual)
print("Summary score:", score)