from typing import Any

from .providers import LLMProvider
from .schemas import GeneratedDraft, OutreachOutput, OutreachRequest, QualityChecks
from .strategies import get_strategy

MIN_QUALIFICATION_SCORE = 70.0

def count_words(text: str) -> int:
    return len([word for word in text.split() if word])

def resolve_strategy(request: OutreachRequest) -> dict[str, Any]:
    selected = request.strategy_selection.selected_strategies[0]
    if request.strategy_content is not None:
        if request.strategy_content.id != selected.id:
            raise ValueError("strategy_content.id must match the selected strategy ID.")
        return request.strategy_content.model_dump(mode="json")
    return get_strategy(selected.id)

def allowed_facts(request: OutreachRequest) -> dict[str, set[str]]:
    lead = request.lead
    result = {
        "industry": {lead.industry},
        "employees": {str(lead.employees)},
        "country": {lead.country},
        "contact_role": {lead.contact_role},
        "pain_point": set(lead.pain_points),
        "pain_points": set(lead.pain_points),
    }
    optional = {
        "company_name": lead.company_name,
        "contact_first_name": lead.contact_first_name,
        "annual_revenue": lead.annual_revenue,
        "erp": lead.erp,
        "accounting_system": lead.accounting_system,
        "company_description": lead.company_description,
    }
    for field, value in optional.items():
        if value:
            result[field] = {str(value)}
    return result

def find_unsupported_facts(
    request: OutreachRequest,
    draft: GeneratedDraft,
) -> list[str]:
    allowed = allowed_facts(request)
    unsupported: list[str] = []
    for fact in draft.personalization.facts_used:
        field = fact.field.strip()
        value = str(fact.value).strip()
        values = allowed.get(field)
        if values is None:
            unsupported.append(f"Unknown fact field: {field}")
            continue
        normalized = {item.strip().casefold() for item in values}
        if value.casefold() not in normalized:
            unsupported.append(f"Unsupported fact: {field}={value}")
    return unsupported

def validate_draft(
    draft: GeneratedDraft,
    strategy: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    words = count_words(draft.initial_email.body)
    if words > 130:
        errors.append(f"Initial email is {words} words; maximum is 130.")
    if draft.initial_email.subject not in draft.subject_options:
        errors.append("Initial email subject must be one of subject_options.")
    if [item.step for item in draft.follow_ups] != [2, 3]:
        errors.append("Follow-up steps must be exactly [2, 3].")
    if draft.cta.strip().casefold() != str(strategy["cta"]).strip().casefold():
        errors.append("CTA must exactly match strategy_content.cta.")
    return errors

def generate_outreach(
    request: OutreachRequest,
    provider: LLMProvider,
) -> OutreachOutput:
    if request.lead.qualification_score < MIN_QUALIFICATION_SCORE:
        raise ValueError(
            f"Lead qualification score must be at least {MIN_QUALIFICATION_SCORE:g}."
        )

    selected = request.strategy_selection.selected_strategies[0]
    strategy = resolve_strategy(request)
    payload = {
        "lead_id": request.lead_id,
        "lead": request.lead.model_dump(mode="json"),
        "selected_strategy": selected.model_dump(mode="json"),
        "strategy_content": strategy,
    }

    draft = provider.generate(payload)
    unsupported = find_unsupported_facts(request, draft)
    validation_errors = validate_draft(draft, strategy)
    status = (
        "manual_review_required"
        if unsupported or validation_errors
        else "outreach_drafted"
    )

    return OutreachOutput(
        lead_id=request.lead_id,
        strategy_id=selected.id,
        channels=["email", "linkedin"],
        language=draft.language,
        personalization=draft.personalization,
        subject_options=draft.subject_options,
        initial_email=draft.initial_email,
        linkedin_message=draft.linkedin_message,
        follow_ups=draft.follow_ups,
        cta=draft.cta,
        quality_checks=QualityChecks(
            qualification_score=request.lead.qualification_score,
            strategy_score=selected.score,
            unsupported_claims=unsupported,
            validation_errors=validation_errors,
            sensitive_data_used=False,
            needs_human_review=True,
        ),
        status=status,
    )
