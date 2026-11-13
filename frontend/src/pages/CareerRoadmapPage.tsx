import React, { useState, useEffect } from 'react';
import { Compass, CheckCircle2, Circle, Sparkles, ExternalLink, BookOpen, Sliders, Download } from 'lucide-react';
import { api } from '../services/api';
import { CareerRoadmap } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

export const CareerRoadmapPage: React.FC = () => {
  const { success, error } = useToast();

  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Form State
  const [targetGoal, setTargetGoal] = useState('Full Stack AI Engineer');
  const [skillsText, setSkillsText] = useState('Python, FastAPI, React, SQL, Git');
  const [level, setLevel] = useState('Entry-level');
  const [durationWeeks, setDurationWeeks] = useState(8);

  useEffect(() => {
    async function loadRoadmap() {
      try {
        const latest = await api.roadmaps.getLatest();
        if (latest) {
          setRoadmap(latest);
          setTargetGoal(latest.career_goal);
          setDurationWeeks(latest.duration_weeks);
          setLevel(latest.experience_level);
        }
      } catch (err) {
        console.error('Failed to load roadmap', err);
      } finally {
        setLoading(false);
      }
    }
    loadRoadmap();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    const skills = skillsText.split(',').map((s) => s.trim()).filter(Boolean);
    if (!targetGoal.trim()) {
      error('Missing Goal', 'Please enter your target career goal.');
      return;
    }

    setGenerating(true);
    try {
      const res = await api.roadmaps.generate({
        skills,
        career_goal: targetGoal.trim(),
        experience_level: level,
        duration_weeks: durationWeeks,
      });
      setRoadmap(res);
      success('Roadmap Generated', `Created strategic ${durationWeeks}-week roadmap for ${targetGoal}`);
    } catch (err: any) {
      error('Generation Failed', err.message || 'Could not generate roadmap.');
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleMilestone = async (week: number, currentCompleted: boolean) => {
    if (!roadmap) return;
    try {
      const updated = await api.roadmaps.toggleMilestone(roadmap.id, week, !currentCompleted);
      setRoadmap(updated);
      if (!currentCompleted) {
        success('Milestone Completed! 🎯', `Marked week ${week} deliverable verified.`);
      }
    } catch (err: any) {
      error('Update failed', err.message || 'Could not toggle milestone.');
    }
  };

  const handleDownloadRoadmap = () => {
    if (!roadmap) return;
    const blob = new Blob([JSON.stringify(roadmap, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `talentverse_roadmap_${roadmap.career_goal.toLowerCase().replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    success('Exported', 'Downloaded roadmap plan.');
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  const completedCount = roadmap?.milestones.filter((m) => m.completed).length || 0;
  const totalCount = roadmap?.milestones.length || 1;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Interactive Career Roadmap
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Transform high-level career ambitions into structured, week-by-week sprints with tangible deliverables.
          </p>
        </div>

        {roadmap && (
          <Button
            onClick={handleDownloadRoadmap}
            variant="outline"
            size="sm"
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export Plan JSON
          </Button>
        )}
      </div>

      {/* Generator Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-500" /> Roadmap Configuration
          </CardTitle>
          <CardDescription>
            Customize your target position, existing skills, and learning timeline.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-1">
              <Input
                label="Target Role / Goal"
                value={targetGoal}
                onChange={(e) => setTargetGoal(e.target.value)}
                placeholder="e.g. AI Systems Engineer"
                required
              />
            </div>

            <div className="lg:col-span-1">
              <Input
                label="Current Known Skills"
                value={skillsText}
                onChange={(e) => setSkillsText(e.target.value)}
                placeholder="Python, React, SQL..."
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Experience Level
              </label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              >
                <option value="Student">Student</option>
                <option value="Entry-level">Entry-level</option>
                <option value="Junior">Junior</option>
                <option value="Mid-level">Mid-level</option>
                <option value="Senior">Senior</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Timeline: {durationWeeks} Weeks
              </label>
              <div className="flex items-center gap-3 pt-2">
                <input
                  type="range"
                  min="4"
                  max="24"
                  step="2"
                  value={durationWeeks}
                  onChange={(e) => setDurationWeeks(Number(e.target.value))}
                  className="w-full accent-brand-500 cursor-pointer"
                />
                <Button
                  type="submit"
                  variant="gradient"
                  size="sm"
                  isLoading={generating}
                  leftIcon={<Sparkles className="w-3.5 h-3.5" />}
                  className="shrink-0"
                >
                  Generate
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Active Roadmap Display */}
      {roadmap && (
        <div className="space-y-6 animate-fade-in">
          {/* Roadmap Overview Banner */}
          <Card className="p-6 bg-gradient-to-r from-brand-950/20 via-indigo-950/10 to-slate-900/5 dark:from-brand-950/40 dark:via-indigo-950/30 dark:to-navy-900 border-brand-500/20">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase font-mono tracking-widest text-brand-600 dark:text-brand-400 font-semibold">
                  ✦ Active Strategy
                </span>
                <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
                  {roadmap.career_goal}
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  {roadmap.experience_level} • {roadmap.duration_weeks} Weeks • {roadmap.milestones.length} Strategic Milestones
                </p>
              </div>

              {/* Progress Gauge */}
              <div className="flex items-center gap-4 min-w-[200px]">
                <div className="flex-1 space-y-1.5 text-right">
                  <div className="text-xs font-medium text-slate-500">Milestone Progress</div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">
                    {progressPercent}%
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-brand-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Priority Skill Gaps */}
            <div className="mt-6 pt-5 border-t border-slate-200/80 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Priority Gaps To Close:
              </span>
              <div className="flex flex-wrap gap-2 mt-2">
                {roadmap.skill_gaps.map((gap, idx) => (
                  <Badge key={idx} variant="warning" size="md">
                    {gap}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>

          {/* Chronological Milestones Timeline */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-brand-500" /> Weekly Learning Milestones
            </h3>

            <div className="space-y-4">
              {roadmap.milestones.map((m) => (
                <Card
                  key={m.week}
                  className={`transition-all duration-200 ${
                    m.completed
                      ? 'border-emerald-500/30 bg-emerald-50/20 dark:bg-emerald-950/10'
                      : 'hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <CardHeader className="flex flex-row items-start justify-between pb-3">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => handleToggleMilestone(m.week, m.completed)}
                        className={`mt-0.5 p-1 rounded-lg transition-colors ${
                          m.completed
                            ? 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/60'
                            : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
                        }`}
                        title={m.completed ? 'Mark incomplete' : 'Mark complete'}
                      >
                        {m.completed ? (
                          <CheckCircle2 className="w-6 h-6" />
                        ) : (
                          <Circle className="w-6 h-6" />
                        )}
                      </button>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold uppercase px-2 py-0.5 rounded bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
                            Week {m.week}
                          </span>
                          <h4
                            className={`text-base font-bold text-slate-900 dark:text-white ${
                              m.completed ? 'line-through opacity-70' : ''
                            }`}
                          >
                            {m.title}
                          </h4>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          <span className="font-semibold text-slate-700 dark:text-slate-300">Deliverable: </span>
                          {m.deliverable}
                        </p>
                      </div>
                    </div>

                    <Badge variant={m.completed ? 'success' : 'default'} size="sm">
                      {m.completed ? 'Completed' : 'In Progress'}
                    </Badge>
                  </CardHeader>

                  <CardContent className="pt-0 space-y-4">
                    {/* Learning Tasks */}
                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/60 border border-slate-100 dark:border-slate-800/80">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Core Learning Tasks:
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                        {m.learning_tasks.map((task, tIdx) => (
                          <li key={tIdx} className="flex items-start gap-2">
                            <span className="text-brand-500 font-bold">•</span>
                            <span>{task}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Success Criteria */}
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                        Verification Criteria:
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {m.success_criteria.map((crit, cIdx) => (
                          <span
                            key={cIdx}
                            className="text-[11px] px-2.5 py-1 rounded-lg bg-white dark:bg-navy-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800"
                          >
                            ✓ {crit}
                          </span>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Curated Resources */}
          {roadmap.recommended_resources && roadmap.recommended_resources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-cyan-500" /> Recommended Learning Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roadmap.recommended_resources.map((res, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 flex flex-col justify-between"
                  >
                    <div>
                      <Badge variant="cyan" size="sm" className="mb-2">
                        {res.type}
                      </Badge>
                      <h5 className="text-xs font-bold text-slate-900 dark:text-white leading-snug">
                        {res.title}
                      </h5>
                    </div>
                    {res.link && (
                      <a
                        href={res.link}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                      >
                        Explore Resource <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};
