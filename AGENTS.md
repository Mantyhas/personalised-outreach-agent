# Codex instructions

- Python 3.12.
- Keep Pydantic validation at API and LLM boundaries.
- Never commit secrets.
- Preserve the mock provider.
- The service drafts content only and must never send messages.
- All outputs require human review.
- Facts used for personalisation must be present in input.
- Initial email maximum: 130 words.
- Exactly 3 subjects and 2 follow-ups.
- Run `pytest -q` before claiming completion.
