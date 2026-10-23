"""TalentVerse backend: schemas, Gemini integration, and JSON persistence."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import streamlit as st

from dotenv import load_dotenv
from pydantic import BaseModel, Field, EmailStr, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
DB_PATH = Path(os.getenv("TALENTVERSE_DB_PATH", "talentverse_profiles.json"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

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



# -------------------------- JSON database --------------------------

def load_db() -> list[dict]:
    if not DB_PATH.exists():
        return []
    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"The profile database file could not be read: {DB_PATH}. "
            "Back it up before replacing it."
        ) from exc


def save_db(profiles: list[dict]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = DB_PATH.with_suffix(DB_PATH.suffix + ".tmp")
    temp_path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(DB_PATH)


def save_profile(profile: CandidateProfile) -> tuple[str, str]:
    profiles = load_db()
    profile_data = profile.model_dump()
    email = (profile.email or "").strip().lower()
    now = datetime.now().isoformat(timespec="seconds")

    # Update existing record by email if an email was provided.
    if email:
        for record in profiles:
            if (record.get("profile", {}).get("email") or "").strip().lower() == email:
                record["profile"] = profile_data
                record["updated_at"] = now
                save_db(profiles)
                return str(record["id"]), "updated"

    record_id = str(max([int(p.get("id", 0)) for p in profiles] + [0]) + 1)
    profiles.append({
        "id": record_id,
        "profile": profile_data,
        "created_at": now,
        "updated_at": now,
    })
    save_db(profiles)
    return record_id, "created"



# -------------------------- AI integration --------------------------

@st.cache_resource
def get_model():
    # Supports either common environment variable name for a Gemini API key.
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Google Gemini API key is missing. Add GOOGLE_API_KEY or GEMINI_API_KEY "
            "to your .env file and restart Streamlit."
        )
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.1,
        google_api_key=api_key,
    )


def run_structured_ai(system_text: str, user_text: str, values: dict, output_model):
    parser = PydanticOutputParser(pydantic_object=output_model)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            system_text + "\n\nReturn output in this exact schema:\n{format_instructions}",
        ),
        ("human", user_text),
    ])
    chain = prompt | get_model() | parser
    return chain.invoke({
        **values,
        "format_instructions": parser.get_format_instructions(),
    })


def analyze_resume(resume_text: str) -> CandidateProfile:
    return run_structured_ai(
        "You extract career information from resume text. Use only facts supported by the text. "
        "Never invent names, dates, skills, employers, degrees, or certifications. Put absent important "
        "fields in missing_information. If a field is absent, use null or an empty list.",
        "Extract the candidate profile from this resume:\n\n{resume_text}",
        {"resume_text": resume_text},
        CandidateProfile,
    )


def make_roadmap(skills: list[str], goal: str, level: str, weeks: int) -> CareerRoadmap:
    return run_structured_ai(
        "You are a practical career learning coach. Create achievable milestones. Identify skill gaps "
        "based on the supplied current skills and goal. Do not claim the user already knows skills not listed. "
        "Keep the plan within the requested duration and state assumptions.",
        "Current skills: {skills}\nCareer goal: {goal}\nExperience level: {level}\nDuration: {weeks} weeks.\n"
        "Create a skill-gap map and milestone learning plan.",
        {"skills": skills, "goal": goal, "level": level, "weeks": weeks},
        CareerRoadmap,
    )


def match_job(profile: CandidateProfile, job_description: str) -> JobMatch:
    return run_structured_ai(
        "Compare the candidate profile with the job description using only supplied evidence. "
        "Distinguish missing skills from skills that are merely unverified. The score is a rough fit estimate, "
        "not a probability of getting hired.",
        "Candidate profile:\n{profile}\n\nJob description:\n{job_description}\n\nCompare them.",
        {"profile": profile.model_dump_json(), "job_description": job_description},
        JobMatch,
    )


def make_project_brief(interests: str, skills: list[str], domain: str) -> ProjectBrief:
    return run_structured_ai(
        "You are a portfolio project mentor. Suggest a feasible project suitable for the listed skills. "
        "Include practical milestones and measurable evaluation metrics.",
        "Interests: {interests}\nSkills: {skills}\nPreferred domain: {domain}\nCreate a project brief.",
        {"interests": interests, "skills": skills, "domain": domain or "Not specified"},
        ProjectBrief,
    )


def analyze_interview(notes: str) -> InterviewAnalysis:
    return run_structured_ai(
        "You are an interview practice coach. Give constructive feedback based only on the notes. "
        "Do not infer personal traits or make unsupported claims.",
        "Analyze these interview practice notes:\n{notes}\nIdentify strengths, improvement areas, practice tasks, "
        "and a focus for the next session.",
        {"notes": notes},
        InterviewAnalysis,
    )


