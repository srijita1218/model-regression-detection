from backend.classifier import classify


result, llm_response = classify(
    "I was charged twice for my subscription this month.",
    "prompts/v1.yaml",
)


print("Category:", result.category)
print("Summary:", result.summary)