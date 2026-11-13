import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, Sliders } from 'lucide-react';
import { api } from '../services/api';
import { ProjectBrief } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

export const ProjectRecommendationsPage: React.FC = () => {
  const { success, error } = useToast();

  const [projects, setProjects] = useState<ProjectBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedProject, setSelectedProject] = useState<ProjectBrief | null>(null);

  // Form State
  const [interests, setInterests] = useState('AI career intelligence, distributed systems, developer productivity');
  const [domain, setDomain] = useState('Full Stack & Applied AI');
  const [difficulty, setDifficulty] = useState('Intermediate');

  useEffect(() => {
    async function loadProjects() {
      try {
        const list = await api.projects.list();
        setProjects(list);
      } catch (err) {
        console.error('Failed to load projects', err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!interests.trim()) {
      error('Missing Field', 'Please describe your interests or domain.');
      return;
    }

    setGenerating(true);
    try {
      const res = await api.projects.generate({
        interests: interests.split(',').map((s) => s.trim()),
        domain,
        difficulty,
      });
      setProjects(res);
      success('Projects Generated', `Created ${res.length} portfolio architecture briefs.`);
    } catch (err: any) {
      error('Generation Failed', err.message || 'Could not generate project briefs.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-72 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Portfolio Project Recommendations
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Prove your capabilities to recruiters with production-grade portfolio architectures designed to demonstrate missing and in-demand skills.
        </p>
      </div>

      {/* Generator Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-500" /> Discover Portfolio Projects
          </CardTitle>
          <CardDescription>
            Specify your technical interest areas and preferred challenge level.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <Input
                label="Interests & Problem Areas"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="e.g. AI tools, cloud infrastructure, fintech"
                required
              />
            </div>

            <div>
              <Input
                label="Preferred Domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="e.g. Full Stack & AI, DevOps"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Difficulty
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                </select>
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

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {projects.map((proj) => (
          <Card
            key={proj.id}
            glow
            className="flex flex-col justify-between hover:-translate-y-1 transition-all duration-300"
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-2 mb-2">
                <Badge variant="cyan" size="sm">
                  {proj.domain}
                </Badge>
                <Badge
                  variant={
                    proj.difficulty === 'Advanced'
                      ? 'danger'
                      : proj.difficulty === 'Intermediate'
                      ? 'brand'
                      : 'success'
                  }
                  size="sm"
                >
                  {proj.difficulty}
                </Badge>
              </div>
              <CardTitle className="text-lg leading-snug">{proj.title}</CardTitle>
              <CardDescription className="line-clamp-2 mt-1.5 text-xs">
                {proj.problem_statement}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4 pt-0">
              {/* Core Features Preview */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Core Capabilities:
                </span>
                <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                  {proj.core_features.slice(0, 3).map((feat, fIdx) => (
                    <li key={fIdx} className="flex items-start gap-1.5 truncate">
                      <span className="text-brand-500">•</span>
                      <span className="truncate">{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Tech Stack Chips */}
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                  Tech Stack:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {proj.suggested_tech_stack.slice(0, 4).map((tech, tIdx) => (
                    <span
                      key={tIdx}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono"
                    >
                      {tech}
                    </span>
                  ))}
                  {proj.suggested_tech_stack.length > 4 && (
                    <span className="text-[10px] px-1.5 py-0.5 text-slate-400">
                      +{proj.suggested_tech_stack.length - 4} more
                    </span>
                  )}
                </div>
              </div>
            </CardContent>

            <div className="p-6 pt-0">
              <Button
                onClick={() => setSelectedProject(proj)}
                variant="secondary"
                size="sm"
                className="w-full"
              >
                View Architecture Brief
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Project Details Modal */}
      {selectedProject && (
        <Modal
          isOpen={Boolean(selectedProject)}
          onClose={() => setSelectedProject(null)}
          title={selectedProject.title}
          description={`${selectedProject.domain} • ${selectedProject.difficulty} Level`}
          maxWidth="2xl"
          footer={
            <Button onClick={() => setSelectedProject(null)} variant="secondary" size="sm">
              Close Brief
            </Button>
          }
        >
          <div className="space-y-5 text-xs sm:text-sm">
            {/* Problem Statement */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-1">
                Problem Statement & Impact:
              </h5>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-navy-950 p-3.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
                {selectedProject.problem_statement}
              </p>
            </div>

            {/* Target Personas */}
            {selectedProject.target_users && selectedProject.target_users.length > 0 && (
              <div>
                <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-1.5">
                  Target User Personas:
                </h5>
                <div className="flex flex-wrap gap-2">
                  {selectedProject.target_users.map((u, idx) => (
                    <Badge key={idx} variant="default" size="sm">
                      {u}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Core Features */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-2">
                Core Engineering Features:
              </h5>
              <ul className="space-y-1.5 text-slate-700 dark:text-slate-300">
                {selectedProject.core_features.map((f, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Full Tech Stack */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-2">
                Suggested Modern Tech Stack:
              </h5>
              <div className="flex flex-wrap gap-2">
                {selectedProject.suggested_tech_stack.map((t, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300 font-mono text-xs border border-brand-200 dark:border-brand-800"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Implementation Milestones */}
            {selectedProject.implementation_milestones && (
              <div>
                <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-2">
                  Execution Phases:
                </h5>
                <div className="space-y-2">
                  {selectedProject.implementation_milestones.map((m, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-950/60 text-slate-700 dark:text-slate-300 text-xs"
                    >
                      <span className="font-semibold text-brand-600 dark:text-brand-400 mr-2">
                        Phase {idx + 1}:
                      </span>
                      {m}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Portfolio Resume Blurb */}
            {selectedProject.portfolio_description && (
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-xs mb-1.5">
                  Resume / GitHub Portfolio Blurb:
                </h5>
                <p className="p-3 rounded-xl bg-brand-50/50 dark:bg-brand-950/40 text-brand-900 dark:text-brand-200 text-xs font-mono border border-brand-500/20">
                  {selectedProject.portfolio_description}
                </p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
