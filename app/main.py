from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from .agent import generate_outreach
from .providers import get_provider
from .schemas import OutreachOutput, OutreachRequest
from .strategies import STRATEGY_LIBRARY

app = FastAPI(
    title="Personalised Outreach Agent",
    version="0.1.0",
    description="Generates drafts only. It never sends messages.",
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personalised-outreach-agent"}

@app.get("/strategies")
def strategies() -> dict[str, list[dict[str, object]]]:
    return {
        "strategies": [
            {
                "id": item["id"],
                "name": item["name"],
                "priority": item["priority"],
            }
            for item in STRATEGY_LIBRARY.values()
        ]
    }

@app.post("/personalised-outreach", response_model=OutreachOutput)
def personalised_outreach(payload: OutreachRequest) -> OutreachOutput:
    try:
        return generate_outreach(payload, get_provider())
    except KeyError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": "STRATEGY_NOT_FOUND", "message": str(error)},
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_INPUT_OR_OUTPUT", "message": str(error)},
        ) from error
    except ValidationError as error:
        raise HTTPException(
            status_code=502,
            detail={"code": "MODEL_OUTPUT_VALIDATION_ERROR", "message": str(error)},
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail={"code": "AGENT_PROVIDER_ERROR", "message": str(error)},
        ) from error
