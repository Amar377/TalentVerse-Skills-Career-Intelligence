import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, CheckCircle2, Download, Save, Sparkles, Layers, GraduationCap, Briefcase, Lightbulb, ShieldAlert, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { CandidateProfile } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Textarea } from '../components/ui/Input';
import { useToast } from '../context/ToastContext';

export const ResumeAnalyzerPage: React.FC = () => {
  const { success, error, warning } = useToast();

  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [rawText, setRawText] = useState('');
  const [pastedText, setPastedText] = useState('');
  const [providerUsed, setProviderUsed] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const analysisInFlight = useRef(false);
  const [isSaving, setIsSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [resultSubTab, setResultSubTab] = useState<'skills' | 'experience' | 'education' | 'projects' | 'insights'>('skills');

  useEffect(() => {
    async function loadLatest() {
      try {
        const latest = await api.resumes.getLatest();
        if (latest && latest.profile) {
          setProfile(latest.profile);
          setRawText(latest.raw_text);
          setProviderUsed(latest.provider_used);
          setModelUsed(latest.model_used);
        }
      } catch {
        // no existing resume yet
      }
    }
    loadLatest();
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file || analysisInFlight.current) return;

    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      error('Invalid format', 'Please upload a PDF, DOCX, or TXT file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      error('File too large', 'Maximum file size allowed is 10MB.');
      return;
    }

    analysisInFlight.current = true;
    setIsAnalyzing(true);
    setUploadProgress(20);

    const progressTimer = setInterval(() => {
      setUploadProgress((prev) => (prev < 85 ? prev + 15 : prev));
    }, 400);

    try {
      const res = await api.resumes.upload(file);
      clearInterval(progressTimer);
      setUploadProgress(100);
      setProfile(res.profile);
      setRawText(res.raw_text);
      setProviderUsed(res.provider_used);
      setModelUsed(res.model_used);
      success('Resume Analyzed Successfully', `Extracted profile for ${res.profile.full_name || 'Candidate'}`);
    } catch (err: any) {
      clearInterval(progressTimer);
      error('Analysis Failed', err.message || 'Could not parse resume file.');
    } finally {
      analysisInFlight.current = false;
      setIsAnalyzing(false);
      setUploadProgress(0);
    }
  };

  const handleAnalyzeText = async () => {
    if (analysisInFlight.current) return;
    if (pastedText.trim().length < 30) {
      warning('Text too short', 'Please paste at least 30 characters of resume text.');
      return;
    }

    analysisInFlight.current = true;
    setIsAnalyzing(true);
    try {
      const res = await api.resumes.analyzeText(pastedText);
      setProfile(res.profile);
      setRawText(res.raw_text);
      setProviderUsed(res.provider_used);
      setModelUsed(res.model_used);
      success('Text Analysis Complete', `Extracted profile for ${res.profile.full_name || 'Candidate'}`);
    } catch (err: any) {
      error('Analysis Failed', err.message || 'Could not analyze resume text.');
    } finally {
      analysisInFlight.current = false;
      setIsAnalyzing(false);
    }
  };

  const handleSaveToProfile = async () => {
    if (!profile) return;
    setIsSaving(true);
    try {
      await api.profiles.updateMyProfile(profile);
      success('Profile Saved', 'Your master candidate profile has been updated.');
    } catch (err: any) {
      error('Save failed', err.message || 'Could not update profile.');
    } finally {
      setIsSaving(false);
    }
  };

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
          Upload your resume in PDF or DOCX format. Our multi-provider AI engine extracts structured skills, evaluates career readiness, and surfaces missing information.
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
              Document Upload (PDF / DOCX)
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
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
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
                Supports PDF and DOCX up to 10MB. Real entity extraction without fabricated skills.
              </p>

              {isAnalyzing && (
                <div className="max-w-xs mx-auto mt-6 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-brand-600 dark:text-brand-400">
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Analyzing with AI...
                    </span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-brand-500 h-full rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
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
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {profile && (
        <div className="space-y-6 animate-fade-in">
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
                  {profile.email} â€¢ {profile.phone || 'Phone not provided'} â€¢ {profile.location || 'Remote'}
                </p>
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mt-2">
                  Target Role: <span className="text-brand-600 dark:text-brand-400 font-semibold">{profile.target_role || 'Software Engineer'}</span>
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
                    onClick={handleSaveToProfile}
                    variant="primary"
                    size="sm"
                    isLoading={isSaving}
                    leftIcon={<Save className="w-4 h-4" />}
                  >
                    Save to Profile
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
            <div className="mt-5 pt-4 border-t border-slate-200/60 dark:border-slate-800 text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              <span className="font-semibold text-slate-900 dark:text-white">Executive Summary: </span>
              {profile.summary}
            </div>
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
                  <div className="flex flex-wrap gap-2">
                    {profile.skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-brand-50 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300 text-xs font-semibold border border-brand-200/80 dark:border-brand-800/80 shadow-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
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
                  profile.experience.map((exp, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed"
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
                  {profile.education.map((edu, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/50 text-xs text-slate-700 dark:text-slate-200 font-medium">
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
                {profile.projects.map((proj, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed"
                  >
                    {proj}
                  </div>
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
    </div>
  );
};
