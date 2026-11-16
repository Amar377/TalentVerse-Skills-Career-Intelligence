import React, { useState, useEffect } from 'react';
import { UserCircle, Save, X, Sparkles, Layers, Briefcase, GraduationCap, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { CandidateProfile, ResumeAnalysisDetails } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input, Textarea } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

const ReadOnlyList: React.FC<{ label: string; items?: string[] }> = ({ label, items = [] }) => {
  if (items.length === 0) return null;

  return (
    <div>
      <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">{label}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
        {items.map((item, index) => <li key={`${label}-${index}`}>{item}</li>)}
      </ul>
    </div>
  );
};

const hasResumeAnalysis = (analysis?: ResumeAnalysisDetails) => {
  if (!analysis) return false;
  return Object.values(analysis).some((value) => {
    if (Array.isArray(value)) return value.length > 0;
    if (value !== null && typeof value === 'object') return Object.keys(value).length > 0;
    if (typeof value === 'string') return value.trim().length > 0;
    return value !== null && value !== undefined;
  });
};

export const ProfilePage: React.FC = () => {
  const { success, error } = useToast();

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Skill input helper
  const [newSkill, setNewSkill] = useState('');
  const [newSoftSkill, setNewSoftSkill] = useState('');

  // Experience input helper
  const [newExp, setNewExp] = useState('');
  const [newEducation, setNewEducation] = useState('');
  const [newCertification, setNewCertification] = useState('');

  // Project input helper
  const [newProj, setNewProj] = useState('');

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await api.profiles.getMyProfile();
        setProfile(data);
      } catch (err) {
        console.error('Failed to load profile', err);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    try {
      const updated = await api.profiles.updateMyProfile({
        full_name: profile.full_name,
        email: profile.email,
        phone: profile.phone,
        location: profile.location,
        target_role: profile.target_role,
        experience_level: profile.experience_level,
        summary: profile.summary,
        skills: profile.skills,
        soft_skills: profile.soft_skills,
        experience: profile.experience,
        education: profile.education,
        certifications: profile.certifications,
        projects: profile.projects,
      });
      setProfile(updated);
      success('Profile Saved', 'Your master candidate profile has been updated.');
    } catch (err: any) {
      error('Save Failed', err.message || 'Could not update profile.');
    } finally {
      setSaving(false);
    }
  };

  const addSkill = () => {
    if (!newSkill.trim() || !profile) return;
    if (!profile.skills.includes(newSkill.trim())) {
      setProfile({ ...profile, skills: [...profile.skills, newSkill.trim()] });
    }
    setNewSkill('');
  };

  const removeSkill = (skillToRemove: string) => {
    if (!profile) return;
    setProfile({
      ...profile,
      skills: profile.skills.filter((s) => s !== skillToRemove),
    });
  };

  const addSoftSkill = () => {
    if (!newSoftSkill.trim() || !profile) return;
    if (!profile.soft_skills.includes(newSoftSkill.trim())) {
      setProfile({ ...profile, soft_skills: [...profile.soft_skills, newSoftSkill.trim()] });
    }
    setNewSoftSkill('');
  };

  const removeSoftSkill = (skillToRemove: string) => {
    if (!profile) return;
    setProfile({
      ...profile,
      soft_skills: profile.soft_skills.filter((s) => s !== skillToRemove),
    });
  };

  const addExperience = () => {
    if (!newExp.trim() || !profile) return;
    setProfile({ ...profile, experience: [...profile.experience, newExp.trim()] });
    setNewExp('');
  };

  const removeExperience = (index: number) => {
    if (!profile) return;
    setProfile({
      ...profile,
      experience: profile.experience.filter((_, i) => i !== index),
    });
  };

  const addEducation = () => {
    if (!newEducation.trim() || !profile) return;
    setProfile({ ...profile, education: [...profile.education, newEducation.trim()] });
    setNewEducation('');
  };

  const removeEducation = (index: number) => {
    if (!profile) return;
    setProfile({ ...profile, education: profile.education.filter((_, i) => i !== index) });
  };

  const addCertification = () => {
    if (!newCertification.trim() || !profile) return;
    setProfile({ ...profile, certifications: [...profile.certifications, newCertification.trim()] });
    setNewCertification('');
  };

  const removeCertification = (index: number) => {
    if (!profile) return;
    setProfile({ ...profile, certifications: profile.certifications.filter((_, i) => i !== index) });
  };

  const addProject = () => {
    if (!newProj.trim() || !profile) return;
    setProfile({ ...profile, projects: [...profile.projects, newProj.trim()] });
    setNewProj('');
  };

  const removeProject = (index: number) => {
    if (!profile) return;
    setProfile({
      ...profile,
      projects: profile.projects.filter((_, i) => i !== index),
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!profile) return null;

  const analysis = profile.resume_analysis;

  return (
    <form onSubmit={handleSave} className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Candidate Master Profile
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Maintain your verified candidate profile used across all AI roadmap, job matching, and interview simulations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Readiness Score
            </span>
            <span className="text-lg font-black text-brand-600 dark:text-brand-400">
              {profile.readiness_score}%
            </span>
          </div>

          <Button
            type="submit"
            variant="gradient"
            isLoading={saving}
            leftIcon={<Save className="w-4 h-4" />}
          >
            Save Changes
          </Button>
        </div>
      </div>

      {/* 1. Basic Credentials */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UserCircle className="w-4 h-4 text-brand-500" /> Identity & Career Positioning
          </CardTitle>
          <CardDescription>Primary candidate contact and positioning attributes.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Input
                label="Full Name"
                value={profile.full_name || ''}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                required
              />
            </div>
            <div>
              <Input
                label="Email Address"
                value={profile.email || ''}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                required
              />
            </div>
            <div>
              <Input
                label="Phone Number"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              />
            </div>
            <div>
              <Input
                label="Location"
                value={profile.location || ''}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Input
                label="Target Role"
                value={profile.target_role || ''}
                onChange={(e) => setProfile({ ...profile, target_role: e.target.value })}
                placeholder="e.g. Full Stack AI Engineer"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Experience Level
              </label>
              <select
                value={profile.experience_level}
                onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              >
                <option value="Student">Student</option>
                <option value="Entry-level">Entry-level</option>
                <option value="Junior">Junior</option>
                <option value="Mid-level">Mid-level</option>
                <option value="Senior">Senior</option>
              </select>
            </div>
          </div>

          <div>
            <Textarea
              label="Professional Summary"
              value={profile.summary || ''}
              onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
              rows={4}
              placeholder="Highlight your background, core technical focus, and primary career objectives..."
            />
          </div>
        </CardContent>
      </Card>

      {/* 2. Skills Manager */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Technical Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-500" /> Technical Skills ({profile.skills.length})
            </CardTitle>
            <CardDescription>Add or remove verified technical proficiencies.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Add skill (e.g. Docker, GraphQL)"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addSkill();
                  }
                }}
              />
              <Button type="button" onClick={addSkill} variant="secondary" size="sm">
                Add
              </Button>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              {profile.skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-50 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300 text-xs font-semibold border border-brand-200/80 dark:border-brand-800/80"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => removeSkill(skill)}
                    className="hover:text-rose-500 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Soft Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-500" /> Soft & Professional Skills ({profile.soft_skills.length})
            </CardTitle>
            <CardDescription>Collaborative and architectural strengths.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Add skill (e.g. System Design, Agile)"
                value={newSoftSkill}
                onChange={(e) => setNewSoftSkill(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addSoftSkill();
                  }
                }}
              />
              <Button type="button" onClick={addSoftSkill} variant="secondary" size="sm">
                Add
              </Button>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              {profile.soft_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/70 text-cyan-700 dark:text-cyan-300 text-xs font-semibold border border-cyan-200/80 dark:border-cyan-800/80"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => removeSoftSkill(skill)}
                    className="hover:text-rose-500 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 3. Experience & Projects */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Experience */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-brand-500" /> Work Experience ({profile.experience.length})
            </CardTitle>
            <CardDescription>Chronological roles and engineering internships.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Company, Role, & key accomplishment"
                value={newExp}
                onChange={(e) => setNewExp(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addExperience();
                  }
                }}
              />
              <Button type="button" onClick={addExperience} variant="secondary" size="sm">
                Add
              </Button>
            </div>

            <div className="space-y-2 pt-2">
              {profile.experience.map((exp, idx) => (
                <div
                  key={idx}
                  className="flex items-start justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-navy-950/60 border border-slate-200/60 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300"
                >
                  <span className="leading-relaxed">{exp}</span>
                  <button
                    type="button"
                    onClick={() => removeExperience(idx)}
                    className="text-slate-400 hover:text-rose-500 transition-colors shrink-0 p-1"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Projects */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-500" /> Verified Projects ({profile.projects.length})
            </CardTitle>
            <CardDescription>Portfolio applications and open source contributions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Project title: What it does & tech used"
                value={newProj}
                onChange={(e) => setNewProj(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addProject();
                  }
                }}
              />
              <Button type="button" onClick={addProject} variant="secondary" size="sm">
                Add
              </Button>
            </div>

            <div className="space-y-2 pt-2">
              {profile.projects.map((proj, idx) => (
                <div
                  key={idx}
                  className="flex items-start justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-navy-950/60 border border-slate-200/60 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300"
                >
                  <span className="leading-relaxed">{proj}</span>
                  <button
                    type="button"
                    onClick={() => removeProject(idx)}
                    className="text-slate-400 hover:text-rose-500 transition-colors shrink-0 p-1"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4. Education & Certifications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-indigo-500" /> Education ({profile.education.length})
            </CardTitle>
            <CardDescription>Edit the education details extracted from your resume.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Degree, institution, graduation year"
                value={newEducation}
                onChange={(e) => setNewEducation(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addEducation();
                  }
                }}
              />
              <Button type="button" onClick={addEducation} variant="secondary" size="sm">Add</Button>
            </div>
            <div className="space-y-2">
              {profile.education.map((education, index) => (
                <div key={`${education.slice(0, 40)}-${index}`} className="flex items-start justify-between gap-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-700 dark:bg-navy-950/60 dark:text-slate-300">
                  <span>{education}</span>
                  <button type="button" aria-label={`Remove education ${index + 1}`} onClick={() => removeEducation(index)} className="text-slate-400 hover:text-rose-500">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Certifications ({profile.certifications.length})
            </CardTitle>
            <CardDescription>Edit certifications and issuing organizations.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Certification and issuing organization"
                value={newCertification}
                onChange={(e) => setNewCertification(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addCertification();
                  }
                }}
              />
              <Button type="button" onClick={addCertification} variant="secondary" size="sm">Add</Button>
            </div>
            <div className="space-y-2">
              {profile.certifications.map((certification, index) => (
                <div key={`${certification.slice(0, 40)}-${index}`} className="flex items-start justify-between gap-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-700 dark:bg-navy-950/60 dark:text-slate-300">
                  <span>{certification}</span>
                  <button type="button" aria-label={`Remove certification ${index + 1}`} onClick={() => removeCertification(index)} className="text-slate-400 hover:text-rose-500">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Saved Resume Analysis</CardTitle>
          <CardDescription>
            AI-generated analysis is read-only here. Edit your verified profile information in the sections above.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!hasResumeAnalysis(analysis) ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No resume analysis has been saved yet. Analyze a resume to see ATS and section-level feedback here.
            </p>
          ) : (
            <>
              {(analysis?.current_role || analysis?.total_experience) && (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {analysis.current_role && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">Current Role</h4>
                      <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">{analysis.current_role}</p>
                    </div>
                  )}
                  {analysis.total_experience && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">Total Experience</h4>
                      <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">{analysis.total_experience}</p>
                    </div>
                  )}
                </div>
              )}

              {analysis?.ats_score != null && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                    ATS Readiness Estimate: {analysis.ats_score}/100
                  </h4>
                  {analysis.ats_score_explanation && (
                    <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{analysis.ats_score_explanation}</p>
                  )}
                </div>
              )}

              {analysis?.summary_quality_analysis && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">Summary Assessment</h4>
                  <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{analysis.summary_quality_analysis}</p>
                </div>
              )}
              <ReadOnlyList label="Summary Improvement Suggestions" items={analysis?.summary_improvement_suggestions} />
              <ReadOnlyList label="Target-Role Skill Alignment" items={analysis?.target_role_skill_alignment} />
              <ReadOnlyList label="Project Improvement Suggestions" items={analysis?.project_improvement_suggestions} />

              {Object.entries(analysis?.skills_by_category ?? {}).map(([category, skills]) => (
                <ReadOnlyList key={category} label={`${category} Skills`} items={skills} />
              ))}

              {(analysis?.experience_analysis ?? []).map((item, index) => (
                <section key={`${item.company ?? ''}-${item.job_title ?? ''}-${index}`} className="space-y-2 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    {[item.job_title, item.company, item.duration].filter(Boolean).join(' · ') || `Experience ${index + 1}`}
                  </h4>
                  <ReadOnlyList label="Responsibilities" items={item.responsibilities} />
                  <ReadOnlyList label="Achievements" items={item.achievements} />
                  <ReadOnlyList label="Missing Measurable Results" items={item.missing_measurable_results} />
                  <ReadOnlyList label="Suggestions" items={item.suggestions} />
                </section>
              ))}

              {(analysis?.education_analysis ?? []).length > 0 && (
                <section className="space-y-2 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Education Analysis</h4>
                  {(analysis?.education_analysis ?? []).map((item, index) => (
                    <p key={`${item.institution ?? ''}-${index}`} className="text-sm text-slate-700 dark:text-slate-300">
                      {[item.degree, item.institution, item.graduation_year].filter(Boolean).join(' · ') || `Education entry ${index + 1}`}
                    </p>
                  ))}
                </section>
              )}

              {(analysis?.projects_analysis ?? []).map((item, index) => (
                <section key={`${item.name ?? ''}-${index}`} className="space-y-2 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    {item.name || `Project ${index + 1}`}
                  </h4>
                  {item.description && <p className="text-sm text-slate-700 dark:text-slate-300">{item.description}</p>}
                  <ReadOnlyList label="Technologies" items={item.technologies} />
                  <ReadOnlyList label="Achievements" items={item.achievements} />
                  <ReadOnlyList label="Suggestions" items={item.suggestions} />
                </section>
              ))}

              <ReadOnlyList label="ATS-Matched Keywords" items={analysis?.ats_matched_keywords} />
              <ReadOnlyList label="Potentially Missing Keywords" items={analysis?.ats_missing_keywords} />
              <ReadOnlyList label="Formatting Issues" items={analysis?.ats_formatting_issues} />
              {Object.keys(analysis?.ats_section_completeness ?? {}).length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-300">Section Completeness</h4>
                  <ul className="mt-1 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                    {Object.entries(analysis?.ats_section_completeness ?? {}).map(([section, present]) => (
                      <li key={section}>{section}: {present ? 'Present' : 'Missing'}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </form>
  );
};
