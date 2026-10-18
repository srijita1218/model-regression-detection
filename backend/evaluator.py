import time

from backend.classifier import classify
from backend.dataset_loader import load_dataset
from backend.summary_evaluator import calculate_summary_score
from backend.latency_metrics import calculate_latency_metrics
from backend.token_metrics import extract_token_metrics

def evaluate_dataset(
    dataset_path: str,
    prompt_path: str,
) -> dict:

    cases,_ = load_dataset(dataset_path) 

    results = []
    correct_categories = 0
    total_latency = 0.0
    total_summary_score = 0.0
    latencies = []
    prompt_tokens = []
    generated_tokens = []
    total_tokens = []

    for case in cases:
        print(f"Running {case.id}...")

        start_time = time.perf_counter() #start timer to check how long ollama is taking

        try:
            actual, llm_response = classify(
                case.input.text,
                prompt_path,
            )

            token_metrics = extract_token_metrics(
                llm_response
            )

            prompt_tokens.append(
                token_metrics["prompt_tokens"]
            )

            generated_tokens.append(
                token_metrics["generated_tokens"]
            )

            total_tokens.append(
                token_metrics["total_tokens"]
            )

            latency = (time.perf_counter() - start_time) * 1000 #gives latency in milliseconds

            latencies.append(latency)

            #comparing categories
            category_correct = (
                actual.category.lower().strip()
                == case.expected_category.lower().strip()
            )

            summary_score = calculate_summary_score(
                case.expected_summary,
                actual.summary,
            )

            total_summary_score += summary_score

            if category_correct:
                correct_categories += 1

            total_latency += latency

            results.append(
                {
                    "id": case.id,
                    "expected_category": case.expected_category,
                    "actual_category": actual.category,
                    "expected_summary": case.expected_summary,
                    "actual_summary": actual.summary,
                    "category_correct": category_correct,
                    "summary_score": summary_score,
                    "latency_ms": round(latency, 2),
                    "prompt_tokens": token_metrics["prompt_tokens"],
                    "generated_tokens": token_metrics["generated_tokens"],
                    "total_tokens": token_metrics["total_tokens"],
                    "error": None,
                }
            )

            print(
                f"  Expected: {case.expected_category}"
            )
            print(
                f"  Actual:   {actual.category}"
            )
            print(
                f"  Correct:  {category_correct}"
            )
            print(
                f"  Summary:  {summary_score:.4f}"
            )
            print(
                f"  Latency:  {latency:.2f} ms"
            )

        except Exception as error:
            latency = (time.perf_counter() - start_time) * 1000

            latencies.append(latency) #even if an llm request fails- it still consumed time

            total_latency += latency

            results.append(
                {
                    "id": case.id,
                    "expected_category": case.expected_category,
                    "actual_category": None,
                    "expected_summary": case.expected_summary,
                    "actual_summary": None,
                    "category_correct": False,
                    "summary_score": 0.0,
                    "latency_ms": round(latency, 2),
                    "error": str(error),
                }
            )

            print(f"  ERROR: {error}")

    total_cases = len(cases)

    category_accuracy = (
        correct_categories / total_cases
        if total_cases > 0
        else 0
    )

    latency_metrics = calculate_latency_metrics(
        latencies
    )

    average_summary_score = (
        total_summary_score / total_cases
        if total_cases > 0
        else 0
    )

    token_metrics_summary = {
        "total_prompt_tokens": sum(prompt_tokens),
        "total_generated_tokens": sum(generated_tokens),
        "total_tokens": sum(total_tokens),
        "average_prompt_tokens": round(
            sum(prompt_tokens) / len(prompt_tokens),
            2,
        ) if prompt_tokens else 0.0,
        "average_generated_tokens": round(
            sum(generated_tokens) / len(generated_tokens),
            2,
        ) if generated_tokens else 0.0,
        "average_total_tokens": round(
            sum(total_tokens) / len(total_tokens),
            2,
        ) if total_tokens else 0.0,
    }

    return {
        "total_cases": total_cases,
        "correct_categories": correct_categories,
        "category_accuracy": round(category_accuracy, 4),
        "average_summary_score": round(
            average_summary_score,
            4,
        ),
        "latency": latency_metrics,
        "tokens": token_metrics_summary,
        "results": results,
    }

   

