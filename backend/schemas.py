"""Pydantic schemas for request and response validation."""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator


AIProviderName = Literal["groq", "gemini", "openai", "mistral"]


# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "candidate"
    is_demo: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ResumeExperienceAnalysis(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    missing_measurable_results: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ResumeEducationAnalysis(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None


class ResumeProjectAnalysis(BaseModel):
    name: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ResumeAnalysisDetails(BaseModel):
    current_role: Optional[str] = None
    total_experience: Optional[str] = None
    summary_quality_analysis: str = ""
    summary_improvement_suggestions: List[str] = Field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    target_role_skill_alignment: List[str] = Field(default_factory=list)
    experience_analysis: List[ResumeExperienceAnalysis] = Field(default_factory=list)
    education_analysis: List[ResumeEducationAnalysis] = Field(default_factory=list)
    projects_analysis: List[ResumeProjectAnalysis] = Field(default_factory=list)
    project_improvement_suggestions: List[str] = Field(default_factory=list)
    ats_score: Optional[int] = Field(default=None, ge=0, le=100)
    ats_score_explanation: str = ""
    ats_matched_keywords: List[str] = Field(default_factory=list)
    ats_missing_keywords: List[str] = Field(default_factory=list)
    ats_formatting_issues: List[str] = Field(default_factory=list)
    ats_section_completeness: Dict[str, bool] = Field(default_factory=dict)


# Candidate Profile schemas
class CandidateProfileData(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: str = "Entry-level"
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvement_recommendations: List[str] = Field(default_factory=list)
    readiness_score: int = Field(default=0, ge=0, le=100)
    current_role: Optional[str] = None
    total_experience: Optional[str] = None
    summary_quality_analysis: str = ""
    summary_improvement_suggestions: List[str] = Field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    target_role_skill_alignment: List[str] = Field(default_factory=list)
    experience_analysis: List[ResumeExperienceAnalysis] = Field(default_factory=list)
    education_analysis: List[ResumeEducationAnalysis] = Field(default_factory=list)
    projects_analysis: List[ResumeProjectAnalysis] = Field(default_factory=list)
    project_improvement_suggestions: List[str] = Field(default_factory=list)
    ats_score: Optional[int] = Field(default=None, ge=0, le=100)
    ats_score_explanation: str = ""
    ats_matched_keywords: List[str] = Field(default_factory=list)
    ats_missing_keywords: List[str] = Field(default_factory=list)
    ats_formatting_issues: List[str] = Field(default_factory=list)
    ats_section_completeness: Dict[str, bool] = Field(default_factory=dict)


class CandidateProfileOut(CandidateProfileData):
    id: str
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resume_analysis: ResumeAnalysisDetails = Field(default_factory=ResumeAnalysisDetails)

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisProfile(CandidateProfileData):
    resume_analysis: ResumeAnalysisDetails = Field(default_factory=ResumeAnalysisDetails)


class CandidateProfileUpdate(CandidateProfileData):
    resume_analysis: Optional[ResumeAnalysisDetails] = None
    replace_resume_analysis: bool = False


# Resume Analyzer schemas
class ResumeAnalysisRequest(BaseModel):
    resume_text: str = Field(min_length=30)
    preferred_provider: Optional[AIProviderName] = None
    replace_profile: bool = False

    @field_validator("resume_text")
    @classmethod
    def require_readable_resume_text(cls, value: str) -> str:
        if len(value.strip()) < 30:
            raise ValueError("Resume text must contain at least 30 readable characters.")
        return value


class ResumeAnalysisResponse(BaseModel):
    profile: ResumeAnalysisProfile
    raw_text: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    provider_used: Optional[str] = None
    model_used: Optional[str] = None


# Career Roadmap schemas
class MilestoneItem(BaseModel):
    week: int
    title: str
    learning_tasks: List[str] = Field(default_factory=list)
    deliverable: str
    success_criteria: List[str] = Field(default_factory=list)
    completed: bool = False


class RoadmapGenerateRequest(BaseModel):
    skills: List[str]
    career_goal: str = Field(min_length=3)
    experience_level: str = "Student"
    duration_weeks: int = Field(default=8, ge=2, le=52)
    preferred_provider: Optional[AIProviderName] = None


class CareerRoadmapData(BaseModel):
    career_goal: str
    experience_level: str = "Student"
    duration_weeks: int = 8
    skill_gaps: List[str] = Field(default_factory=list)
    milestones: List[MilestoneItem] = Field(default_factory=list)
    assumptions_or_missing_information: List[str] = Field(default_factory=list)
    recommended_resources: List[Dict[str, str]] = Field(default_factory=list)
    progress_percent: int = 0


class RoadmapOut(CareerRoadmapData):
    id: str
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MilestoneToggleRequest(BaseModel):
    week: int
    completed: bool


# Job Matcher schemas
class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=25)
    target_role: Optional[str] = None
    company: Optional[str] = None
    profile_id: Optional[str] = None
    custom_profile: Optional[CandidateProfileData] = None
    preferred_provider: Optional[AIProviderName] = None


class JobMatchData(BaseModel):
    target_role: str
    company: Optional[str] = None
    match_score_percent: int = Field(ge=0, le=100)
    matching_skills: List[str] = Field(default_factory=list)
    missing_or_unverified_skills: List[str] = Field(default_factory=list)
    experience_relevance: List[str] = Field(default_factory=list)
    education_relevance: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    improvement_actions: List[str] = Field(default_factory=list)
    caveat: str = "AI-generated estimate, not a hiring decision."


class JobMatchOut(JobMatchData):
    id: str
    user_id: Optional[str] = None
    job_description: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Project Recommendations schemas
class ProjectGenerateRequest(BaseModel):
    interests: str = Field(min_length=5)
    skills: List[str] = Field(default_factory=list)
    domain: Optional[str] = "General"
    difficulty: Optional[str] = "Intermediate"
    preferred_provider: Optional[AIProviderName] = None


class ProjectBriefData(BaseModel):
    title: str
    problem_statement: str
    domain: str = "General"
    difficulty: str = "Intermediate"
    target_users: List[str] = Field(default_factory=list)
    core_features: List[str] = Field(default_factory=list)
    suggested_tech_stack: List[str] = Field(default_factory=list)
    implementation_milestones: List[str] = Field(default_factory=list)
    evaluation_metrics: List[str] = Field(default_factory=list)
    portfolio_description: Optional[str] = None


class ProjectBriefOut(ProjectBriefData):
    id: str
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Interview Coach schemas
class InterviewQuestionRequest(BaseModel):
    target_role: str = Field(min_length=2)
    interview_type: str = "technical"  # technical or behavioral
    level: str = "Entry-level"
    preferred_provider: Optional[AIProviderName] = None


class InterviewQuestionItem(BaseModel):
    id: str
    question: str
    type: str
    difficulty: str
    key_topics: List[str] = Field(default_factory=list)
    tips: Optional[str] = None


class InterviewQuestionsResponse(BaseModel):
    target_role: str
    questions: List[InterviewQuestionItem]


class InterviewEvaluateRequest(BaseModel):
    target_role: str
    interview_type: str = "technical"
    question: str
    user_answer: str = Field(min_length=5)
    preferred_provider: Optional[AIProviderName] = None


class InterviewAnalysisData(BaseModel):
    answer_score: int = Field(ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    suggested_answer: str
    feedback: str
    practice_tasks: List[str] = Field(default_factory=list)
    next_session_focus: str


class InterviewOut(InterviewAnalysisData):
    id: str
    user_id: Optional[str] = None
    target_role: str
    interview_type: str
    question: str
    user_answer: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Saved Reports
class SavedReportCreate(BaseModel):
    report_type: str
    title: str
    summary: Optional[str] = None
    score: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    data: Dict[str, Any]


class SavedReportOut(BaseModel):
    id: str
    report_type: str
    title: str
    summary: Optional[str] = None
    score: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    data: Dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Analytics & Dashboard
class SkillDistributionItem(BaseModel):
    category: str
    name: str
    type: str   # technical / soft


class RecentActivityItem(BaseModel):
    id: str
    type: str  # resume, roadmap, job_match, project, interview
    title: str
    description: str
    timestamp: datetime
    score: Optional[int] = None


class DashboardStatsOut(BaseModel):
    candidate_name: str
    target_role: str
    career_readiness_score: int
    skills_count: int
    completed_milestones: int
    total_milestones: int
    recent_job_fit_score: Optional[int] = None
    skills_distribution: List[SkillDistributionItem]
    recent_activities: List[RecentActivityItem]
    recommended_actions: List[Dict[str, str]]


# System & AI Provider schemas
class ProviderInfo(BaseModel):
    name: str
    model: str
    configured: bool
    key_name: str


class SystemStatusOut(BaseModel):
    priority: List[str]
    providers: List[ProviderInfo]
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    status: str = "operational"
