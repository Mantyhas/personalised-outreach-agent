from __future__ import annotations

import re
from typing import Any

from .schemas import (
    LeadData,
    OutreachRequest,
    RawStrategyAgentOutput,
    SelectedStrategy,
    StrategyContent,
    StrategySelection,
    StrategyTalkingPoint,
)


def parse_employee_count(value: Any) -> int:
    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        match = re.search(r"\d[\d,\s]*", value)

        if match:
            digits = re.sub(r"[^\d]", "", match.group())

            if digits:
                return int(digits)

    raise ValueError(
        "matched_on.company_size must contain an employee number."
    )


def require_text(
    matched_on: dict[str, Any],
    field_name: str,
) -> str:
    value = matched_on.get(field_name)

    if value is None or str(value).strip() == "":
        raise ValueError(
            f"matched_on.{field_name} is required."
        )

    return str(value).strip()


def parse_pain_points(value: Any) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError(
            "matched_on.pain_points must be a list."
        )

    return [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]


def flatten_talking_points(
    talking_points: list[StrategyTalkingPoint | str],
) -> list[str]:
    result: list[str] = []

    for talking_point in talking_points:
        if isinstance(talking_point, str):
            result.append(talking_point)
        else:
            result.append(
                f"{talking_point.title}: "
                f"{talking_point.description}"
            )

    return result


def normalize_outreach_request(
    payload: OutreachRequest | RawStrategyAgentOutput,
) -> OutreachRequest:
    if isinstance(payload, OutreachRequest):
        return payload

    if payload.id != payload.strategy.id:
        raise ValueError(
            "Top-level strategy ID must match strategy.id."
        )

    matched = payload.matched_on

    qualification_score = matched.get(
        "qualification_score"
    )

    if qualification_score is None:
        raise ValueError(
            "matched_on.qualification_score is required."
        )

    annual_revenue = matched.get("annual_revenue")

    return OutreachRequest(
        lead_id="unassigned",
        lead=LeadData(
            company_name=None,
            contact_first_name=None,
            contact_role=require_text(
                matched,
                "role",
            ),
            industry=require_text(
                matched,
                "industry",
            ),
            employees=parse_employee_count(
                matched.get("company_size")
            ),
            annual_revenue=(
                str(annual_revenue)
                if annual_revenue is not None
                else None
            ),
            country=require_text(
                matched,
                "country",
            ),
            erp=matched.get("erp"),
            accounting_system=matched.get(
                "accounting_system"
            ),
            company_description=None,
            pain_points=parse_pain_points(
                matched.get("pain_points")
            ),
            qualification_score=float(
                qualification_score
            ),
        ),
        strategy_selection=StrategySelection(
            selected_strategies=[
                SelectedStrategy(
                    id=payload.id,
                    score=payload.score,
                    matched_on=payload.matched_on,
                )
            ]
        ),
        strategy_content=StrategyContent(
            id=payload.strategy.id,
            name=payload.strategy.name,
            description=payload.strategy.description,
            talking_points=flatten_talking_points(
                payload.strategy.talking_points
            ),
            cta=payload.strategy.cta,
            priority=payload.strategy.priority,
        ),
    )