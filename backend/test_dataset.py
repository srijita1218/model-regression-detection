from backend.dataset_loader import load_dataset


cases = load_dataset("datasets/golden_dataset.json")

print("Total cases:", len(cases))

for case in cases[:3]:
    print()
    print("ID:", case.id)
    print("Email:", case.input.text)
    print("Expected category:", case.expected_category)
    print("Difficulty:", case.difficulty)