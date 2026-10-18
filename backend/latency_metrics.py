def calculate_percentile(
    values: list[float],
    percentile: float,
) -> float:

    if not values:
        return 0.0

    sorted_values = sorted(values)

    position = (
        percentile / 100
    ) * (len(sorted_values) - 1)

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(sorted_values) - 1,
    )

    fraction = position - lower_index

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    result = (
        lower_value
        + (upper_value - lower_value) * fraction
    )

    return round(result, 2)


def calculate_latency_metrics(
    latencies: list[float],
) -> dict:

    if not latencies:
        return {
            "minimum_ms": 0.0,
            "average_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "maximum_ms": 0.0,
        }

    return {
        "minimum_ms": round(
            min(latencies),
            2,
        ),
        "average_ms": round(
            sum(latencies) / len(latencies),
            2,
        ),
        "p50_ms": calculate_percentile(
            latencies,
            50,
        ),
        "p95_ms": calculate_percentile(
            latencies,
            95,
        ),
        "maximum_ms": round(
            max(latencies),
            2,
        ),
    }