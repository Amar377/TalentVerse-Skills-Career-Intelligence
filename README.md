# TalentVerse 2.0 â€” AI-Powered Career Intelligence SaaS Platform

> **"Your Skills. Your Potential. Your Career, Intelligently Connected."**

TalentVerse 2.0 is an enterprise-grade, visually exceptional career intelligence SaaS platform. It transforms unstructured resumes and fragmented skill sets into quantifiable career readiness, actionable learning roadmaps, explainable job match benchmarks, portfolio architecture briefs, and interactive mock interview mentoring.

---

## âœ¨ Product Features

### 1. World-Class SaaS Landing Page
- **Hero & Value Proposition**: High-conversion hero with tagline and one-click demo sandbox.
- **Platform Architecture Showcase**: Highlights the multi-provider fallback engine (Gemini 3.8 Flash, Groq, OpenAI, Mistral).
- **The Talent Acceleration Loop**: 4-step cyclical workflow (Analyze â†’ Map â†’ Prepare â†’ Match).
- **Audience Benefits**: Tailored pathways for students/graduates and working professionals.
- **Interactive FAQ & Professional Footer**.

### 2. Analytics Dashboard
- **Personalized Welcome Banner**: Greets candidate with active target role and sandbox status.
- **Career Readiness Score Meter**: Computed 0â€“100% readiness gauge with progress indicators.
- **Technical & Soft Skills Inventory**: Shows skills listed in the candidate's profile without inventing proficiency scores.
- **Roadmap Milestones Tracker**: Live progress percentage with completed milestones count.
- **Strategic Next Actions**: High/medium priority recommendations with one-click direct deep-links.
- **Recent Activity Timeline**: Chronological log of analyses, scores, and updates.

### 3. Resume Analyzer & Intelligence
- **Drag-and-Drop Parser**: Accepts PDF, DOCX, TXT, and Markdown files (up to 10MB), extracts document text, and uses structured AI analysis.
- **Alternative Paste Text Tab**: Direct input for quick pasting.
- **Comprehensive Candidate Profile**:
  - Technical & Soft Skills chips
  - Chronological Experience history
  - Education & Verified Certifications
  - Portfolio Projects
  - Core Strengths & Missing Information identification
  - Actionable Improvement Recommendations
- **Save to Master Profile & JSON Dossier Export**.

### 4. Interactive Career Roadmap
- **Customizable Sprint Generator**: Set target role, known skills, seniority level, and duration (4 to 24 weeks).
- **Priority Skill Gaps**: Highlights key competencies required for the target position.
- **Interactive Weekly Milestones**:
  - Weekly learning tasks checklist with persistent checkboxes.
  - Tangible deliverables and verification criteria.
  - Live progress meter updating in real-time.
- **Curated Learning Resources**: Outbound links to documentation, books, and courses.

### 5. Job Fit Matcher & Gap Analysis
- **Job Posting Input**: Paste any real-world job description and benchmark against your candidate profile.
- **AI-Estimated Match Score**: Fit estimate with matching evidence and missing-skill context; it is not a hiring decision.
- **Side-by-Side Comparison**:
  - Matching Verified Skills (green chips with checkmarks)
  - Missing or Unverified Skills (amber chips with alert indicators)
- **Contextual Alignment**: Experience and education relevance breakdown.
- **Actionable Steps to Qualify**: Concrete tasks to bridge the remaining gap before applying.

### 6. Portfolio Project Recommendations
- **Targeted Project Discovery**: Filters projects by domain and difficulty (Beginner, Intermediate, Advanced).
- **Engineering Architecture Cards**:
  - Problem statement & target user personas
  - Core technical capabilities
  - Modern tech stack chips
  - Chronological execution phases
  - Quantifiable evaluation metrics (e.g. latency, throughput)
  - Polished resume/portfolio snippet ready for GitHub READMEs.

### 7. AI Interview Coach
- **Dual Formats**: Supports both Technical Architecture & Behavioral (STAR method) interviews.
- **Role-Tailored Question Generator**: Generates 4 high-signal interview questions with difficulty tags and coach tips.
- **Interactive Response Submission**: Candidate types structured answers and submits for deep AI analysis.
- **AI Evaluation Dossier**:
  - Objective answer score (0â€“100)
  - Observed strengths
  - Missing principles and concepts
  - **Gold-Standard Model Answer**: Demonstrates how a top-tier senior candidate answers.
  - Drill exercises for next session focus.

### 8. Candidate Master Profile
- Comprehensive editor for personal info, target role, experience level, summary, technical skills manager, soft skills manager, work experience, and verified projects.
- Live readiness score calculation with instant database persistence.

### 9. Saved Reports Dossier
- Archive of all generated analyses with filters by report type (`resume`, `roadmap`, `job_match`, `project`, `interview`).

- Search bar, full JSON modal inspector, and single-click JSON dossier download.

### 10. Platform Settings & Multi-Provider Telemetry
- Light & Dark mode toggle (custom deep navy obsidian studio vs crisp daylight).
- Live Multi-Provider AI Fallback Dashboard displaying loaded API keys and provider cascade order.
- One-click session reset.

---

## ðŸ—ï¸ Architecture & Technology Stack

### Frontend
- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS with warm ivory, plum, terracotta, gold, and sage design tokens; separate aubergine dark theme
- **Icons**: Lucide React
- **Routing**: React Router DOM (v7 SPA client routing)
- **State & Alerts**: Custom React Context (`AuthContext`, `ThemeContext`, `ToastContext`)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ORM & Database**: SQLAlchemy 2.0 with SQLite database (`talentverse.db`)
- **Document Parsing**: PyMuPDF (`pymupdf`) for PDFs & `python-docx` for Word documents
- **Multi-Provider AI Engine**:
  - **Google Gemini**: Modern `google-genai` SDK (`gemini-3.8-flash`)
  - **Groq**: `groq` SDK (`llama-3.3-70b-versatile`)
  - **OpenAI**: `openai` SDK (`gpt-4o-mini`)
  - **Mistral**: `mistralai` SDK (`mistral-small-latest`)
  - **Provider Failover**: Tries configured providers in order. If all fail, the API returns a clear service-unavailable response instead of fabricating analysis.

---

## ðŸš€ Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 20.19+ or 22.12+ and npm (required by the current Vite version)

### 2. Environment Configuration
If `.env` does not already exist, copy `.env.example` to `.env` in the project root. Do not overwrite an existing `.env`. Set `TALENTVERSE_SECRET_KEY` to a random secret of at least 32 characters before production. Keep `.env` private.

```env
AI_PROVIDER_ORDER=gemini,groq,openai,mistral
GEMINI_MODEL=gemini-3.8-flash
GOOGLE_API_KEY=your_google_gemini_api_key
TALENTVERSE_SECRET_KEY=replace-with-a-random-secret-at-least-32-characters
CORS_ORIGINS=https://your-frontend.example.com

# Optional fallbacks
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

### 3. Install Dependencies

**Backend:**
```bash
python -m pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Running the Application

#### Option A: Unified Production Mode (Recommended)
Run the FastAPI application. It serves both the REST API and the compiled React frontend on port 8000:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

#### Option B: Full-Stack Developer Mode (Hot Module Replacement)
1. **Start Backend** from PowerShell in the project directory:
   ```bash
   .\start_backend.ps1
   ```
2. **Start Frontend** in a second PowerShell terminal:
   ```bash
   .\start_frontend.ps1
   ```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## ðŸ§ª Automated Testing
Install development dependencies and run the backend suite. Setting the provider order to `disabled` verifies the no-provider error path without making live provider requests:
```bash
python -m pip install -r requirements-dev.txt
$env:AI_PROVIDER_ORDER="disabled"
python -m pytest backend/tests -q
Remove-Item Env:AI_PROVIDER_ORDER
```

---

## ðŸ”’ Security & Privacy
- API keys are loaded from the server environment or `.env` and are not sent to the frontend client.
- Password hashes use per-password salted PBKDF2-SHA256; successful login upgrades legacy hashes.
- JWT bearer tokens validate protected workspace sessions.
- Protected API routes require a valid bearer token; demo access uses the explicit demo login.
- Configure a strong `TALENTVERSE_SECRET_KEY` and explicit `CORS_ORIGINS` in production.
- AI request limits are in-memory per process and need a shared store for multi-worker deployments.

## Database and Schema Changes

SQLite is the default database. Startup creates missing tables with SQLAlchemy metadata, but the repository does not currently include versioned database migrations; `create_all` does not update existing table schemas. Back up the database and add a migration workflow before applying schema changes to an existing deployment. PostgreSQL is not currently a documented or dependency-complete deployment target.
