import requests

from backend.alerts import send_slack_alert


def sample_summary():
    return {
        "status": "CRITICAL",
        "regression_count": 3,
        "baseline_accuracy": 0.95,
        "current_accuracy": 0.80,
    }


def test_send_slack_alert_success(monkeypatch, capsys):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.com/webhook")

    class MockResponse:
        def raise_for_status(self):
            pass

    def mock_post(url, json, timeout):
        assert url == "https://example.com/webhook"
        assert timeout == 10
        assert "CRITICAL" in json["text"]
        assert "3" in json["text"]
        assert "95.0%" in json["text"]
        assert "80.0%" in json["text"]
        assert "https://report.example.com" in json["text"]

        return MockResponse()

    monkeypatch.setattr("backend.alerts.requests.post", mock_post)

    result = send_slack_alert(
        sample_summary(),
        "https://report.example.com",
    )

    assert result is True
    assert "Slack alert sent successfully." in capsys.readouterr().out


def test_missing_webhook(monkeypatch, capsys):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    result = send_slack_alert(sample_summary(), "https://report.example.com")

    assert result is False
    assert "not configured" in capsys.readouterr().out


def test_slack_http_error(monkeypatch, capsys):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.com/webhook")

    class MockResponse:
        def raise_for_status(self):
            raise requests.HTTPError("Slack returned an error")

    monkeypatch.setattr(
        "backend.alerts.requests.post",
        lambda *args, **kwargs: MockResponse(),
    )

    result = send_slack_alert(sample_summary(), "https://report.example.com")

    assert result is False
    assert "Slack alert failed" in capsys.readouterr().out


def test_slack_network_error(monkeypatch, capsys):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.com/webhook")

    def mock_post(*args, **kwargs):
        raise requests.ConnectionError("Network unavailable")

    monkeypatch.setattr("backend.alerts.requests.post", mock_post)

    result = send_slack_alert(sample_summary(), "https://report.example.com")

    assert result is False
    assert "Network unavailable" in capsys.readouterr().out
