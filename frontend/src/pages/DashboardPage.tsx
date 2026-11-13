import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, Award, Clock, Compass, Crosshair, FileText, Mic2, Layers, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import { DashboardStats } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await api.analytics.getDashboard();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-80 rounded-2xl lg:col-span-2" />
          <Skeleton className="h-80 rounded-2xl" />
        </div>
      </div>
    );
  }

  const technicalSkills = stats?.skills_distribution.filter((skill) => skill.type === 'technical') || [];
  const professionalSkills = stats?.skills_distribution.filter((skill) => skill.type === 'soft') || [];

  const milestoneProgress =
    stats && stats.total_milestones > 0
      ? Math.round((stats.completed_milestones / stats.total_milestones) * 100)
      : 0;

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-brand-900 via-indigo-900 to-navy-900 text-white shadow-xl border border-brand-500/20">
        <div className="absolute right-0 top-0 -mt-12 -mr-12 w-96 h-96 bg-brand-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-300 font-semibold">
                ✦ Career Intelligence Overview
              </span>
              {user?.is_demo && (
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800">
                  Interactive Sandbox
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome , {stats?.candidate_name || 'Candidate'}
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-xl">
              Targeting: <span className="text-white font-semibold">{stats?.target_role}</span>. Your career acceleration engine is active with real-time gap analysis.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/app/resume-analyzer">
              <Button variant="secondary" size="sm" leftIcon={<FileText className="w-4 h-4" />}>
                Update Resume
              </Button>
            </Link>
            <Link to="/app/roadmap">
              <Button variant="gradient" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View Roadmap
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Key Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Career Readiness */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold">
            <span>Career Readiness</span>
            <Award className="w-4 h-4 text-brand-500" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats?.career_readiness_score ?? 0}%
            </span>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              {(stats?.career_readiness_score ?? 0) >= 80 ? 'Job-ready' : 'In progress'}
            </span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-brand-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${stats?.career_readiness_score ?? 0}%` }}
            />
          </div>
        </Card>

        {/* Verified Skills */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold">
            <span>Verified Skills</span>
            <Layers className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats?.skills_count ?? 0}
            </span>
            <span className="text-xs text-slate-500">Tech & Soft Skills</span>
          </div>
          <p className="text-[11px] text-slate-400 truncate">
            {stats?.skills_distribution.slice(0, 3).map((s) => s.name).join(', ')}
          </p>
        </Card>

        {/* Roadmap Milestones */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold">
            <span>Roadmap Completion</span>
            <Compass className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {milestoneProgress}%
            </span>
            <span className="text-xs text-slate-500">
              {stats?.total_milestones ? `${stats.completed_milestones}/${stats.total_milestones} done` : 'No roadmap yet'}
            </span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-indigo-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${milestoneProgress}%` }}
            />
          </div>
        </Card>

        {/* Job Match Benchmark */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-semibold">
            <span>Estimated Job Fit</span>
            <Crosshair className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {stats?.recent_job_fit_score != null ? `${stats.recent_job_fit_score}%` : '—'}
            </span>
            {stats?.recent_job_fit_score != null && (
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                {stats.recent_job_fit_score >= 80 ? 'Strong match' : 'Review results'}
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 truncate">
            {stats?.recent_job_fit_score != null ? `Against ${stats.target_role}` : 'No job analysis yet'}
          </p>
        </Card>
      </div>

      {/* 3. Skills listed in the candidate profile */}
      <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Skills in your profile</CardTitle>
              <CardDescription>Skills currently listed in your candidate profile.</CardDescription>
            </div>
            <Link to="/app/profile">
              <Button variant="ghost" size="sm">
                Edit Skills
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[{ title: 'Technical skills', skills: technicalSkills }, { title: 'Professional skills', skills: professionalSkills }].map((group) => (
              <section key={group.title}>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">{group.title}</h3>
                {group.skills.length ? (
                  <div className="flex flex-wrap gap-2">
                    {group.skills.map((skill, index) => (
                      <Badge key={`${skill.name}-${index}`} variant="outline">{skill.name}</Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No skills listed yet.</p>
                )}
              </section>
            ))}
          </CardContent>
      </Card>

      {/* 4. Strategic Actions & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recommended Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-500" />
              Recommended Next Actions
            </CardTitle>
            <CardDescription>Prioritized high-impact steps to boost your hiring readiness.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats?.recommended_actions.map((rec, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 rounded-xl border border-slate-200/70 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 hover:border-brand-500/40 transition-all"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-white">
                      {rec.title}
                    </span>
                    <Badge
                      variant={rec.urgency === 'High' ? 'danger' : rec.urgency === 'Medium' ? 'warning' : 'default'}
                      size="sm"
                    >
                      {rec.urgency} Priority
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{rec.reason}</p>
                </div>
                <Link to={rec.action}>
                  <Button variant="secondary" size="sm" rightIcon={<ChevronRight className="w-3.5 h-3.5" />}>
                    Start
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Activities Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-500" />
              Recent Activity
            </CardTitle>
            <CardDescription>Live log of AI analyses and roadmap updates.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats?.recent_activities.length ? stats.recent_activities.map((act) => (
              <div key={act.id} className="flex items-start gap-3 text-xs">
                <div className="w-7 h-7 rounded-lg bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0 mt-0.5">
                  {act.type === 'resume' && <FileText className="w-3.5 h-3.5" />}
                  {act.type === 'roadmap' && <Compass className="w-3.5 h-3.5" />}
                  {act.type === 'job_match' && <Crosshair className="w-3.5 h-3.5" />}
                  {act.type === 'interview' && <Mic2 className="w-3.5 h-3.5" />}
                  {act.type === 'project' && <Sparkles className="w-3.5 h-3.5" />}
                </div>
                <div className="flex-1 truncate">
                  <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {act.title}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                    {act.description}
                  </div>
                </div>
                {act.score !== undefined && act.score !== null && (
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">
                    {act.score}%
                  </span>
                )}
              </div>
            )) : <p className="text-sm text-slate-500">Your saved analyses and roadmap updates will appear here.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
