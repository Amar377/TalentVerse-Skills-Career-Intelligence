# TalentVerse — Skills & Career Intelligence

A Streamlit application for resume analysis, career roadmaps, job matching, portfolio project planning, and interview practice feedback.

## What's improved

- Provider-agnostic AI layer: Groq, Google Gemini, OpenAI, and Mistral.
- Provider priority and model names are controlled in `.env`.
- Automatic fallback: if one configured provider fails, TalentVerse tries the next configured provider.
- Pydantic schema-guided output and clear user-facing error messages.
- Polished responsive Streamlit interface with provider status, last successful model, and five career workflows.
- Session-only profile storage and demo request limits remain enabled.

## Project files

- `uitalentverse.py` — Streamlit frontend
- `talentverse.py` — schemas, AI provider selection/fallback, workflows, and request protection
- `requirements.txt` — dependencies
- `.env.example` — safe environment-variable template

## Setup (Windows PowerShell)

```powershell
cd path\to\TalentVerse-Skills-Career-Intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add at least one valid API key. Keep `.env` private and never commit it.

Run the app:

```powershell
streamlit run uitalentverse.py
```

## Switching providers only through `.env`

Example: Groq primary, Gemini fallback:

```env
AI_PROVIDER_ORDER=groq,gemini,openai,mistral
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-3.8-flash
```

Example: Gemini primary, Groq fallback:

```env
AI_PROVIDER_ORDER=gemini,groq
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-3.8-flash
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
```

The application only tries providers that have a key configured. It attempts providers in `AI_PROVIDER_ORDER` order and falls back when a provider errors. After changing `.env`, restart Streamlit so the new configuration is loaded. Provider and model availability depends on your provider account and the current API catalog.

## Security and privacy

- Do not share or commit `.env`.
- Do not commit real candidate data.
- The profile save feature stores data only in the current Streamlit session; it is not durable database storage.
- Request limits are in-memory demo protections and are not a substitute for production-grade distributed rate limiting.
- AI-generated career recommendations should be reviewed by the user.

## Smoke-test checklist

- [ ] `streamlit run uitalentverse.py` launches
- [ ] Sidebar shows configured providers and their priority order
- [ ] Resume analysis returns a structured `CandidateProfile`
- [ ] Roadmap returns milestones
- [ ] Job matching returns a score and evidence
- [ ] Project brief returns features and milestones
- [ ] Interview Coach returns strengths and practice tasks
- [ ] An invalid/missing API key falls through to the next configured provider
- [ ] Saving and exporting session profiles works
