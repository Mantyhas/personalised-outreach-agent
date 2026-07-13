from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def valid_payload() -> dict:
    return {
        "lead_id": "lead_001",
        "lead": {
            "company_name": "Example GmbH",
            "contact_first_name": "Anna",
            "contact_role": "Finance Director",
            "industry": "Construction",
            "employees": 250,
            "annual_revenue": "€50M–€100M",
            "country": "Germany",
            "erp": "SAP",
            "accounting_system": "Oracle",
            "company_description": "A construction company operating across Germany.",
            "pain_points": ["manual reconciliation", "audit preparation"],
            "qualification_score": 87,
        },
        "strategy_selection": {
            "selected_strategies": [
                {
                    "id": "audit_risk",
                    "score": 92,
                    "matched_on": {
                        "industry": "Construction",
                        "role": "Finance Director",
                        "company_size": "250 employees",
                        "pain_points": [
                            "manual reconciliation",
                            "audit preparation",
                        ],
                        "country": "Germany",
                    },
                }
            ]
        },
    }

def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generates_outreach(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    response = client.post("/personalised-outreach", json=valid_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "outreach_drafted"
    assert len(data["subject_options"]) == 3
    assert len(data["follow_ups"]) == 2
    assert data["quality_checks"]["needs_human_review"] is True
    assert data["quality_checks"]["validation_errors"] == []

def test_rejects_unqualified_lead(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    payload = valid_payload()
    payload["lead"]["qualification_score"] = 40
    response = client.post("/personalised-outreach", json=payload)
    assert response.status_code == 400

def test_rejects_unknown_strategy(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    payload = valid_payload()
    payload["strategy_selection"]["selected_strategies"][0]["id"] = "missing"
    response = client.post("/personalised-outreach", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "STRATEGY_NOT_FOUND"
