import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, CheckCircle2, Download, Sparkles, Layers, GraduationCap, Briefcase, Lightbulb, ShieldAlert, Loader2, Pencil } from 'lucide-react';
import { api } from '../services/api';
import { CandidateProfile } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { AIModelSelector } from '../components/AIModelSelector';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Textarea } from '../components/ui/Input';
import { useToast } from '../context/ToastContext';
import { useAIProvider } from '../hooks/useAIProvider';
import { useNavigate } from 'react-router-dom';

export const ResumeAnalyzerPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error, warning } = useToast();
  const { providers, preferredProvider, selectProvider, loadingProviders } = useAIProvider();

  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [rawText, setRawText] = useState('');
  const [pastedText, setPastedText] = useState('');
  const [providerUsed, setProviderUsed] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const analysisInFlight = useRef(false);
  const analysisRequestSequence = useRef(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [replaceExistingProfile, setReplaceExistingProfile] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);
  const scrollToResults = useRef(false);
  const [dragOver, setDragOver] = useState(false);
  const [resultSubTab, setResultSubTab] = useState<'skills' | 'experience' | 'education' | 'projects' | 'insights'>('skills');

  useEffect(() => {
    const requestSequence = analysisRequestSequence.current;
    async function loadLatest() {
      try {
        const latest = await api.resumes.getLatest();
        if (analysisRequestSequence.current !== requestSequence) return;
        if (latest && latest.profile) {
          setProfile(latest.profile);
          setRawText(latest.raw_text);
          setProviderUsed(latest.provider_used);
          setModelUsed(latest.model_used);
        }
      } catch (err) {
        if (analysisRequestSequence.current === requestSequence) {
          setAnalysisError(err instanceof Error ? err.message : 'Could not load your previous resume analysis.');
        }
      }
    }
    loadLatest();
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file || analysisInFlight.current) return;

    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      error('Unsupported file type', 'Choose a PDF, DOCX, TXT, or Markdown (.md) file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      error('File too large', 'Maximum file size allowed is 10MB.');
      return;
    }

    analysisInFlight.current = true;
    analysisRequestSequence.current += 1;
    setProfile(null);
    setRawText('');
    setProviderUsed(null);
    setModelUsed(null);
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const res = await api.resumes.upload(file, preferredProvider, replaceExistingProfile);
      setProfile(res.profile);
      setRawText(res.raw_text);
      setProviderUsed(res.provider_used);
      setModelUsed(res.model_used);
      scrollToResults.current = true;
      success('Resume Analyzed Successfully', `Extracted profile for ${res.profile.full_name || 'Candidate'}`);
    } catch (err: any) {
      const message = err.message || 'Could not parse resume file.';
      setAnalysisError(message);
      error('Analysis Failed', message);
    } finally {
      analysisInFlight.current = false;
      setIsAnalyzing(false);
    }
  };

  const handleAnalyzeText = async () => {
    if (analysisInFlight.current) return;
    if (pastedText.trim().length < 30) {
      warning('Text too short', 'Please paste at least 30 characters of resume text.');
      return;
    }

    analysisInFlight.current = true;
    analysisRequestSequence.current += 1;
    setProfile(null);
    setRawText('');
    setProviderUsed(null);
    setModelUsed(null);
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await api.resumes.analyzeText(pastedText, preferredProvider, replaceExistingProfile);
      setProfile(res.profile);
      setRawText(res.raw_text);
      setProviderUsed(res.provider_used);
      setModelUsed(res.model_used);
      scrollToResults.current = true;
      success('Text Analysis Complete', `Extracted profile for ${res.profile.full_name || 'Candidate'}`);
    } catch (err: any) {
      const message = err.message || 'Could not analyze resume text.';
      setAnalysisError(message);
      error('Analysis Failed', message);
    } finally {
      analysisInFlight.current = false;
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (profile && scrollToResults.current) {
      scrollToResults.current = false;
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [profile]);

  const handleDownloadReport = () => {
    if (!profile) return;
    const reportData = {
      profile,
      extracted_raw_text_length: rawText.length,
      provider: providerUsed,
      model: modelUsed,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `talentverse_resume_analysis_${(profile.full_name || 'candidate').toLowerCase().replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    success('Report Exported', 'Downloaded structured resume analysis dossier.');
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Resume Analyzer & Intelligence
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Upload a PDF, DOCX, TXT, or Markdown resume. Our multi-provider AI engine extracts structured skills, evaluates career readiness, and surfaces missing information.
        </p>
      </div>

      {/* Upload Zone & Paste Text Tabs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'upload'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-300 border border-brand-500/30'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Upload File (PDF / DOCX / TXT / MD)
            </button>
            <button
              onClick={() => setActiveTab('paste')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'paste'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-300 border border-brand-500/30'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Paste Resume Text
            </button>
          </div>

          {providerUsed && (
            <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-slate-400">
              <Sparkles className="w-3.5 h-3.5 text-brand-500" />
              <span>Analyzed via {providerUsed} ({modelUsed})</span>
            </div>
          )}
        </CardHeader>

        <CardContent>
          <div className="mb-4 max-w-sm">
            <AIModelSelector
              providers={providers}
              preferredProvider={preferredProvider}
              onChange={selectProvider}
              loading={loadingProviders}
              disabled={isAnalyzing}
            />
          </div>
          <label className="mb-4 flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={replaceExistingProfile}
              onChange={(event) => setReplaceExistingProfile(event.target.checked)}
              disabled={isAnalyzing}
              className="mt-0.5 accent-brand-500"
            />
            <span>
              Replace existing non-empty profile fields with details from this resume.
              Leave unchecked to preserve your existing profile and only add missing information.
            </span>
          </label>
          {activeTab === 'upload' ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  handleFileUpload(e.dataTransfer.files[0]);
                }
              }}
              className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all ${
                dragOver
                  ? 'border-brand-500 bg-brand-50/20 dark:bg-brand-950/20'
                  : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-navy-950/20'
              }`}
            >
              <input
                type="file"
                id="resume-file-input"
                className="hidden"
                accept=".pdf,.docx,.txt,.md"
                disabled={isAnalyzing}
                onChange={(e) => {
                  const file = e.currentTarget.files?.[0];
                  e.currentTarget.value = '';
                  if (file) void handleFileUpload(file);
                }}
              />

              <div className="w-14 h-14 rounded-2xl bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400 mx-auto mb-4">
                <UploadCloud className="w-7 h-7" />
              </div>

              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                Drop your resume here, or{' '}
                <label
                  htmlFor="resume-file-input"
                  className="text-brand-600 dark:text-brand-400 hover:underline cursor-pointer"
                >
                  browse files
                </label>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-4">
                Supports PDF, DOCX, TXT, and Markdown (.md) files up to 10MB. Scanned PDFs need selectable text; OCR is not available.
              </p>

              {isAnalyzing && (
                <div className="max-w-sm mx-auto mt-6">
                  <div className="flex items-center justify-center gap-2 text-xs text-brand-600 dark:text-brand-400">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Uploading and analyzing your resume. This may take a minute.</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <Textarea
                label="Paste Resume Text"
                placeholder="Paste the full text of your resume here, including experience, skills, and education..."
                rows={9}
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
              />
              <div className="flex justify-end">
                <Button
                  onClick={handleAnalyzeText}
                  variant="gradient"
                  isLoading={isAnalyzing}
                  leftIcon={<Sparkles className="w-4 h-4" />}
                >
                  Analyze Resume Text
                </Button>
              </div>
            </div>
          )}
          {analysisError && (
            <div role="alert" className="mt-4 rounded-xl border border-rose-300 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
              <strong>Resume analysis unavailable:</strong> {analysisError} You can retry the upload or paste the resume text.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {profile && (
        <div ref={resultsRef} className="space-y-6 animate-fade-in scroll-mt-6">
          {/* Candidate Overview Card */}
          <Card className="p-6 bg-gradient-to-r from-white via-slate-50 to-brand-50/20 dark:from-navy-900 dark:via-navy-900 dark:to-brand-950/30">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                    {profile.full_name || 'Candidate Profile'}
                  </h2>
                  <Badge variant="brand" size="sm">
                    {profile.experience_level}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {[profile.email, profile.phone, profile.location].filter(Boolean).join(' • ') || 'No contact details were extracted'}
                </p>
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mt-2">
                  Target Role: <span className="text-brand-600 dark:text-brand-400 font-semibold">{profile.target_role || 'Not stated in the resume'}</span>
                  {profile.current_role && <> · Current Role: <span className="font-semibold">{profile.current_role}</span></>}
                  {profile.total_experience && <> · Experience: <span className="font-semibold">{profile.total_experience}</span></>}
                </p>
              </div>

              {/* Readiness Score Badge */}
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-white dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 text-center min-w-[110px]">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Readiness
                  </div>
                  <div className="text-2xl font-black text-brand-600 dark:text-brand-400 mt-0.5">
                    {profile.readiness_score}%
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <Button
                    onClick={() => navigate('/app/profile')}
                    variant="primary"
                    size="sm"
                    leftIcon={<Pencil className="w-4 h-4" />}
                  >
                    Review & Edit Profile
                  </Button>
                  <Button
                    onClick={handleDownloadReport}
                    variant="outline"
                    size="sm"
                    leftIcon={<Download className="w-4 h-4" />}
                  >
                    Export Dossier
                  </Button>
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="mt-5 pt-4 border-t border-slate-200/60 dark:border-slate-800 space-y-3">
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                <span className="font-semibold text-slate-900 dark:text-white">Professional Summary: </span>
                {profile.summary || 'No professional summary was extracted.'}
              </p>
              {profile.summary_quality_analysis && (
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  <span className="font-semibold">Summary assessment: </span>{profile.summary_quality_analysis}
                </p>
              )}
              {profile.summary_improvement_suggestions?.length ? (
                <ul className="list-disc pl-5 space-y-1 text-xs text-brand-700 dark:text-brand-300">
                  {profile.summary_improvement_suggestions.map((suggestion, index) => <li key={`${suggestion}-${index}`}>{suggestion}</li>)}
                </ul>
              ) : null}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-brand-500" /> ATS Readiness Estimate
              </CardTitle>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                General resume-readiness guidance, not a score from a specific ATS or a guarantee of interview results.
                Add a job description in Job Matcher for role-specific keyword comparison.
              </p>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex items-center gap-4">
                <div className="min-w-[84px] text-center">
                  <div className="text-3xl font-black text-brand-600 dark:text-brand-400">
                    {profile.ats_score ?? '—'}
                  </div>
                  <div className="text-[10px] uppercase tracking-wide text-slate-500">
                    {profile.ats_score == null ? 'Not scored' : 'out of 100'}
                  </div>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-brand-500 transition-all"
                      style={{ width: `${profile.ats_score ?? 0}%` }}
                    />
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    {profile.ats_score_explanation || 'No ATS assessment explanation was returned for this resume.'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-2">
                    Evidenced keywords
                  </h3>
                  {profile.ats_matched_keywords?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {profile.ats_matched_keywords.map((keyword, index) => (
                        <Badge key={`${keyword}-${index}`} variant="success" size="sm">{keyword}</Badge>
                      ))}
                    </div>
                  ) : <p className="text-xs text-slate-500">No keywords were identified.</p>}
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400 mb-2">
                    Potential missing keywords
                  </h3>
                  {profile.ats_missing_keywords?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {profile.ats_missing_keywords.map((keyword, index) => (
                        <Badge key={`${keyword}-${index}`} variant="warning" size="sm">{keyword}</Badge>
                      ))}
                    </div>
                  ) : <p className="text-xs text-slate-500">No specific keyword gaps identified.</p>}
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-300 mb-2">
                    Formatting checks
                  </h3>
                  {profile.ats_formatting_issues?.length ? (
                    <ul className="space-y-1">
                      {profile.ats_formatting_issues.map((issue, index) => (
                        <li key={`${issue}-${index}`} className="text-xs text-slate-600 dark:text-slate-300">
                          • {issue}
                        </li>
                      ))}
                    </ul>
                  ) : <p className="text-xs text-slate-500">No formatting issues were identified.</p>}
                </div>
              </div>
              {profile.ats_section_completeness && Object.keys(profile.ats_section_completeness).length > 0 && (
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-300 mb-2">
                    Section completeness used in the estimate
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(profile.ats_section_completeness).map(([section, present]) => (
                      <Badge key={section} variant={present ? 'success' : 'warning'} size="sm">
                        {section.replace(/_/g, ' ')}: {present ? 'present' : 'not found'}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section Navigation Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setResultSubTab('skills')}
              className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap flex items-center gap-2 ${
                resultSubTab === 'skills'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold border border-brand-500/20'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              Skills & Core Competencies ({profile.skills.length})
            </button>
            <button
              onClick={() => setResultSubTab('experience')}
              className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap flex items-center gap-2 ${
                resultSubTab === 'experience'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold border border-brand-500/20'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Experience ({profile.experience.length})
            </button>
            <button
              onClick={() => setResultSubTab('education')}
              className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap flex items-center gap-2 ${
                resultSubTab === 'education'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold border border-brand-500/20'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              Education & Certifications
            </button>
            <button
              onClick={() => setResultSubTab('projects')}
              className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap flex items-center gap-2 ${
                resultSubTab === 'projects'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold border border-brand-500/20'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              Verified Projects ({profile.projects.length})
            </button>
            <button
              onClick={() => setResultSubTab('insights')}
              className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap flex items-center gap-2 ${
                resultSubTab === 'insights'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold border border-brand-500/20'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Lightbulb className="w-4 h-4" />
              AI Recommendations & Gaps
            </button>
          </div>

          {/* Tab 1: Skills */}
          {resultSubTab === 'skills' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Layers className="w-4 h-4 text-brand-500" /> Technical Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {Object.keys(profile.skills_by_category || {}).length > 0 ? (
                    <div className="space-y-4">
                      {Object.entries(profile.skills_by_category || {}).map(([category, skills]) => (
                        <div key={category}>
                          <h4 className="mb-2 text-xs font-bold text-slate-600 dark:text-slate-300">{category}</h4>
                          <div className="flex flex-wrap gap-2">
                            {skills.map((skill, idx) => (
                              <Badge key={`${category}-${skill}-${idx}`} variant="brand" size="sm">{skill}</Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : profile.skills.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {profile.skills.map((skill, idx) => (
                        <Badge key={`${skill}-${idx}`} variant="brand" size="sm">{skill}</Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No technical skills were extracted. Review the resume text and try again.</p>
                  )}
                  {profile.target_role_skill_alignment?.length ? (
                    <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
                      <h4 className="mb-2 text-xs font-bold text-slate-600 dark:text-slate-300">Target-role alignment</h4>
                      <ul className="list-disc space-y-1 pl-5 text-xs text-slate-600 dark:text-slate-300">
                        {profile.target_role_skill_alignment.map((item, idx) => <li key={`${item}-${idx}`}>{item}</li>)}
                      </ul>
                    </div>
                  ) : null}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-500" /> Soft & Leadership Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {profile.soft_skills.length === 0 && (
                      <p className="text-xs text-slate-500">No soft skills were identified in the resume.</p>
                    )}
                    {profile.soft_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/70 text-cyan-700 dark:text-cyan-300 text-xs font-semibold border border-cyan-200/80 dark:border-cyan-800/80 shadow-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tab 2: Experience */}
          {resultSubTab === 'experience' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Work Experience History</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {profile.experience.length === 0 ? (
                  <p className="text-xs text-slate-500">No formal work experience parsed.</p>
                ) : (
                  profile.experience_analysis?.length ? profile.experience_analysis.map((item, idx) => (
                    <div
                      key={`${item.company || 'experience'}-${idx}`}
                      className="space-y-3 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 text-xs leading-relaxed text-slate-700 dark:border-slate-800 dark:bg-navy-950/40 dark:text-slate-200 sm:text-sm"
                    >
                      <div className="font-bold text-slate-900 dark:text-white">
                        {[item.job_title, item.company].filter(Boolean).join(' · ') || profile.experience[idx]}
                        {item.duration ? <span className="font-normal text-slate-500"> · {item.duration}</span> : null}
                      </div>
                      {item.responsibilities.length > 0 && (
                        <p><strong>Responsibilities:</strong> {item.responsibilities.join(' ')}</p>
                      )}
                      {item.achievements.length > 0 && (
                        <p><strong>Achievements:</strong> {item.achievements.join(' ')}</p>
                      )}
                      {item.missing_measurable_results.length > 0 && (
                        <p><strong>Missing measurable results:</strong> {item.missing_measurable_results.join(' ')}</p>
                      )}
                      {item.suggestions.length > 0 && (
                        <ul className="list-disc space-y-1 pl-5 text-brand-700 dark:text-brand-300">
                          {item.suggestions.map((suggestion, suggestionIdx) => <li key={`${suggestion}-${suggestionIdx}`}>{suggestion}</li>)}
                        </ul>
                      )}
                    </div>
                  )) : profile.experience.map((exp, idx) => (
                    <div
                      key={`${exp.slice(0, 40)}-${idx}`}
                      className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 text-xs leading-relaxed text-slate-700 dark:border-slate-800 dark:bg-navy-950/40 dark:text-slate-200 sm:text-sm"
                    >
                      {exp}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )}

          {/* Tab 3: Education & Certs */}
          {resultSubTab === 'education' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-indigo-500" /> Education
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {profile.education.length === 0 && !profile.education_analysis?.length && (
                    <p className="text-xs text-slate-500">No education details were extracted.</p>
                  )}
                  {profile.education_analysis?.length ? (
                    profile.education_analysis.map((item, idx) => (
                      <div key={`${item.institution || item.degree || 'education'}-${idx}`} className="rounded-xl bg-slate-50 p-3 text-xs text-slate-700 dark:bg-navy-950/50 dark:text-slate-200">
                        {[item.degree, item.institution, item.graduation_year].filter(Boolean).join(' · ')}
                      </div>
                    ))
                  ) : profile.education.map((edu, idx) => (
                    <div key={`${edu.slice(0, 40)}-${idx}`} className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/50 text-xs text-slate-700 dark:text-slate-200 font-medium">
                      {edu}
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Certifications
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {profile.certifications.length === 0 ? (
                    <p className="text-xs text-slate-500">No certifications listed.</p>
                  ) : (
                    profile.certifications.map((cert, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 text-xs text-emerald-700 dark:text-emerald-300 font-medium border border-emerald-500/20">
                        {cert}
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tab 4: Projects */}
          {resultSubTab === 'projects' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Portfolio & Engineering Projects</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {profile.projects.length === 0 && !profile.projects_analysis?.length && (
                  <p className="text-xs text-slate-500">No projects were extracted. Add relevant projects to your resume if applicable.</p>
                )}
                {profile.projects_analysis?.map((project, idx) => (
                  <div key={`${project.name || 'project'}-${idx}`} className="space-y-2 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 text-xs text-slate-700 dark:border-slate-800 dark:bg-navy-950/40 dark:text-slate-200">
                    <h4 className="font-bold">{project.name || 'Project'}</h4>
                    {project.technologies.length > 0 && <p><strong>Technologies:</strong> {project.technologies.join(', ')}</p>}
                    {project.description && <p>{project.description}</p>}
                    {project.achievements.length > 0 && <p><strong>Achievements:</strong> {project.achievements.join(' ')}</p>}
                    {project.suggestions.length > 0 && (
                      <ul className="list-disc space-y-1 pl-5 text-brand-700 dark:text-brand-300">
                        {project.suggestions.map((suggestion, suggestionIdx) => <li key={`${suggestion}-${suggestionIdx}`}>{suggestion}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
                {!profile.projects_analysis?.length && profile.projects.map((proj, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed"
                  >
                    {proj}
                  </div>
                ))}
                {profile.project_improvement_suggestions?.map((suggestion, idx) => (
                  <p key={`${suggestion}-${idx}`} className="rounded-lg bg-brand-50 p-3 text-xs text-brand-800 dark:bg-brand-950/30 dark:text-brand-300">
                    {suggestion}
                  </p>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Tab 5: AI Recommendations & Missing Information */}
          {resultSubTab === 'insights' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Strengths */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" /> Core Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {profile.strengths.length === 0 && (
                    <p className="text-xs text-slate-500">No strengths were returned for this analysis.</p>
                  )}
                  {profile.strengths.map((str, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed border border-emerald-500/20">
                      {str}
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Missing Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2 text-amber-600 dark:text-amber-400">
                    <ShieldAlert className="w-4 h-4" /> Missing Data
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {profile.missing_information.length === 0 && (
                    <p className="text-xs text-slate-500">No missing information was identified.</p>
                  )}
                  {profile.missing_information.map((item, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 text-xs text-amber-800 dark:text-amber-300 leading-relaxed border border-amber-500/20">
                      {item}
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2 text-brand-600 dark:text-brand-400">
                    <Lightbulb className="w-4 h-4" /> Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {profile.improvement_recommendations.length === 0 && (
                    <p className="text-xs text-slate-500">No additional recommendations were returned for this analysis.</p>
                  )}
                  {profile.improvement_recommendations.map((rec, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-brand-50/60 dark:bg-brand-950/30 text-xs text-brand-800 dark:text-brand-300 leading-relaxed border border-brand-500/20">
                      {rec}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
      {!profile && !isAnalyzing && !analysisError && (
        <Card className="border-dashed p-6 text-center">
          <CardTitle className="text-sm">No resume analysis to display yet</CardTitle>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            Upload a readable PDF, DOCX, TXT, or Markdown resume, or paste its text to see the structured results here.
          </p>
        </Card>
      )}
    </div>
  );
};
