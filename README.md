<div align="center">

# TalentVerse
### Skills & Career Intelligence Platform

**Turn career goals into actionable learning plans, discover skill gaps, and build a stronger technical portfolio.**

A Gemini-powered Streamlit application for resume analysis, career planning, job matching, portfolio project planning, and interview practice feedback.

</div>

---

## Overview

TalentVerse helps students and early-career candidates understand their current skills and plan their next career steps. It uses Google's Gemini API to transform user-provided text into structured, actionable career insights.

The application has a simple two-file architecture:

- **`uitalentverse.py`** — Streamlit user interface.
- **`talentverse.py`** — Gemini integration, structured validation, analysis logic, and JSON-based profile storage.

## Features

| Feature | What it does |
|---|---|
| **Resume Analyzer** | Extracts a structured candidate profile from pasted resume text, including skills, education, projects, and experience. |
| **Career Roadmap** | Compares current skills with a career goal and generates skill gaps, learning priorities, and milestone-based actions. |
| **Job Matcher** | Compares a candidate profile with a job description, highlighting relevant skills, missing evidence, and improvement opportunities. |
| **Portfolio Project Brief** | Uses a user's interests and skills to propose a project, recommended technologies, core features, and implementation milestones. |
| **Interview Coach** | Turns interview practice notes into strengths, improvement areas, and next-practice tasks. |
| **Profile Management** | Saves and updates candidate profiles in a local JSON file, using the candidate's email to identify an existing profile. |

> **Input note:** Resume analysis currently supports pasted text. Audio upload and automatic speech-to-text transcription are not implemented yet.

## Tech Stack

- **Python** — application logic
- **Streamlit** — interactive web UI
- **Google Gemini API** — generative AI
- **LangChain Google GenAI integration** — model integration
- **Pydantic** — structured data validation
- **JSON** — local profile persistence

## Application Architecture

```text
                 ┌──────────────────────────┐
                 │       User / Browser     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │     uitalentverse.py     │
                 │      Streamlit UI        │
                 └────────────┬─────────────┘
                              │ function calls
                              ▼
                 ┌──────────────────────────┐
                 │      talentverse.py      │
                 │ Gemini · Pydantic · JSON │
                 └────────────┬─────────────┘
                              │
                ┌─────────────┴──────────────┐
                ▼                            ▼
       ┌─────────────────┐          ┌─────────────────┐
       │ Google Gemini   │          │ Local JSON file │
       │   API service   │          │ Candidate data  │
       └─────────────────┘          └─────────────────┘
```

## Getting Started

### 1. Prerequisites

- Python 3.10 or newer (use a version compatible with your installed dependencies)
- A Google Gemini API key
- Git (optional, for cloning the repository)

### 2. Clone the repository

```bash
git clone https://github.com/Amar377/TalentVerse-Skills-Career-Intelligence.git
cd TalentVerse-Skills-Career-Intelligence
```

### 3. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the Python executable inside the environment directly or follow your organization's approved PowerShell execution-policy guidance.

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure your API key

Create a local file named `.env` in the project root. Add your Gemini API key using the variable name supported by the backend (commonly `GOOGLE_API_KEY` or `GEMINI_API_KEY`).

Example:

```env
GOOGLE_API_KEY=replace_with_your_own_api_key
GEMINI_API_KEY=replace_with_your_own_api_key
```

If your backend reads a configurable model name, set it to a model available to your Gemini API account. Do not paste real API keys into this README, source files, screenshots, or public issues.

### 6. Run TalentVerse

```bash
streamlit run uitalentverse.py
```

Streamlit will print a local address in the terminal, commonly `http://localhost:8501`. Open that address in your browser.

## How to Use

1. Open the feature you want to use from the app's navigation or tabs.
2. Paste the resume, career goal, job description, project interests, or interview notes requested by that feature.
3. Run the analysis and review the generated result.
4. Check extracted fields carefully; AI-generated output should be treated as assistance, not as a guaranteed factual record.
5. Confirm a candidate profile before saving it, when the UI provides that option.
6. Open **Saved Profiles** to review stored candidate profiles.

## Testing Checklist

Use this checklist after setup or when making changes:

- [ ] App launches using `streamlit run uitalentverse.py`
- [ ] Resume Analyzer returns a structured profile
- [ ] Candidate profile can be saved
- [ ] Existing profile can be updated without creating a duplicate
- [ ] Career Roadmap returns skill gaps and milestones
- [ ] Job Matcher returns a reasonable candidate/job comparison
- [ ] Portfolio Project Brief returns actionable project details
- [ ] Interview Coach returns strengths and practice tasks
- [ ] Missing or invalid inputs are handled clearly
- [ ] App behaves sensibly when the Gemini API quota is exhausted

The resume analysis, profile persistence, career roadmap, job matching, and project brief workflows have been manually tested during development. Interview Coach testing remains pending when Gemini API quota is available. Results may vary with the model, input quality, and API availability.

## Project Structure

```text
TalentVerse-Skills-Career-Intelligence/
├── uitalentverse.py          # Streamlit frontend
├── talentverse.py            # AI and data backend
├── requirements.txt          # Python dependencies
├── .env                      # Local secrets; do not commit
├── .env.example              # Optional safe configuration template
├── .gitignore                # Excludes secrets and local artifacts
└── talentverse_profiles.json # Local profile data; do not commit
```

The exact files present in your repository may differ. Keep `.env`, virtual environments, caches, and any file containing personal candidate data out of version control.

## Privacy and Security

- **Never commit API keys or secrets.** Keep them in a local `.env` file and ensure `.env` is listed in `.gitignore`.
- Do not commit real resumes, candidate records, or generated local profile databases.
- Use fictional sample data when demonstrating the app publicly.
- Review AI-generated output before relying on it for career or hiring decisions.
- Avoid entering sensitive personal information unless you understand where it is sent and stored. Resume text sent for analysis is processed by the configured AI provider under that provider's terms.
- If a secret was ever committed, remove it from the repository and rotate/revoke it. Deleting it in a later commit does not make the exposed secret safe.

## Current Limitations

- Resume input is text-based; audio transcription is not available yet.
- Candidate profiles are stored locally in a JSON file; this is intended for a prototype and is not a production multi-user database.
- Gemini API usage is subject to account access, rate limits, and quota availability.
- The app is a Streamlit application and does not currently expose a separate FastAPI backend.

## Roadmap

- [ ] Add audio introduction upload and speech-to-text transcription
- [ ] Add more automated tests for schemas, validation, and profile storage
- [ ] Improve user-facing handling of API quota and network errors
- [ ] Add optional database support for multi-user deployment
- [ ] Deploy the application and document the live demo once available

## Contributing

Suggestions and bug reports are welcome. If you want to contribute:

1. Fork the repository.
2. Create a feature branch.
3. Make a focused change and test it locally.
4. Open a pull request describing the change and the test results.

Please do not include secrets, personal resumes, or private candidate data in commits or issue reports.

## License

No license has been specified yet. Add a `LICENSE` file before presenting the project as open source, and choose a license that matches how you want others to use, modify, and distribute the code.

---

<div align="center">

**Built to make career planning more structured, practical, and actionable.**

</div>
