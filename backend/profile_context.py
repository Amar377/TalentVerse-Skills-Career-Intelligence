"""Build a minimal, non-contact candidate context for AI feature prompts."""
from typing import Optional

from backend.database import CandidateProfileModel


def build_candidate_context(profile: Optional[CandidateProfileModel]) -> Optional[str]:
    if profile is None:
        return None

    sections = []
    if profile.target_role:
        sections.append(f"Career target: {profile.target_role}")
    if profile.summary:
        sections.append(f"Professional summary: {profile.summary[:1200]}")

    for label, values in (
        ("Demonstrated skills", profile.skills),
        ("Education", profile.education),
        ("Certifications", profile.certifications),
        ("Experience", profile.experience),
        ("Projects", profile.projects),
    ):
        cleaned = [str(value).strip()[:500] for value in (values or []) if str(value).strip()]
        if cleaned:
            sections.append(f"{label}: " + " | ".join(cleaned[:10]))

    return "\n".join(sections)[:5000] or None
