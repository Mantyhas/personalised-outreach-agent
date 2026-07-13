from copy import deepcopy
from typing import Any

STRATEGY_LIBRARY: dict[str, dict[str, Any]] = {
    "audit_risk": {
        "id": "audit_risk",
        "name": "Audit Risk Reduction",
        "description": (
            "Position Taxivity as a tool that proactively identifies "
            "audit issues before regulators do."
        ),
        "talking_points": [
            "Reduce audit exposure",
            "Automatically detect tax inconsistencies",
            "Increase confidence before external audits",
        ],
        "cta": "Schedule a compliance assessment",
        "priority": 90,
    }
}

def get_strategy(strategy_id: str) -> dict[str, Any]:
    strategy = STRATEGY_LIBRARY.get(strategy_id)
    if strategy is None:
        raise KeyError(f"Unknown strategy: {strategy_id}")
    return deepcopy(strategy)
