import json
import os
import re
from typing import Any, Protocol

import httpx

from dotenv import load_dotenv

from .schemas import GeneratedDraft

load_dotenv()

class LLMProvider(Protocol):
    def generate(self, payload: dict[str, Any]) -> GeneratedDraft: ...

class MockProvider:
    """Deterministic provider: the MVP works without an API key."""

    def generate(self, payload: dict[str, Any]) -> GeneratedDraft:
        lead = payload["lead"]
        strategy = payload["strategy_content"]
        first = lead.get("contact_first_name") or "there"
        company = lead.get("company_name") or "your company"
        industry = lead["industry"]
        country = lead["country"]
        role = lead["contact_role"]
        pain = (lead.get("pain_points") or ["audit preparation"])[0]
        systems = [x for x in (lead.get("erp"), lead.get("accounting_system")) if x]
        systems_phrase = f" and uses {' and '.join(systems)}" if systems else ""

        subjects = [
            f"Reducing audit preparation risk at {company}",
            "A proactive approach to audit readiness",
            "Identifying tax inconsistencies earlier",
        ]
        body = (
            f"Hi {first},\n\n"
            f"I noticed that {company} operates in the {industry} sector in "
            f"{country}{systems_phrase}.\n\n"
            f"For a {role}, {pain} can become harder to manage as finance "
            "operations grow. Taxivity helps finance teams identify potential "
            "tax inconsistencies earlier, reduce audit exposure, and increase "
            "confidence before external audits.\n\n"
            f"Would you be open to a short conversation about a "
            f"{strategy['cta'].lower()}?\n\nBest regards,\nMantas"
        )

        facts = [
            {"field": "industry", "value": industry},
            {"field": "country", "value": country},
            {"field": "contact_role", "value": role},
        ]
        for field in ("company_name", "erp", "accounting_system"):
            if lead.get(field):
                facts.append({"field": field, "value": lead[field]})
        if lead.get("pain_points"):
            facts.append({"field": "pain_point", "value": pain})

        return GeneratedDraft.model_validate({
            "language": "English",
            "personalization": {
                "facts_used": facts,
                "primary_angle": strategy["name"],
                "reason": "The strategy matches the lead profile and audit-related context.",
            },
            "subject_options": subjects,
            "initial_email": {"subject": subjects[0], "body": body},
            "linkedin_message": {
                "body": (
                    f"Hi {first}, I work with finance teams that want to identify "
                    f"tax and reconciliation issues before external audits. "
                    f"Given {company}'s environment, the {strategy['name'].lower()} "
                    "approach may be relevant. Open to a brief conversation?"
                )
            },
            "follow_ups": [
                {
                    "step": 2,
                    "delay_days": 3,
                    "subject": f"Re: {subjects[0]}",
                    "body": (
                        f"Hi {first},\n\nJust following up. Taxivity can help "
                        "finance teams identify potential tax inconsistencies "
                        "before they become audit findings.\n\n"
                        f"Would a short {strategy['cta'].lower()} be useful?\n\n"
                        "Best regards,\nMantas"
                    ),
                },
                {
                    "step": 3,
                    "delay_days": 5,
                    "subject": "One final thought on audit readiness",
                    "body": (
                        f"Hi {first},\n\nOne final thought: reviewing tax and "
                        "reconciliation risks before an external audit can make "
                        "preparation more predictable.\n\nWould it be useful "
                        "to see how Taxivity approaches this?\n\nBest regards,\nMantas"
                    ),
                },
            ],
            "cta": strategy["cta"],
        })

class OpenAICompatibleProvider:
    SYSTEM_PROMPT = """
When listing pain points in personalization.facts_used, create one separate
object per pain point and use the field name "pain_point".

Never combine multiple pain points into one "pain_points" value.

The first follow-up must have step=2 and delay_days=3.
The second follow-up must have step=3 and delay_days=5.
""".strip()

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _json(text: str) -> dict[str, Any]:
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
        result = json.loads(clean)
        if not isinstance(result, dict):
            raise ValueError("Model output must be a JSON object.")
        return result

    def generate(self, payload: dict[str, Any]) -> GeneratedDraft:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Input JSON:\n"
                        + json.dumps(payload, ensure_ascii=False, indent=2)
                        + "\n\nOutput JSON schema:\n"
                        + json.dumps(
                            GeneratedDraft.model_json_schema(),
                            ensure_ascii=False,
                            indent=2,
                        )
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }
        if os.getenv("LLM_JSON_MODE", "true").lower() in {"1", "true", "yes"}:
            body["response_format"] = {"type": "json_object"}

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=90,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        return GeneratedDraft.model_validate(self._json(text))

def get_provider() -> LLMProvider:
    name = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if name == "mock":
        return MockProvider()
    if name == "openai_compatible":
        values = {
            "LLM_BASE_URL": os.getenv("LLM_BASE_URL"),
            "LLM_API_KEY": os.getenv("LLM_API_KEY"),
            "LLM_MODEL": os.getenv("LLM_MODEL"),
        }
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise RuntimeError("Missing environment variables: " + ", ".join(missing))
        return OpenAICompatibleProvider(
            base_url=values["LLM_BASE_URL"],
            api_key=values["LLM_API_KEY"],
            model=values["LLM_MODEL"],
        )
    raise RuntimeError("LLM_PROVIDER must be 'mock' or 'openai_compatible'.")
