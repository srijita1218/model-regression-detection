import os

import requests


def send_slack_alert(summary: dict, report_link: str) -> bool:
    """
    Send a ModelWatch regression alert to Slack.

    Returns True if the alert was sent successfully.
    Returns False if Slack is unavailable or not configured.

    Slack failures never interrupt the evaluation pipeline.
    """

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Slack alert skipped: SLACK_WEBHOOK_URL is not configured.")
        return False

    status = summary.get("status", "UNKNOWN")
    regression_count = summary.get("regression_count", 0)
    baseline_accuracy = summary.get("baseline_accuracy", 0)
    current_accuracy = summary.get("current_accuracy", 0)

    message = (
        f"*ModelWatch | {status}*\n\n"
        f"*Status:* {status}\n"
        f"*Category regressions:* {regression_count}\n"
        f"*Accuracy:* {baseline_accuracy * 100:.1f}% -> "
        f"{current_accuracy * 100:.1f}%\n\n"
        f"*Report:* {report_link}"
    )

    payload = {"text": message}

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

        print("Slack alert sent successfully.")
        return True

    except Exception as error:
        print(f"Slack alert failed: {error}")
        return False
