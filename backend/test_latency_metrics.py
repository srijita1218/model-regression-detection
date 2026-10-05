#just to test the latency metrics.

from backend.latency_metrics import calculate_latency_metrics


latencies = [
    100,
    200,
    300,
    400,
    500,
]


metrics = calculate_latency_metrics(
    latencies
)


print(metrics)