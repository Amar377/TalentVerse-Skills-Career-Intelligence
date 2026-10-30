"""TalentVerse: polished Streamlit interface for AI-powered career intelligence."""
import json
import uuid
from datetime import datetime

import streamlit as st
from pydantic import ValidationError
from talentverse import (
    CandidateProfile, CareerRoadmap, analyze_resume, make_roadmap, match_job,
    make_project_brief, analyze_interview, friendly_error_message,
    provider_status, configured_providers,
)

st.set_page_config(page_title="TalentVerse | Career Intelligence", page_icon="🎯", layout="wide")

st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background: #f5f7fb; }
.block-container { max-width: 1380px; padding-top: 1.4rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#10172d 0%,#202c52 100%); }
[data-testid="stSidebar"] * { color: #f5f7ff; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] code { color: #a5f3fc; background: #26365d; }
.tv-hero { padding: 2.15rem 2.35rem; border-radius: 26px; margin-bottom: 1.3rem; color: white; background: radial-gradient(circle at 85% 15%,rgba(34,211,238,.32),transparent 28%),linear-gradient(120deg,#111827 0%,#3730a3 56%,#0369a1 100%); box-shadow: 0 18px 48px rgba(30,41,99,.17); }
.tv-eyebrow { font-size:.72rem; font-weight:800; letter-spacing:.18em; opacity:.82; }
.tv-hero h1 { color:white; font-size:clamp(2.35rem,4vw,3.4rem); margin:.45rem 0 .25rem; letter-spacing:-.045em; }
.tv-hero h1 span { color:#67e8f9; }
.tv-hero p { color:#e0e7ff; font-size:1.06rem; max-width:800px; }
.tv-chips { display:flex; gap:.5rem; flex-wrap:wrap; margin-top:1rem; }
.tv-chips span { border:1px solid rgba(255,255,255,.25); background:rgba(255,255,255,.1); border-radius:999px; padding:.38rem .72rem; font-size:.78rem; }
[data-testid="stTabs"] [role="tablist"] { gap:.38rem; border-bottom:1px solid #dbe2f0; flex-wrap:wrap; }
[data-testid="stTabs"] button[role="tab"] { border-radius:12px 12px 0 0; padding:.72rem .82rem; font-weight:700; }
[data-testid="stTabs"] button[aria-selected="true"] { background:#e7eafe; color:#3730a3; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:16px; }
.stButton>button,.stFormSubmitButton>button { border-radius:11px; min-height:2.65rem; font-weight:700; border:1px solid #c7d2fe; }
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"] { background:linear-gradient(90deg,#4338ca,#2563eb); border:0; color:white; }
.stButton>button:hover,.stFormSubmitButton>button:hover { transform:translateY(-1px); box-shadow:0 7px 18px rgba(67,56,202,.14); }
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea { border-radius:10px; }
[data-testid="stMetric"] { background:white; padding:1rem; border:1px solid #e2e8f0; border-radius:14px; }
[data-testid="stAlert"] { border-radius:12px; }
hr { border-color:#e2e8f0; }
.tv-section { color:#3730a3; font-weight:800; letter-spacing:.02em; }
@media(max-width:700px){.tv-hero{padding:1.35rem;border-radius:18px}.tv-chips{gap:.35rem}}
</style>
""", unsafe_allow_html=True)

if "talentverse_session_id" not in st.session_state:
    st.session_state["talentverse_session_id"] = uuid.uuid4().hex
if "session_profiles" not in st.session_state:
    st.session_state["session_profiles"] = []


def show_list(title: str, items: list[str]):
    st.markdown(f"**{title}**")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("Nothing to show yet.")


def display_profile(profile: CandidateProfile):
    st.subheader("Candidate profile")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Name:** {profile.full_name or 'Not provided'}")
        st.markdown(f"**Email:** {profile.email or 'Not provided'}")
        st.markdown(f"**Target role:** {profile.target_role or 'Not provided'}")
        st.markdown(f"**Experience level:** {profile.experience_level}")
    with right:
        show_list("Core skills", profile.skills)
        show_list("Certifications", profile.certifications)
    col1, col2 = st.columns(2)
    with col1:
        show_list("Education", profile.education)
        show_list("Projects", profile.projects)
    with col2:
        show_list("Experience", profile.experience)
        show_list("Information to verify", profile.missing_information)
    st.markdown("**Professional summary**")
    st.write(profile.summary)
    with st.expander("View structured profile JSON"):
        st.json(profile.model_dump())


def run_error(label: str, exc: Exception):
    st.error(f"{label}: {friendly_error_message(exc)}")


st.markdown("""
<div class="tv-hero">
  <div class="tv-eyebrow">AI-POWERED CAREER WORKSPACE</div>
  <h1>TalentVerse <span>✦</span></h1>
  <p>Turn your skills, experience, and ambitions into a clearer career direction — with structured insights, practical milestones, and job-readiness guidance.</p>
  <div class="tv-chips"><span>✦ Resume intelligence</span><span>↗ Skill-gap planning</span><span>◎ Job readiness</span><span>⌘ Portfolio building</span></div>
</div>
""", unsafe_allow_html=True)

# Summary cards
status = provider_status()
configured = configured_providers()
last_provider = st.session_state.get("talentverse_last_provider")
last_model = st.session_state.get("talentverse_last_model")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Career workflows", "5", help="Resume analysis, roadmap, job matching, project brief, interview coach.")
with c2:
    st.metric("Configured AI providers", str(len(configured)), help="Provider keys are read from your .env file.")
with c3:
    st.metric("Last successful model", last_model or "Not used yet")

with st.sidebar:
    st.markdown("## 🎯 TalentVerse")
    st.caption("Skills & Career Intelligence")
    st.divider()
    st.markdown("### AI provider status")
    if configured:
        for provider in status["providers"]:
            if provider["configured"]:
                st.success(f'{provider["name"].title()} · {provider["model"]}')
            else:
                st.caption(f'{provider["name"].title()} · not configured')
        st.caption("Fallback order: " + " → ".join(status["priority"]))
    else:
        st.warning("No AI provider configured. Add at least one API key to .env.")
    st.divider()
    st.markdown(f"**Session profiles:** {len(st.session_state['session_profiles'])}")
    st.caption("Demo safeguards are enabled. Profile saves are private to this active browser session.")
    if st.button("Refresh workspace", use_container_width=True):
        st.rerun()

st.info("Privacy reminder: use sample or anonymized resumes. AI-generated career insights should be reviewed before relying on them. Profiles saved here exist only for the active Streamlit session.")

tabs = st.tabs(["📄 Resume Analyzer", "🧭 Career Roadmap", "🎯 Job Matcher", "🧪 Project Brief", "🎤 Interview Coach", "🗂️ Saved Profiles"])

# Resume Analyzer
with tabs[0]:
    st.subheader("Understand your experience")
    st.write("Paste resume text to extract a structured profile with skills, projects, education, experience, and information that may need verification.")
    with st.container(border=True):
        resume_text = st.text_area("Resume text", height=230, placeholder="Paste resume text here…", key="resume_input")
        if st.button("Analyze resume", type="primary", key="analyze_resume_btn", use_container_width=True):
            if len(resume_text.strip()) < 30:
                st.error("Please enter at least 30 characters of resume text.")
            else:
                with st.spinner("Analyzing resume with your configured AI providers…"):
                    try:
                        st.session_state["last_profile"] = analyze_resume(resume_text.strip())
                        st.success(f"Resume analysis completed using {st.session_state.get('talentverse_last_provider', 'an AI provider').title()}. Review the extracted fields before saving.")
                    except Exception as exc:
                        run_error("Resume analysis failed", exc)
    current_profile = st.session_state.get("last_profile")
    if current_profile:
        display_profile(current_profile)
        st.divider()
        st.subheader("Save this profile")
        st.caption("Saving requires explicit confirmation. Data stays in this active Streamlit session.")
        confirmed = st.checkbox("I reviewed this profile and confirm it can be saved.", key="confirm_profile_save")
        if st.button("Save / update profile", disabled=not confirmed, key="save_profile_btn"):
            profiles = st.session_state["session_profiles"]
            profile_data = current_profile.model_dump()
            email = (current_profile.email or "").strip().lower()
            existing_index = next((i for i, item in enumerate(profiles)
                                   if email and (item["profile"].get("email") or "").strip().lower() == email), None)
            now = datetime.now().isoformat(timespec="seconds")
            if existing_index is not None:
                profiles[existing_index]["profile"] = profile_data
                profiles[existing_index]["updated_at"] = now
                record_id, action = profiles[existing_index]["id"], "updated"
            else:
                record_id = str(max([int(item["id"]) for item in profiles] + [0]) + 1)
                profiles.append({"id": record_id, "profile": profile_data, "created_at": now, "updated_at": now})
                st.session_state["session_profiles"] = profiles
                action = "created"
            st.success(f"Profile {action}. Record ID: {record_id}")

# Career Roadmap
with tabs[1]:
    st.subheader("Turn a career goal into a practical plan")
    with st.form("roadmap_form"):
        col1, col2 = st.columns(2)
        with col1:
            skills_text = st.text_input("Current skills (comma-separated)", placeholder="Python, SQL, Git")
            goal = st.text_input("Career goal", placeholder="Become a machine learning engineer")
        with col2:
            level = st.selectbox("Experience level", ["Student", "Entry-level", "Junior", "Mid-level", "Senior"])
            weeks = st.slider("Plan duration", min_value=2, max_value=24, value=8, format="%d weeks")
        roadmap_submit = st.form_submit_button("Generate career roadmap", type="primary", use_container_width=True)
    if roadmap_submit:
        skills = [x.strip() for x in skills_text.split(",") if x.strip()]
        if not skills or not goal.strip():
            st.error("Enter at least one current skill and a career goal.")
        else:
            with st.spinner("Mapping skill gaps and building milestones…"):
                try:
                    st.session_state["last_roadmap"] = make_roadmap(skills, goal.strip(), level, weeks)
                except Exception as exc:
                    run_error("Roadmap generation failed", exc)
    roadmap = st.session_state.get("last_roadmap")
    if roadmap:
        st.markdown(f"### Roadmap: {roadmap.career_goal}")
        show_list("Priority skill gaps", roadmap.skill_gaps)
        for milestone in roadmap.milestones:
            with st.expander(f"Week {milestone.week} · {milestone.title}", expanded=True):
                show_list("Learning tasks", milestone.learning_tasks)
                st.markdown(f"**Deliverable:** {milestone.deliverable}")
                show_list("Success criteria", milestone.success_criteria)
        show_list("Assumptions / missing information", roadmap.assumptions_or_missing_information)
        with st.expander("View roadmap JSON"):
            st.json(roadmap.model_dump())

# Job Matcher
with tabs[2]:
    st.subheader("Compare a candidate with a job opportunity")
    saved_records = st.session_state["session_profiles"]
    profile_options = {
        f"ID {record.get('id')} — {record.get('profile', {}).get('full_name') or 'Unnamed candidate'}": record
        for record in saved_records
    }
    source_choice = st.radio("Candidate profile source", ["Use latest analyzed profile", "Use a saved profile"], horizontal=True)
    selected_profile = None
    if source_choice == "Use latest analyzed profile":
        selected_profile = st.session_state.get("last_profile")
        if selected_profile is None:
            st.info("Analyze a resume first, or choose a saved profile.")
    elif profile_options:
        selected_label = st.selectbox("Saved candidate", list(profile_options.keys()))
        try:
            selected_profile = CandidateProfile.model_validate(profile_options[selected_label]["profile"])
        except ValidationError as exc:
            st.error(f"The saved profile is invalid: {exc}")
    else:
        st.info("No profiles saved in this session yet. Analyze a resume and save it first.")
    job_text = st.text_area("Job description", height=190, placeholder="Paste a job description, required skills, and responsibilities…", key="job_description")
    if st.button("Analyze job match", type="primary", key="match_job_btn", use_container_width=True):
        if selected_profile is None:
            st.error("Select or create a candidate profile first.")
        elif len(job_text.strip()) < 30:
            st.error("Please enter a job description with at least 30 characters.")
        else:
            with st.spinner("Comparing skills and requirements…"):
                try:
                    st.session_state["last_job_match"] = match_job(selected_profile, job_text.strip())
                except Exception as exc:
                    run_error("Job matching failed", exc)
    result = st.session_state.get("last_job_match")
    if result:
        st.metric("Estimated profile match", f"{result.match_score_percent}%")
        st.progress(result.match_score_percent / 100)
        st.markdown(f"**Target role:** {result.target_role}")
        left, right = st.columns(2)
        with left:
            show_list("Matching skills", result.matching_skills)
            show_list("Evidence considered", result.evidence)
        with right:
            show_list("Missing or unverified skills", result.missing_or_unverified_skills)
            show_list("Suggested improvements", result.improvement_actions)
        st.caption(result.caveat)
        with st.expander("View match JSON"):
            st.json(result.model_dump())

# Project Brief
with tabs[3]:
    st.subheader("Design a portfolio project that proves your skills")
    with st.form("project_form"):
        interests = st.text_area("Interests / problem areas", placeholder="I like AI, education, cybersecurity, and productivity tools.")
        col1, col2 = st.columns(2)
        with col1:
            skills_for_project = st.text_input("Current skills (comma-separated)", placeholder="Python, Flask, SQL")
        with col2:
            domain = st.text_input("Preferred domain (optional)", placeholder="Healthcare, education, cybersecurity…")
        project_submit = st.form_submit_button("Generate project brief", type="primary", use_container_width=True)
    if project_submit:
        skills = [x.strip() for x in skills_for_project.split(",") if x.strip()]
        if not interests.strip() or not skills:
            st.error("Enter your interests and at least one skill.")
        else:
            with st.spinner("Designing a practical portfolio project…"):
                try:
                    st.session_state["last_project_brief"] = make_project_brief(interests.strip(), skills, domain.strip())
                except Exception as exc:
                    run_error("Project brief generation failed", exc)
    project = st.session_state.get("last_project_brief")
    if project:
        st.markdown(f"### {project.title}")
        st.write(project.problem_statement)
        col1, col2 = st.columns(2)
        with col1:
            show_list("Target users", project.target_users)
            show_list("Core features", project.core_features)
        with col2:
            show_list("Suggested tech stack", project.suggested_tech_stack)
            show_list("Implementation milestones", project.implementation_milestones)
        show_list("Evaluation metrics", project.evaluation_metrics)
        with st.expander("View project JSON"):
            st.json(project.model_dump())

# Interview Coach
with tabs[4]:
    st.subheader("Convert practice notes into a focused improvement plan")
    notes = st.text_area("Interview practice notes", height=210, placeholder="Describe questions you practised, where you struggled, and any feedback you received.", key="interview_notes")
    if st.button("Analyze interview notes", type="primary", key="analyze_interview_btn", use_container_width=True):
        if len(notes.strip()) < 10:
            st.error("Please enter at least 10 characters of interview notes.")
        else:
            with st.spinner("Reviewing your practice notes…"):
                try:
                    st.session_state["last_interview_analysis"] = analyze_interview(notes.strip())
                except Exception as exc:
                    run_error("Interview analysis failed", exc)
    interview = st.session_state.get("last_interview_analysis")
    if interview:
        col1, col2 = st.columns(2)
        with col1:
            show_list("Strengths", interview.strengths)
            show_list("Improvement areas", interview.improvement_areas)
        with col2:
            show_list("Next practice tasks", interview.practice_tasks)
            st.markdown("**Focus for next session**")
            st.write(interview.next_session_focus)
        with st.expander("View interview analysis JSON"):
            st.json(interview.model_dump())

# Saved Profiles
with tabs[5]:
    st.subheader("Your saved candidate profiles")
    records = st.session_state["session_profiles"]
    st.info("Privacy mode: profiles are stored only in this active Streamlit session. They may disappear when the session ends or the app restarts.")
    if not records:
        st.info("No profiles saved yet. Analyze a resume, review it, and save it.")
    else:
        st.write(f"{len(records)} profile(s) in your current session.")
        for record in records:
            profile_data = record.get("profile", {})
            name = profile_data.get("full_name") or "Unnamed candidate"
            with st.expander(f"ID {record.get('id')} — {name}"):
                st.write(f"**Email:** {profile_data.get('email') or 'Not provided'}")
                st.write(f"**Target role:** {profile_data.get('target_role') or 'Not provided'}")
                st.write(f"**Created:** {record.get('created_at', 'Unknown')}")
                st.write(f"**Updated:** {record.get('updated_at', 'Unknown')}")
                st.json(profile_data)
        st.download_button("Download session profiles JSON", data=json.dumps(records, indent=2, ensure_ascii=False), file_name="talentverse_session_profiles_export.json", mime="application/json")
        if st.button("Clear profiles from this session", type="secondary"):
            st.session_state["session_profiles"] = []
            st.success("Session profiles cleared.")
            st.rerun()

st.divider()
st.caption("TalentVerse is an AI-assisted career tool. Verify generated information before using it in job applications, resumes, or interviews.")
