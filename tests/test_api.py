from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def valid_payload() -> dict:
    return {
        "selected_strategies": [
            {
                "id": "audit_risk_reduction",
                "score": 122.0,
                "matched_on": {
                    "industry": "Construction",
                    "role": "Finance Director",
                    "company_size": "250 employees",
                    "pain_points": [
                        "audit prep",
                    ],
                    "country": "Lithuania",
                    "erp": "SAP",
                    "accounting_system": "Oracle",
                    "annual_revenue": None,
                    "qualification_score": 87,
                },
                "strategy": {
                    "id": "audit_risk_reduction",
                    "name": "Audit Risk Reduction",
                    "description": (
                        "Position Taxivity as a proactive tax "
                        "compliance platform."
                    ),
                    "talking_points": [
                        {
                            "title": "Reduce Audit Exposure",
                            "description": (
                                "Identify potential tax issues "
                                "before audit findings."
                            ),
                        }
                    ],
                    "cta": (
                        "Schedule a 30-minute "
                        "compliance assessment."
                    ),
                    "priority": 90,
                },
            }
        ]
    }


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generates_outreach(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    response = client.post(
        "/personalised-outreach",
        json=valid_payload(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "outreach_drafted"
    assert data["strategy_id"] == "audit_risk_reduction"
    assert len(data["subject_options"]) == 3
    assert len(data["follow_ups"]) == 2
    assert data["quality_checks"]["strategy_score"] == 122.0
    assert data["quality_checks"]["needs_human_review"] is True
    assert data["quality_checks"]["validation_errors"] == []


def test_rejects_unqualified_lead(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    payload = valid_payload()
    payload["selected_strategies"][0]["matched_on"][
    "qualification_score"
] = 40

    response = client.post(
        "/personalised-outreach",
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]["code"]
        == "INVALID_INPUT_OR_OUTPUT"
    )


def test_rejects_mismatched_strategy_id(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    payload = valid_payload()
    payload["selected_strategies"][0]["id"] = "different_strategy"

    response = client.post(
        "/personalised-outreach",
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]["code"]
        == "INVALID_INPUT_OR_OUTPUT"
    )