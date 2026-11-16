"""Multi-provider AI Engine for TalentVerse 2.0 with fallback and structured outputs."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import date
from typing import Callable, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

from backend.config import (
    AI_PROVIDER_ORDER,
    PROVIDER_MODELS,
    PROVIDER_ENV_KEYS,
    SESSION_DAILY_LIMIT,
    GLOBAL_DAILY_LIMIT,
    DUPLICATE_COOLDOWN_SECONDS,
)
from backend.schemas import (
    CandidateProfileData,
    CareerRoadmapData,
    JobMatchData,
    ProjectBriefData,
    InterviewAnalysisData,
    InterviewQuestionItem,
)

logger = logging.getLogger("talentverse.ai")

T = TypeVar("T", bound=BaseModel)

# Rate limiting lock and caches
_rate_lock = threading.Lock()
_usage_day = date.today()
_session_usage: dict[str, int] = {}
_global_usage = 0
_recent_requests: dict[tuple[str, str], float] = {}

_last_successful_provider: Optional[str] = None
_last_successful_model: Optional[str] = None


class RateLimitError(RuntimeError):
    pass


class AIProviderUnavailable(RuntimeError):
    pass


class IncompleteAIResponse(ValueError):
    def __init__(self, fields: set[str]):
        self.fields = tuple(sorted(fields))
        super().__init__("AI response is missing required fields.")


RESUME_REQUIRED_FIELDS = frozenset(CandidateProfileData.model_fields)
_RESUME_REQUIRED_ATS_SECTIONS = frozenset(
    {"summary", "skills", "experience", "education", "projects"}
)
_GROQ_JSON_SCHEMA_MODELS = frozenset(
    {
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-safeguard-20b",
        "qwen/qwen3.8-27b",
        "meta-models/muse-spark-open",
    }
)


def resume_analysis_issues(profile: CandidateProfileData) -> set[str]:
    """Return missing analysis output without inspecting or logging resume content."""
    issues = set()
    if profile.ats_score is None:
        issues.add("ats_score")
    if not profile.ats_score_explanation.strip():
        issues.add("ats_score_explanation")
    if not _RESUME_REQUIRED_ATS_SECTIONS.issubset(profile.ats_section_completeness):
        issues.add("ats_section_completeness")
    if profile.experience and not profile.experience_analysis:
        issues.add("experience_analysis")
    if profile.education and not profile.education_analysis:
        issues.add("education_analysis")
    if profile.projects and not profile.projects_analysis:
        issues.add("projects_analysis")
    return issues


def reset_daily_usage_if_needed() -> None:
    global _usage_day, _session_usage, _global_usage, _recent_requests
    today = date.today()
    if today != _usage_day:
        _usage_day = today
        _session_usage = {}
        _global_usage = 0
        _recent_requests = {}


def check_rate_limits(
    session_id: str,
    payload_text: str,
    preferred_provider: Optional[str] = None,
) -> None:
    global _global_usage
    fingerprint_source = f"{preferred_provider or 'default'}\0{payload_text}"
    fingerprint = hashlib.sha256(
        fingerprint_source.encode("utf-8", errors="replace")
    ).hexdigest()
    now = time.monotonic()
    key = (session_id, fingerprint)

    with _rate_lock:
        reset_daily_usage_if_needed()
        previous = _recent_requests.get(key)
        if previous is not None and now - previous < DUPLICATE_COOLDOWN_SECONDS:
            wait_sec = max(1, int(DUPLICATE_COOLDOWN_SECONDS - (now - previous)))
            raise RateLimitError(
                f"Duplicate request detected. Please wait {wait_sec}s before resubmitting."
            )
        if _session_usage.get(session_id, 0) >= SESSION_DAILY_LIMIT:
            raise RateLimitError(
                f"Daily limit of {SESSION_DAILY_LIMIT} AI requests reached for this session."
            )
        if _global_usage >= GLOBAL_DAILY_LIMIT:
            raise RateLimitError("Shared daily AI request limit reached. Please try again tomorrow.")

        _session_usage[session_id] = _session_usage.get(session_id, 0) + 1
        _global_usage += 1
        _recent_requests[key] = now

        # Prune old records
        cutoff = now - DUPLICATE_COOLDOWN_SECONDS
        for old_key, ts in list(_recent_requests.items()):
            if ts < cutoff:
                _recent_requests.pop(old_key, None)


def get_configured_providers() -> list[str]:
    """Returns list of providers that have an API key set."""
    res = []
    for p in AI_PROVIDER_ORDER:
        key_name = PROVIDER_ENV_KEYS.get(p)
        if key_name and os.getenv(key_name, "").strip():
            res.append(p)
    return res


def get_provider_status() -> dict:
    global _last_successful_provider, _last_successful_model
    return {
        "priority": AI_PROVIDER_ORDER,
        "providers": [
            {
                "name": p,
                "model": PROVIDER_MODELS.get(p, "unknown"),
                "configured": bool(os.getenv(PROVIDER_ENV_KEYS.get(p, ""), "").strip()),
                "key_name": PROVIDER_ENV_KEYS.get(p, ""),
            }
            for p in AI_PROVIDER_ORDER
        ],
        "active_provider": _last_successful_provider,
        "active_model": _last_successful_model,
        "status": "configured" if get_configured_providers() else "unconfigured",
    }


def _call_gemini(prompt: str, json_schema_desc: str, model: Optional[str] = None) -> str:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30_000))
    model = model or PROVIDER_MODELS.get("gemini", "gemini-3.8-flash")

    contents = f"{prompt}\n\nYou MUST respond ONLY with a valid JSON object matching this schema:\n{json_schema_desc}"
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text


def _call_groq(prompt: str, json_schema_desc: str, model: Optional[str] = None) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key, timeout=30.0, max_retries=0)
    model = model or PROVIDER_MODELS.get("groq", "llama-3.3-70b-versatile")

    system_msg = f"You are a career intelligence AI. You MUST respond ONLY with valid JSON matching:\n{json_schema_desc}"
    if model.lower() in _GROQ_JSON_SCHEMA_MODELS:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "talentverse_response",
                "strict": False,
                "schema": json.loads(json_schema_desc),
            },
        }
    else:
        response_format = {"type": "json_object"}

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        response_format=response_format,
        temperature=0.2,
    )
    return completion.choices[0].message.content


def _call_openai(prompt: str, json_schema_desc: str, model: Optional[str] = None) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=0)
    model = model or PROVIDER_MODELS.get("openai", "gpt-4o-mini")

    system_msg = f"You are a career intelligence AI. Respond in JSON matching:\n{json_schema_desc}"
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return completion.choices[0].message.content


def _call_mistral(prompt: str, json_schema_desc: str, model: Optional[str] = None) -> str:
    try:
        from mistralai import Mistral
    except ImportError:
        from mistralai.client import Mistral

    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key, timeout_ms=30_000)
    model = model or PROVIDER_MODELS.get("mistral", "mistral-small-latest")

    system_msg = f"Respond ONLY in valid JSON matching schema:\n{json_schema_desc}"
    resp = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def execute_ai_json(
    prompt: str,
    schema_class: Type[T],
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
    required_fields: Optional[frozenset[str]] = None,
    result_issues: Optional[Callable[[T], set[str]]] = None,
) -> tuple[T, str, str]:
    """
    Executes prompt across configured providers in priority order.
    Returns (parsed_pydantic_object, provider_name, model_name).
    """
    global _last_successful_provider, _last_successful_model

    providers = get_configured_providers()
    if not providers:
        logger.warning("AI request unavailable: no configured provider keys.")
        raise AIProviderUnavailable("No AI provider is configured. Add a provider API key in the server environment.")

    if preferred_provider is not None and preferred_provider not in PROVIDER_ENV_KEYS:
        raise AIProviderUnavailable("The selected AI provider is not supported.")
    if preferred_provider in providers:
        providers = [preferred_provider] + [
            provider for provider in providers if provider != preferred_provider
        ]
    elif preferred_provider is None and "groq" in providers:
        providers = ["groq"] + [provider for provider in providers if provider != "groq"]

    check_rate_limits(session_id, prompt, preferred_provider=preferred_provider)
    schema_desc = json.dumps(schema_class.model_json_schema(), indent=2)
    failures: list[str] = []
    for provider in providers:
        model = PROVIDER_MODELS.get(provider, "default")
        try:
            logger.info("Attempting AI request with %s (%s).", provider, model)
            raw_json = ""
            if provider == "gemini":
                raw_json = _call_gemini(prompt, schema_desc, model)
            elif provider == "groq":
                raw_json = _call_groq(prompt, schema_desc, model)
            elif provider == "openai":
                raw_json = _call_openai(prompt, schema_desc, model)
            elif provider == "mistral":
                raw_json = _call_mistral(prompt, schema_desc, model)
        except Exception as exc:
            failures.append(f"{provider}: {type(exc).__name__}")
            logger.warning(
                "AI request failed for %s (%s): %s.",
                provider,
                model,
                type(exc).__name__,
            )
            continue

        if not isinstance(raw_json, str) or not raw_json.strip():
            failures.append(f"{provider}: empty response")
            logger.warning("AI response from %s (%s) was empty.", provider, model)
            continue

        try:
            parsed_data = json.loads(_clean_json_text(raw_json))
        except json.JSONDecodeError:
            failures.append(f"{provider}: invalid JSON")
            logger.warning("AI response from %s (%s) was not valid JSON.", provider, model)
            continue

        if not isinstance(parsed_data, dict):
            failures.append(f"{provider}: response was not a JSON object")
            logger.warning("AI response from %s (%s) was not a JSON object.", provider, model)
            continue

        missing_fields = set(required_fields or ()) - parsed_data.keys()
        if missing_fields:
            failures.append(f"{provider}: incomplete structured response")
            logger.warning(
                "AI response from %s (%s) omitted required fields: %s.",
                provider,
                model,
                sorted(missing_fields),
            )
            continue

        try:
            obj = schema_class.model_validate(parsed_data)
        except ValidationError as exc:
            invalid_fields = sorted(
                {
                    error["loc"][0]
                    for error in exc.errors(include_input=False)
                    if error.get("loc") and isinstance(error["loc"][0], str)
                }
            )
            failures.append(f"{provider}: schema validation failed")
            logger.warning(
                "AI response from %s (%s) failed schema validation for fields: %s.",
                provider,
                model,
                invalid_fields,
            )
            continue

        issues = result_issues(obj) if result_issues else set()
        if issues:
            failures.append(f"{provider}: incomplete structured response")
            logger.warning(
                "AI response from %s (%s) failed completeness checks for fields: %s.",
                provider,
                model,
                sorted(issues),
            )
            continue

        _last_successful_provider = provider
        _last_successful_model = model
        logger.info("AI response accepted from %s (%s).", provider, model)
        return obj, provider, model

    failure_summary = "; ".join(failures)
    logger.warning("AI request unavailable: all configured providers failed (%s).", failure_summary)
    raise AIProviderUnavailable(
        "All configured AI providers failed. "
        f"Provider errors: {failure_summary}. Check model IDs, provider access, and service availability."
    )


# ---------------- High-level Feature Functions ----------------

def analyze_resume_ai(
    resume_text: str,
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
) -> tuple[CandidateProfileData, str, str]:
    prompt = (
        "You are an expert technical talent analyst and resume intelligence engine. "
        "Analyze the resume and return a complete, structured JSON object matching the requested schema. "
        "Extract only facts supported by the resume. Use null only for schema fields that allow null; use "
        "empty strings, lists, or dictionaries for unavailable non-null fields. Never infer contact details, "
        "dates, years of experience, degrees, employers, or outcomes.\n"
        "For the overview, extract current_role and total_experience only when the resume supports them. "
        "Set target_role only when the resume states a career objective or desired role; do not present an "
        "inferred role as the candidate's stated goal.\n"
        "For experience_analysis, preserve company, job title, and duration only when stated; separate "
        "resume-supported responsibilities and achievements, identify missing measurable results, and give "
        "suggestions without inventing metrics. For education_analysis and projects_analysis, extract the "
        "requested details only when explicitly available. Keep the existing string-list profile fields populated too.\n"
        "Group technical skills into skills_by_category and explain target-role skill alignment only when a "
        "target role is stated. Assess the professional summary and provide specific improvement suggestions. "
        "Each improvement_recommendation should state what to improve, why it matters, how to improve it, and "
        "a truthful example rewrite when the resume provides enough evidence.\n"
        "Provide actionable, truthful suggestions to improve ATS compatibility. Never invent experience, "
        "skills, credentials, metrics, or keywords. Distinguish keywords evidenced in the resume from "
        "important role keywords that are missing.\n"
        "Set ats_score to a 0-100 general ATS-readiness estimate based on parseable structure, clear "
        "sections, relevant evidenced keywords, and concise evidence-based content. Do not claim to have run "
        "a third-party ATS. This estimate cannot predict hiring outcomes. Explain the main factors in "
        "ats_score_explanation, report whether the summary, skills, experience, education, and projects sections "
        "are present in ats_section_completeness, and list concrete formatting concerns. If the target role is "
        "not stated, explain that role-specific keyword alignment requires a job description.\n"
        "Set readiness_score separately as a general completeness/readiness score (0-100).\n\n"
        f"RESUME TEXT:\n{resume_text}"
    )
    return execute_ai_json(
        prompt,
        CandidateProfileData,
        session_id=session_id,
        preferred_provider=preferred_provider,
        required_fields=RESUME_REQUIRED_FIELDS,
        result_issues=resume_analysis_issues,
    )

def generate_roadmap_ai(
    skills: list[str],
    goal: str,
    level: str,
    weeks: int,
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
    candidate_context: Optional[str] = None,
) -> tuple[CareerRoadmapData, str, str]:
    prompt = (
        "You are a principal career strategist and technical learning mentor. "
        f"A candidate with experience level '{level}' wants to achieve the career goal: '{goal}'.\n"
        f"Current known skills: {', '.join(skills) if skills else 'None specified'}.\n"
        f"Resume-based experience and project context:\n{candidate_context or 'No additional resume context provided.'}\n"
        f"Target learning timeline: {weeks} weeks.\n\n"
        "Create an actionable, week-by-week career development roadmap. Identify critical skill gaps, "
        "concrete weekly milestones with specific learning tasks, tangible deliverables, measurable success criteria, "
        "and high-quality recommended learning resources."
    )
    return execute_ai_json(
        prompt,
        CareerRoadmapData,
        session_id=session_id,
        preferred_provider=preferred_provider,
    )

def match_job_ai(
    profile: CandidateProfileData,
    job_description: str,
    target_role: Optional[str] = None,
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
) -> tuple[JobMatchData, str, str]:
    profile_json = profile.model_dump_json(indent=2)
    prompt = (
        "You are an advanced AI recruiting and talent intelligence engine. "
        "Evaluate the candidate profile against the provided job description with high objectivity.\n"
        "Calculate an overall match score percent (0-100).\n"
        "Explicitly list matching skills that the candidate satisfies.\n"
        "Identify missing or unverified skills required by the job.\n"
        "Assess experience relevance and education relevance.\n"
        "Provide concrete evidence from the profile and clear improvement actions the candidate should take.\n\n"
        f"TARGET ROLE: {target_role or profile.target_role or 'Target Position'}\n\n"
        f"CANDIDATE PROFILE:\n{profile_json}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )
    return execute_ai_json(
        prompt,
        JobMatchData,
        session_id=session_id,
        preferred_provider=preferred_provider,
    )

def generate_project_recommendations_ai(
    interests: str,
    skills: list[str],
    domain: str,
    difficulty: str,
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
    candidate_context: Optional[str] = None,
) -> tuple[list[ProjectBriefData], str, str]:
    """Generates 3 tailored project recommendations matching candidate profile."""
    class MultiProjectResponse(BaseModel):
        projects: list[ProjectBriefData]

    prompt = (
        "You are an elite portfolio mentor and engineering architect. "
        "Recommend 3 distinct, impressive portfolio projects that will help this candidate stand out to hiring managers.\n"
        f"Candidate Interests: {interests}\n"
        f"Current Skills: {', '.join(skills)}\n"
        f"Resume-based career direction and experience:\n{candidate_context or 'No additional resume context provided.'}\n"
        f"Preferred Domain: {domain}\n"
        f"Target Difficulty: {difficulty}\n\n"
        "For each project, provide:\n"
        "- title: Catchy, professional name\n"
        "- problem_statement: High-impact real-world challenge it solves\n"
        "- domain: e.g. Fintech, AI/ML, Healthcare, Developer Tools\n"
        "- difficulty: Beginner, Intermediate, or Advanced\n"
        "- target_users: List of user personas\n"
        "- core_features: 4-6 key technical features\n"
        "- suggested_tech_stack: Specific modern technologies\n"
        "- implementation_milestones: 4 chronological execution steps\n"
        "- evaluation_metrics: Quantifiable benchmarks (latency, accuracy, user satisfaction)\n"
        "- portfolio_description: A polished 2-sentence blurb ready for their resume or GitHub README."
    )
    res, provider, model = execute_ai_json(
        prompt,
        MultiProjectResponse,
        session_id=session_id,
        preferred_provider=preferred_provider,
    )
    if not res.projects:
        raise AIProviderUnavailable("The configured AI provider returned no project recommendations.")
    return res.projects, provider, model

def generate_interview_questions_ai(
    target_role: str,
    interview_type: str = "technical",
    level: str = "Entry-level",
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
    candidate_context: Optional[str] = None,
) -> tuple[list[InterviewQuestionItem], str, str]:
    class QuestionList(BaseModel):
        questions: list[InterviewQuestionItem]

    prompt = (
        f"You are a veteran technical hiring manager conducting a {interview_type} interview for a '{target_role}' ({level}).\n"
        "Generate 4 realistic, high-signal interview questions ranging from conceptual to practical problem solving.\n"
        "Use demonstrated skills and experience in the candidate context to tailor questions, without assuming "
        "unlisted qualifications. Include relevant questions about identified skill gaps where appropriate.\n"
        f"CANDIDATE CONTEXT:\n{candidate_context or 'No resume profile context is available.'}\n"
        "For each question, provide an id, the question text, type ('technical' or 'behavioral'), difficulty ('Easy', 'Medium', 'Hard'), "
        "a list of key topics the candidate should cover, and a quick helpful tip."
    )
    res, provider, model = execute_ai_json(
        prompt,
        QuestionList,
        session_id=session_id,
        preferred_provider=preferred_provider,
    )
    if not res.questions:
        raise AIProviderUnavailable("The configured AI provider returned no interview questions.")
    return res.questions, provider, model

def evaluate_interview_ai(
    target_role: str,
    interview_type: str,
    question: str,
    user_answer: str,
    session_id: str = "guest",
    preferred_provider: Optional[str] = None,
    candidate_context: Optional[str] = None,
) -> tuple[InterviewAnalysisData, str, str]:
    prompt = (
        f"You are an expert technical interviewer evaluating a candidate for the role '{target_role}'.\n"
        f"INTERVIEW TYPE: {interview_type}\n"
        f"QUESTION: {question}\n\n"
        f"CANDIDATE PROFILE CONTEXT:\n{candidate_context or 'No resume profile context is available.'}\n\n"
        f"CANDIDATE'S ANSWER:\n{user_answer}\n\n"
        "Evaluate this response objectively. Provide:\n"
        "- answer_score: Numerical rating from 0 to 100 based on accuracy, depth, structure, and clarity\n"
        "- strengths: List of what the candidate did well\n"
        "- improvement_areas: Specific ways the candidate can enhance their delivery or depth\n"
        "- missing_concepts: Key technical or behavioral principles omitted that top candidates mention\n"
        "- suggested_answer: A top-tier, gold-standard model answer demonstrating ideal pacing and content\n"
        "- feedback: Direct, constructive coaching commentary\n"
        "- practice_tasks: 2-3 specific exercises to master these concepts\n"
        "- next_session_focus: Primary topic or technique to prioritize next"
    )
    return execute_ai_json(
        prompt,
        InterviewAnalysisData,
        session_id=session_id,
        preferred_provider=preferred_provider,
    )



