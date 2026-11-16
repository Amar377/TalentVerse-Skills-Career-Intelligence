import React, { useState, useEffect } from 'react';
import { Crosshair, CheckCircle2, AlertTriangle, Sparkles, Briefcase, GraduationCap } from 'lucide-react';
import { api } from '../services/api';
import { JobMatch, CandidateProfile } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { AIModelSelector } from '../components/AIModelSelector';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Textarea, Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';
import { useAIProvider } from '../hooks/useAIProvider';

export const JobMatcherPage: React.FC = () => {
  const { success, error, warning } = useToast();
  const { providers, preferredProvider, selectProvider, loadingProviders } = useAIProvider();

  const [jobDescription, setJobDescription] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [company, setCompany] = useState('');
  const [profiles, setProfiles] = useState<CandidateProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');

  const [matchResult, setMatchResult] = useState<JobMatch | null>(null);
  const [isMatching, setIsMatching] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [profileList, latestMatch] = await Promise.allSettled([
          api.profiles.list(),
          api.jobs.getLatest(),
        ]);
        if (profileList.status === 'fulfilled' && profileList.value.length > 0) {
          setProfiles(profileList.value);
          setSelectedProfileId(profileList.value[0].id || '');
          setTargetRole(profileList.value[0].target_role || '');
        }
        if (latestMatch.status === 'fulfilled' && latestMatch.value) {
          setMatchResult(latestMatch.value);
          setTargetRole(latestMatch.value.target_role);
          setCompany(latestMatch.value.company || '');
          setJobDescription(latestMatch.value.job_description);
        }
      } catch (err) {
        console.error('Failed to load initial data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (jobDescription.trim().length < 25) {
      warning('Description too short', 'Please paste a job description with at least 25 characters.');
      return;
    }

    setIsMatching(true);
    try {
      const res = await api.jobs.match({
        job_description: jobDescription.trim(),
        target_role: targetRole.trim(),
        company: company.trim(),
        profile_id: selectedProfileId || undefined,
        preferred_provider: preferredProvider,
      });
      setMatchResult(res);
      success('Match Analysis Complete', `Fit Score: ${res.match_score_percent}% for ${res.target_role}`);
    } catch (err: any) {
      error('Matching Failed', err.message || 'Could not evaluate job match.');
    } finally {
      setIsMatching(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Job Fit Matcher & Gap Analysis
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Compare candidate credentials against any job description. Compute match scores, isolate missing competencies, and view verified evidence.
        </p>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-emerald-500" /> Job Description & Role Context
          </CardTitle>
          <CardDescription>
            Paste the job posting requirements and choose which profile to benchmark.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleMatch} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Input
                  label="Target Job Title"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="e.g. Senior Backend Engineer"
                  required
                />
              </div>

              <div className="max-w-sm">
                <AIModelSelector
                  providers={providers}
                  preferredProvider={preferredProvider}
                  onChange={selectProvider}
                  loading={loadingProviders}
                  disabled={isMatching}
                />
              </div>

              <div>
                <Input
                  label="Company Name (Optional)"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Stripe, OpenAI"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Benchmark Profile
                </label>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name || 'Unnamed Candidate'} ({p.target_role || p.experience_level})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <Textarea
                label="Job Description & Requirements"
                placeholder="Paste the job description, required technical skills, qualifications, and responsibilities..."
                rows={7}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                required
              />
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                variant="gradient"
                isLoading={isMatching}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Analyze Job Fit
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results View */}
      {matchResult && (
        <div className="space-y-6 animate-fade-in">
          {/* Fit Score Banner */}
          <Card className="p-6 bg-gradient-to-r from-emerald-950/20 via-slate-900/10 to-brand-950/20 border-emerald-500/30">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono uppercase tracking-widest text-emerald-500 font-bold">
                    ✦ Job Fit Assessment
                  </span>
                  {matchResult.company && (
                    <Badge variant="default" size="sm">
                      {matchResult.company}
                    </Badge>
                  )}
                </div>
                <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
                  {matchResult.target_role}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
                  {matchResult.caveat}
                </p>
              </div>

              {/* Match Score Gauge */}
              <div className="flex items-center gap-4">
                <div className="p-4 rounded-2xl bg-white dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-center min-w-[140px] shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Match Score
                  </div>
                  <div
                    className={`text-3xl font-black mt-1 ${
                      matchResult.match_score_percent >= 80
                        ? 'text-emerald-500'
                        : matchResult.match_score_percent >= 60
                        ? 'text-amber-500'
                        : 'text-rose-500'
                    }`}
                  >
                    {matchResult.match_score_percent}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-medium mt-0.5">
                    {matchResult.match_score_percent >= 80
                      ? 'High Readiness'
                      : matchResult.match_score_percent >= 60
                      ? 'Moderate Fit'
                      : 'Skill Gaps Present'}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Side-by-Side Skills Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Matching Skills */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" /> Matching Verified Skills ({matchResult.matching_skills.length})
                </CardTitle>
                <CardDescription>Directly satisfied by candidate profile credentials.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {matchResult.matching_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 text-xs font-semibold border border-emerald-200/80 dark:border-emerald-800/80 shadow-xs flex items-center gap-1.5"
                    >
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Missing Skills */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="w-5 h-5" /> Missing or Unverified Skills ({matchResult.missing_or_unverified_skills.length})
                </CardTitle>
                <CardDescription>Required competencies absent from current profile.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {matchResult.missing_or_unverified_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/70 text-amber-700 dark:text-amber-300 text-xs font-semibold border border-amber-200/80 dark:border-amber-800/80 shadow-xs flex items-center gap-1.5"
                    >
                      ! {skill}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Experience & Education Relevance */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-brand-500" /> Experience Relevance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                {matchResult.experience_relevance.map((exp, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/40 text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
                    {exp}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-indigo-500" /> Education & Qualifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                {matchResult.education_relevance.map((edu, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/40 text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
                    {edu}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Concrete Improvement Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 text-brand-600 dark:text-brand-400">
                <Sparkles className="w-4 h-4" /> Actionable Next Steps to Qualify
              </CardTitle>
              <CardDescription>
                Specific projects or preparation tasks to bridge the remaining gap.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {matchResult.improvement_actions.map((act, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 text-xs text-slate-700 dark:text-slate-200"
                >
                  <span className="w-5 h-5 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-600 dark:text-brand-300 font-bold flex items-center justify-center shrink-0 text-[10px]">
                    {idx + 1}
                  </span>
                  <div className="flex-1 leading-relaxed">{act}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
