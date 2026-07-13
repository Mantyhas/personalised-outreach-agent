# Personalised Outreach Agent MVP

Working Python/FastAPI agent that receives a qualified lead and selected
strategy, then returns:

- 3 email subject options
- 1 initial email under 130 words
- 1 LinkedIn message
- 2 follow-up emails
- facts used for personalisation
- CTA and validation results
- `needs_human_review: true`

It never sends messages.

## Run on Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

The default provider is `mock`, so it works without an API key.

## Run tests

```powershell
pytest -q
```

## Test endpoint

```text
POST /personalised-outreach
```

Use `sample_request.json` in Swagger or curl.

## Use a real model later

Set in `.env`:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://your-provider-base-url/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
LLM_JSON_MODE=true
```

The provider must expose `POST /chat/completions`.

## Later database integration

A database worker will read the lead sections, call this agent, save the
response under `personalised_outreach`, mark its task completed, and create
the next `compliance_agent` task.
