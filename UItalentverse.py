"""TalentVerse frontend: Streamlit user interface."""
import json
import streamlit as st
from pydantic import ValidationError
from talentverse import (
    DB_PATH, GEMINI_MODEL, CandidateProfile, CareerRoadmap,
    analyze_resume, make_roadmap, match_job, make_project_brief,
    analyze_interview, load_db, save_profile,
)

st.set_page_config(
    page_title="TalentVerse | Career Intelligence",
    page_icon="🎯",
    layout="wide",
)

# -------------------------- Display helpers --------------------------

def show_list(title: str, items: list[str]):
    st.markdown(f"**{title}**")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("No items returned.")


def display_profile(profile: CandidateProfile):
    st.subheader("Extracted candidate profile")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {profile.full_name or 'Not provided'}")
        st.markdown(f"**Email:** {profile.email or 'Not provided'}")
        st.markdown(f"**Target role:** {profile.target_role or 'Not provided'}")
        st.markdown(f"**Experience level:** {profile.experience_level}")
    with col2:
        show_list("Skills", profile.skills)
        show_list("Certifications", profile.certifications)
    show_list("Experience", profile.experience)
    show_list("Education", profile.education)
    show_list("Projects", profile.projects)
    if profile.missing_information:
        st.warning("Information to review: " + ", ".join(profile.missing_information))
    st.markdown("**Summary**")
    st.write(profile.summary)
    with st.expander("View structured JSON"):
        st.json(profile.model_dump())


# -------------------------- Main UI --------------------------

st.title("🎯 TalentVerse")
st.caption("Skills & Career Intelligence — turn your experience and goals into a practical career plan.")

with st.sidebar:
    st.header("Workspace")
    st.write("AI provider: **Google Gemini**")
    st.write(f"Model: `{GEMINI_MODEL}`")
    st.write(f"Saved profiles: **{len(load_db())}**")
    st.caption("Review AI-generated information before saving it.")
    if st.button("Refresh saved profiles", use_container_width=True):
        st.rerun()

tabs = st.tabs([
    "Resume Analyzer",
    "Career Roadmap",
    "Job Matcher",
    "Project Brief",
    "Interview Coach",
    "Saved Profiles",
])

# Resume Analyzer
with tabs[0]:
    st.subheader("Analyze a resume")
    st.write("Paste resume text to extract a structured candidate profile. Do not paste sensitive information you do not want processed.")
    resume_text = st.text_area(
        "Resume text",
        height=220,
        placeholder="Paste the resume text here...",
        key="resume_input",
    )
    if st.button("Analyze Resume", type="primary", key="analyze_resume_btn"):
        if len(resume_text.strip()) < 30:
            st.error("Please enter at least 30 characters of resume text.")
        else:
            with st.spinner("Analyzing resume with Gemini..."):
                try:
                    st.session_state["last_profile"] = analyze_resume(resume_text.strip())
                    st.success("Resume analysis completed. Review the extracted fields before saving.")
                except Exception as exc:
                    st.error(f"Resume analysis failed: {exc}")
    current_profile = st.session_state.get("last_profile")
    if current_profile:
        display_profile(current_profile)
        st.divider()
        st.subheader("Save profile")
        st.caption("Saving requires explicit confirmation. If the profile has an email already in the database, that record will be updated.")
        confirmed = st.checkbox("I reviewed this profile and confirm that it can be saved.", key="confirm_profile_save")
        if st.button("Save / Update Profile", disabled=not confirmed, key="save_profile_btn"):
            try:
                record_id, action = save_profile(current_profile)
                st.success(f"Profile {action} successfully. Record ID: {record_id}")
            except Exception as exc:
                st.error(f"Could not save profile: {exc}")

# Career Roadmap
with tabs[1]:
    st.subheader("Build a career roadmap")
    with st.form("roadmap_form"):
        skills_text = st.text_input("Current skills (comma-separated)", placeholder="Python, SQL, Git")
        goal = st.text_input("Career goal", placeholder="Become a machine learning engineer")
        level = st.selectbox("Experience level", ["Student", "Entry-level", "Junior", "Mid-level", "Senior"])
        weeks = st.slider("Plan duration (weeks)", min_value=2, max_value=24, value=8)
        roadmap_submit = st.form_submit_button("Generate Roadmap", type="primary")
    if roadmap_submit:
        skills = [x.strip() for x in skills_text.split(",") if x.strip()]
        if not skills or not goal.strip():
            st.error("Enter at least one current skill and a career goal.")
        else:
            with st.spinner("Creating your skill-gap map and roadmap..."):
                try:
                    roadmap = make_roadmap(skills, goal.strip(), level, weeks)
                    st.session_state["last_roadmap"] = roadmap
                except Exception as exc:
                    st.error(f"Roadmap generation failed: {exc}")
    roadmap = st.session_state.get("last_roadmap")
    if roadmap:
        st.markdown(f"### Roadmap for: {roadmap.career_goal}")
        show_list("Skill gaps", roadmap.skill_gaps)
        for milestone in roadmap.milestones:
            with st.expander(f"Week {milestone.week}: {milestone.title}", expanded=True):
                show_list("Learning tasks", milestone.learning_tasks)
                st.markdown(f"**Deliverable:** {milestone.deliverable}")
                show_list("Success criteria", milestone.success_criteria)
        show_list("Assumptions / missing information", roadmap.assumptions_or_missing_information)
        with st.expander("View roadmap JSON"):
            st.json(roadmap.model_dump())

# Job Matcher
with tabs[2]:
    st.subheader("Match a candidate profile to a job")
    saved_records = load_db()
    profile_options = {
        f"ID {record.get('id')} — {record.get('profile', {}).get('full_name') or 'Unnamed candidate'}": record
        for record in saved_records
    }
    source_choice = st.radio("Candidate profile source", ["Use latest analyzed profile", "Use a saved profile"], horizontal=True)
    selected_profile = None
    if source_choice == "Use latest analyzed profile":
        selected_profile = st.session_state.get("last_profile")
        if selected_profile is None:
            st.info("Analyze a resume in the Resume Analyzer tab first, or choose a saved profile.")
    elif profile_options:
        selected_label = st.selectbox("Saved candidate", list(profile_options.keys()))
        try:
            selected_profile = CandidateProfile.model_validate(profile_options[selected_label]["profile"])
        except ValidationError as exc:
            st.error(f"The saved profile is invalid: {exc}")
    else:
        st.info("No saved profiles yet. Analyze a resume and save the profile first.")

    job_text = st.text_area("Job description", height=180, placeholder="Paste the job description here...", key="job_description")
    if st.button("Compare with Job", type="primary", key="match_job_btn"):
        if selected_profile is None:
            st.error("Select or create a candidate profile first.")
        elif len(job_text.strip()) < 30:
            st.error("Please enter a job description with at least 30 characters.")
        else:
            with st.spinner("Comparing skills and requirements..."):
                try:
                    st.session_state["last_job_match"] = match_job(selected_profile, job_text.strip())
                except Exception as exc:
                    st.error(f"Job matching failed: {exc}")
    result = st.session_state.get("last_job_match")
    if result:
        st.metric("Estimated profile match", f"{result.match_score_percent}%")
        st.progress(result.match_score_percent / 100)
        st.markdown(f"**Target role:** {result.target_role}")
        show_list("Matching skills", result.matching_skills)
        show_list("Missing or unverified skills", result.missing_or_unverified_skills)
        show_list("Evidence considered", result.evidence)
        show_list("Suggested improvements", result.improvement_actions)
        st.caption(result.caveat)
        with st.expander("View match JSON"):
            st.json(result.model_dump())

# Project Brief
with tabs[3]:
    st.subheader("Generate a portfolio project brief")
    with st.form("project_form"):
        interests = st.text_area("Interests / problem areas", placeholder="I like AI, education, and productivity tools.")
        skills_for_project = st.text_input("Current skills (comma-separated)", placeholder="Python, Flask, SQL")
        domain = st.text_input("Preferred domain (optional)", placeholder="Healthcare, education, cybersecurity...")
        project_submit = st.form_submit_button("Generate Project Brief", type="primary")
    if project_submit:
        skills = [x.strip() for x in skills_for_project.split(",") if x.strip()]
        if not interests.strip() or not skills:
            st.error("Enter your interests and at least one skill.")
        else:
            with st.spinner("Designing your portfolio project..."):
                try:
                    st.session_state["last_project_brief"] = make_project_brief(interests.strip(), skills, domain.strip())
                except Exception as exc:
                    st.error(f"Project brief generation failed: {exc}")
    project = st.session_state.get("last_project_brief")
    if project:
        st.markdown(f"### {project.title}")
        st.write(project.problem_statement)
        show_list("Target users", project.target_users)
        show_list("Core features", project.core_features)
        show_list("Suggested tech stack", project.suggested_tech_stack)
        show_list("Implementation milestones", project.implementation_milestones)
        show_list("Evaluation metrics", project.evaluation_metrics)
        with st.expander("View project JSON"):
            st.json(project.model_dump())

# Interview Coach
with tabs[4]:
    st.subheader("Turn interview notes into a practice plan")
    notes = st.text_area(
        "Interview practice notes",
        height=200,
        placeholder="Paste notes about answers you gave, questions you found difficult, or feedback you received.",
        key="interview_notes",
    )
    if st.button("Analyze Interview Notes", type="primary", key="analyze_interview_btn"):
        if len(notes.strip()) < 10:
            st.error("Please enter at least 10 characters of interview notes.")
        else:
            with st.spinner("Reviewing your practice notes..."):
                try:
                    st.session_state["last_interview_analysis"] = analyze_interview(notes.strip())
                except Exception as exc:
                    st.error(f"Interview analysis failed: {exc}")
    interview = st.session_state.get("last_interview_analysis")
    if interview:
        show_list("Strengths", interview.strengths)
        show_list("Improvement areas", interview.improvement_areas)
        show_list("Next practice tasks", interview.practice_tasks)
        st.markdown("**Focus for next session**")
        st.write(interview.next_session_focus)
        with st.expander("View interview analysis JSON"):
            st.json(interview.model_dump())

# Saved Profiles
with tabs[5]:
    st.subheader("Saved candidate profiles")
    records = load_db()
    if not records:
        st.info("No profiles saved yet. Analyze a resume, review the extracted fields, and save the profile.")
    else:
        st.write(f"{len(records)} profile(s) stored in `{DB_PATH}`.")
        for record in records:
            profile_data = record.get("profile", {})
            name = profile_data.get("full_name") or "Unnamed candidate"
            with st.expander(f"ID {record.get('id')} — {name}"):
                st.write(f"**Email:** {profile_data.get('email') or 'Not provided'}")
                st.write(f"**Target role:** {profile_data.get('target_role') or 'Not provided'}")
                st.write(f"**Created:** {record.get('created_at', 'Unknown')}")
                st.write(f"**Updated:** {record.get('updated_at', 'Unknown')}")
                st.json(profile_data)
        st.download_button(
            "Download profile database JSON",
            data=json.dumps(records, indent=2, ensure_ascii=False),
            file_name="talentverse_profiles_export.json",
            mime="application/json",
        )

st.divider()
st.caption("TalentVerse is an AI-assisted career tool. Review generated content before using it in applications or interviews.")
