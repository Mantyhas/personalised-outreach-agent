from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Scalar = str | int | float | bool

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class LeadData(StrictModel):
    company_name: str | None = None
    contact_first_name: str | None = None
    contact_role: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    employees: int = Field(gt=0)
    annual_revenue: str | None = None
    country: str = Field(min_length=1)
    erp: str | None = None
    accounting_system: str | None = None
    company_description: str | None = None
    pain_points: list[str] = Field(default_factory=list)
    qualification_score: float = Field(ge=0)

class SelectedStrategy(StrictModel):
    id: str = Field(min_length=1)
    score: float = Field(ge=0)
    matched_on: dict[str, Any] = Field(default_factory=dict)

class StrategySelection(StrictModel):
    selected_strategies: list[SelectedStrategy]

    @field_validator("selected_strategies")
    @classmethod
    def require_strategy(cls, value: list[SelectedStrategy]) -> list[SelectedStrategy]:
        if not value:
            raise ValueError("At least one strategy must be selected.")
        return value

class StrategyContent(StrictModel):
    id: str
    name: str
    description: str
    talking_points: list[str]
    cta: str
    priority: int = 0

class StrategyTalkingPoint(StrictModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class RawStrategyContent(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    talking_points: list[StrategyTalkingPoint]
    cta: str = Field(min_length=1)
    priority: int = 0


class RawStrategyAgentOutput(StrictModel):
    id: str = Field(min_length=1)
    score: float = Field(ge=0)
    matched_on: dict[str, Any]
    strategy: RawStrategyContent

class StrategyAgentBatchInput(StrictModel):
    selected_strategies: list[RawStrategyAgentOutput] = Field(
        min_length=1,
        max_length=3,
    )

class OutreachRequest(StrictModel):
    lead_id: str = Field(min_length=1)
    lead: LeadData
    strategy_selection: StrategySelection
    strategy_content: StrategyContent | None = None

class FactUsed(StrictModel):
    field: str
    value: Scalar

class Personalization(StrictModel):
    facts_used: list[FactUsed]
    primary_angle: str
    reason: str

class EmailMessage(StrictModel):
    subject: str
    body: str

class LinkedInMessage(StrictModel):
    body: str

class FollowUp(StrictModel):
    step: int
    delay_days: int = Field(ge=1)
    subject: str
    body: str

class GeneratedDraft(StrictModel):
    language: str = "English"
    personalization: Personalization
    subject_options: list[str] = Field(min_length=3, max_length=3)
    initial_email: EmailMessage
    linkedin_message: LinkedInMessage
    follow_ups: list[FollowUp] = Field(min_length=2, max_length=2)
    cta: str

class QualityChecks(StrictModel):
    qualification_score: float
    strategy_score: float
    unsupported_claims: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    sensitive_data_used: bool = False
    needs_human_review: bool = True

class OutreachOutput(StrictModel):
    lead_id: str
    strategy_id: str
    channels: list[Literal["email", "linkedin"]]
    language: str
    personalization: Personalization
    subject_options: list[str]
    initial_email: EmailMessage
    linkedin_message: LinkedInMessage
    follow_ups: list[FollowUp]
    cta: str
    quality_checks: QualityChecks
    status: Literal["outreach_drafted", "manual_review_required"]
