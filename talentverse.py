"""TalentVerse backend: configurable multi-provider AI, schemas, and demo-safe request limits."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import date
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv(override=False)


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip().lower() for item in os.getenv(name, default).split(",") if item.strip()]


# Provider priority is controlled entirely through .env. The first configured provider is tried first.
AI_PROVIDER_ORDER = _csv_env("AI_PROVIDER_ORDER", "groq,gemini,openai,mistral")
PROVIDER_MODELS = {
    "groq": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "gemini": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "mistral": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
}
PROVIDER_ENV_KEYS = {
    "groq": "GROQ_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

SESSION_DAILY_LIMIT = max(1, int(os.getenv("TALENTVERSE_SESSION_DAILY_LIMIT", "10")))
GLOBAL_DAILY_LIMIT = max(1, int(os.getenv("TALENTVERSE_GLOBAL_DAILY_LIMIT", "100")))
DUPLICATE_COOLDOWN_SECONDS = max(5, int(os.getenv("TALENTVERSE_DUPLICATE_COOLDOWN_SECONDS", "20")))

_rate_lock = threading.Lock()
_usage_day = date.today()
_session_usage: dict[str, int] = {}
_global_usage = 0
_recent_requests: dict[tuple[str, str], float] = {}


class RateLimitError(RuntimeError):
    """Raised when a demo request limit or duplicate-submit guard is reached."""


# -------------------------- Pydantic schemas --------------------------

class CandidateProfile(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: str = "unknown"
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    summary: str


class Milestone(BaseModel):
    week: int
    title: str
    learning_tasks: list[str] = Field(default_factory=list)
    deliverable: str
    success_criteria: list[str] = Field(default_factory=list)


class CareerRoadmap(BaseModel):
    career_goal: str
    skill_gaps: list[str] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    assumptions_or_missing_information: list[str] = Field(default_factory=list)


class JobMatch(BaseModel):
    target_role: str
    match_score_percent: int = Field(ge=0, le=100)
    matching_skills: list[str] = Field(default_factory=list)
    missing_or_unverified_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    improvement_actions: list[str] = Field(default_factory=list)
    caveat: str = "AI-generated estimate, not a hiring decision."


class ProjectBrief(BaseModel):
    title: str
    problem_statement: str
    target_users: list[str] = Field(default_factory=list)
    core_features: list[str] = Field(default_factory=list)
    suggested_tech_stack: list[str] = Field(default_factory=list)
    implementation_milestones: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)


class InterviewAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    practice_tasks: list[str] = Field(default_factory=list)
    next_session_focus: str


# -------------------------- Provider configuration --------------------------

def provider_status() -> dict:
    """Safe provider status for UI display; never returns secret values."""
    return {
        "priority": AI_PROVIDER_ORDER,
        "providers": [
            {
                "name": provider,
                "model": PROVIDER_MODELS.get(provider, "unknown"),
                "configured": bool(os.getenv(PROVIDER_ENV_KEYS.get(provider, ""))),
                "key_name": PROVIDER_ENV_KEYS.get(provider, ""),
            }
            for provider in AI_PROVIDER_ORDER
        ],
    }


def configured_providers() -> list[str]:
    return [
        provider for provider in AI_PROVIDER_ORDER
        if provider in PROVIDER_ENV_KEYS and os.getenv(PROVIDER_ENV_KEYS[provider])
    ]


def _build_model(provider: str):
    """Load provider integrations lazily so unused providers are optional."""
    model = PROVIDER_MODELS[provider]
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model, api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1, timeout=60, max_retries=0,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model, google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1, timeout=60, max_retries=0,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model, api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1, timeout=60, max_retries=0,
        )
    if provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=model, api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.1, timeout=60, max_retries=0,
        )
    raise ValueError(f"Unsupported provider '{provider}'. Supported providers: groq, gemini, openai, mistral.")


# -------------------------- Request protection --------------------------

def _reset_daily_usage_if_needed() -> None:
    global _usage_day, _session_usage, _global_usage, _recent_requests
    today = date.today()
    if today != _usage_day:
        _usage_day = today
        _session_usage = {}
        _global_usage = 0
        _recent_requests = {}


def reserve_ai_request(user_text: str) -> None:
    """Rate-limit attempts to protect free-tier API quotas."""
    global _global_usage
    session_id = str(st.session_state.get("talentverse_session_id", "unknown-session"))
    fingerprint = hashlib.sha256(user_text.encode("utf-8", errors="replace")).hexdigest()
    now = time.monotonic()
    key = (session_id, fingerprint)

    with _rate_lock:
        _reset_daily_usage_if_needed()
        previous = _recent_requests.get(key)
        if previous is not None and now - previous < DUPLICATE_COOLDOWN_SECONDS:
            wait_seconds = max(1, int(DUPLICATE_COOLDOWN_SECONDS - (now - previous)))
            raise RateLimitError(
                f"This request was just submitted. Please wait about {wait_seconds} seconds before trying it again."
            )
        if _session_usage.get(session_id, 0) >= SESSION_DAILY_LIMIT:
            raise RateLimitError(
                f"You've reached the demo limit of {SESSION_DAILY_LIMIT} AI requests for this session today."
            )
        if _global_usage >= GLOBAL_DAILY_LIMIT:
            raise RateLimitError("TalentVerse has reached its shared daily AI demo limit. Please try again tomorrow.")

        _session_usage[session_id] = _session_usage.get(session_id, 0) + 1
        _global_usage += 1
        _recent_requests[key] = now
        cutoff = now - DUPLICATE_COOLDOWN_SECONDS
        for old_key, timestamp in list(_recent_requests.items()):
            if timestamp < cutoff:
                _recent_requests.pop(old_key, None)


def friendly_error_message(exc: Exception) -> str:
    if isinstance(exc, RateLimitError):
        return str(exc)
    message = str(exc).lower()
    if any(term in message for term in ("resource_exhausted", "quota", "rate limit", "429", "too many requests")):
        return "An AI provider's rate limit or quota was reached. TalentVerse tried the configured fallback providers. Check your API quotas or try again later."
    if any(term in message for term in ("api key", "api_key", "unauthorized", "permission denied", "401", "403")):
        return "AI provider authentication failed. Check the API keys in your .env file or hosting secrets."
    if any(term in message for term in ("timeout", "timed out", "connection", "network")):
        return "TalentVerse could not reach an AI provider. Check your connection and try again."
    return f"The AI request could not be completed. Details: {str(exc)[:350]}"


def run_structured_ai(system_text: str, user_text: str, values: dict, output_model):
    """Run a schema-guided prompt, trying configured providers in .env priority order."""
    request_payload = system_text + "\n" + user_text + "\n" + json.dumps(values, sort_keys=True, default=str)
    reserve_ai_request(request_payload)

    candidates = configured_providers()
    if not candidates:
        available = ", ".join(PROVIDER_ENV_KEYS.values())
        raise RuntimeError(
            "No AI provider is configured. Add at least one API key in .env. Supported keys: " + available
        )

    parser = PydanticOutputParser(pydantic_object=output_model)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_text + "\n\nReturn output in this exact schema:\n{format_instructions}"),
        ("human", user_text),
    ])
    failures = []

    for provider in candidates:
        try:
            model = _build_model(provider)
            chain = prompt | model | parser
            result = chain.invoke({**values, "format_instructions": parser.get_format_instructions()})
            # Keep the last successful provider visible in the UI for this session.
            st.session_state["talentverse_last_provider"] = provider
            st.session_state["talentverse_last_model"] = PROVIDER_MODELS[provider]
            return result
        except Exception as exc:
            failures.append(f"{provider} ({PROVIDER_MODELS.get(provider, 'unknown')}): {type(exc).__name__}: {str(exc)[:240]}")
            # Move to the next configured provider without retrying this one.
            continue

    raise RuntimeError("All configured AI providers failed. " + " | ".join(failures))


# -------------------------- Feature workflows --------------------------

def analyze_resume(resume_text: str) -> CandidateProfile:
    return run_structured_ai(
        "You extract career information from resume text. Use only facts supported by the text. "
        "Never invent names, dates, skills, employers, degrees, or certifications. Put absent important "
        "fields in missing_information. If a field is absent, use null or an empty list.",
        "Extract the candidate profile from this resume:\n\n{resume_text}",
        {"resume_text": resume_text}, CandidateProfile,
    )


def make_roadmap(skills: list[str], goal: str, level: str, weeks: int) -> CareerRoadmap:
    return run_structured_ai(
        "You are a practical career learning coach. Create achievable milestones. Identify skill gaps "
        "based on the supplied current skills and goal. Do not claim the user already knows skills not listed. "
        "Keep the plan within the requested duration and state assumptions.",
        "Current skills: {skills}\nCareer goal: {goal}\nExperience level: {level}\nDuration: {weeks} weeks.\n"
        "Create a skill-gap map and milestone learning plan.",
        {"skills": skills, "goal": goal, "level": level, "weeks": weeks}, CareerRoadmap,
    )


def match_job(profile: CandidateProfile, job_description: str) -> JobMatch:
    return run_structured_ai(
        "Compare the candidate profile with the job description using only supplied evidence. "
        "Distinguish missing skills from skills that are merely unverified. The score is a rough fit estimate, "
        "not a probability of getting hired.",
        "Candidate profile:\n{profile}\n\nJob description:\n{job_description}\n\nCompare them.",
        {"profile": profile.model_dump_json(), "job_description": job_description}, JobMatch,
    )


def make_project_brief(interests: str, skills: list[str], domain: str) -> ProjectBrief:
    return run_structured_ai(
        "You are a portfolio project mentor. Suggest a feasible project suitable for the listed skills. "
        "Include practical milestones and measurable evaluation metrics.",
        "Interests: {interests}\nSkills: {skills}\nPreferred domain: {domain}\nCreate a project brief.",
        {"interests": interests, "skills": skills, "domain": domain or "Not specified"}, ProjectBrief,
    )


def analyze_interview(notes: str) -> InterviewAnalysis:
    return run_structured_ai(
        "You are an interview practice coach. Give constructive feedback based only on the notes. "
        "Do not infer personal traits or make unsupported claims.",
        "Analyze these interview practice notes:\n{notes}\nIdentify strengths, improvement areas, practice tasks, "
        "and a focus for the next session.",
        {"notes": notes}, InterviewAnalysis,
    )
