import React, { useState, useEffect } from 'react';
import { UserCircle, Save, X, Sparkles, Layers, Briefcase } from 'lucide-react';
import { api } from '../services/api';
import { CandidateProfile } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input, Textarea } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

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
      const updated = await api.profiles.updateMyProfile(profile);
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
    </form>
  );
};
