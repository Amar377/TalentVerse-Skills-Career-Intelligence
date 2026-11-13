import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, AlertCircle, Lightbulb, Sliders } from 'lucide-react';
import { api } from '../services/api';
import { InterviewQuestion, InterviewAnalysis } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Textarea, Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

export const InterviewCoachPage: React.FC = () => {
  const { success, error, warning } = useToast();

  const [targetRole, setTargetRole] = useState('Full Stack AI Engineer');
  const [interviewType, setInterviewType] = useState<'technical' | 'behavioral'>('technical');
  const [level, setLevel] = useState('Entry-level');

  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<InterviewAnalysis | null>(null);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInitial() {
      try {
        const history = await api.interviews.history();
        if (history.length > 0) {
          setEvaluation(history[0]);
        }
      } catch (err) {
        console.error('Failed to load initial interview state', err);
      } finally {
        setLoading(false);
      }
    }
    loadInitial();
  }, []);

  const handleGenerateQuestions = async () => {
    setIsGenerating(true);
    try {
      const res = await api.interviews.getQuestions({
        target_role: targetRole,
        interview_type: interviewType,
        level,
      });
      setQuestions(res.questions);
      if (res.questions.length > 0) {
        setSelectedQuestion(res.questions[0]);
      }
      success('Questions Ready', `Generated ${res.questions.length} ${interviewType} questions for ${targetRole}`);
    } catch (err: any) {
      error('Generation Failed', err.message || 'Could not fetch questions.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEvaluateAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQuestion) return;
    if (userAnswer.trim().length < 15) {
      warning('Answer too short', 'Please write at least a couple of sentences to receive comprehensive AI evaluation.');
      return;
    }

    setIsEvaluating(true);
    try {
      const res = await api.interviews.evaluate({
        target_role: targetRole,
        interview_type: interviewType,
        question: selectedQuestion.question,
        user_answer: userAnswer.trim(),
      });
      setEvaluation(res);
      success('Evaluation Complete! 🎯', `Your response scored ${res.answer_score}/100`);
    } catch (err: any) {
      error('Evaluation Failed', err.message || 'Could not evaluate response.');
    } finally {
      setIsEvaluating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          AI Interview Preparation & Coach
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Practice role-specific technical and behavioral questions. Receive objective scoring, highlight omitted principles, and read model answers.
        </p>
      </div>

      {/* Role & Interview Type Config */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-500" /> Interview Simulation Parameters
          </CardTitle>
          <CardDescription>
            Tailor questions to your target position and interview format.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <Input
                label="Target Role"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Full Stack AI Engineer"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Interview Type
              </label>
              <select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value as any)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              >
                <option value="technical">Technical Architecture & Coding</option>
                <option value="behavioral">Behavioral (STAR Method)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Seniority Level
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  <option value="Entry-level">Entry-level</option>
                  <option value="Junior">Junior</option>
                  <option value="Mid-level">Mid-level</option>
                  <option value="Senior">Senior</option>
                </select>
                <Button
                  onClick={handleGenerateQuestions}
                  variant="gradient"
                  size="sm"
                  isLoading={isGenerating}
                  className="shrink-0"
                >
                  Generate
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Practice Workspace: Questions List + Active Answer Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Questions Selector */}
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Select Practice Question:
          </span>
          {questions.map((q) => (
            <div
              key={q.id}
              onClick={() => {
                setSelectedQuestion(q);
                setUserAnswer('');
              }}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                selectedQuestion?.id === q.id
                  ? 'border-brand-500 bg-brand-50/30 dark:bg-brand-950/30 shadow-subtle'
                  : 'border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-navy-900'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <Badge variant={q.type === 'technical' ? 'brand' : 'cyan'} size="sm">
                  {q.type}
                </Badge>
                <Badge
                  variant={q.difficulty === 'Hard' ? 'danger' : q.difficulty === 'Medium' ? 'warning' : 'success'}
                  size="sm"
                >
                  {q.difficulty}
                </Badge>
              </div>
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-snug">
                {q.question}
              </p>
            </div>
          ))}
        </div>

        {/* Right Column: Question Details & Answer Input */}
        <div className="lg:col-span-2 space-y-6">
          {selectedQuestion ? (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="brand" size="sm">
                    {selectedQuestion.type.toUpperCase()}
                  </Badge>
                  <Badge variant="default" size="sm">
                    {selectedQuestion.difficulty}
                  </Badge>
                </div>
                <CardTitle className="text-lg leading-snug">{selectedQuestion.question}</CardTitle>
                {selectedQuestion.tips && (
                  <CardDescription className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-medium pt-1">
                    <Lightbulb className="w-3.5 h-3.5" />
                    <span>Coach Tip: {selectedQuestion.tips}</span>
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <form onSubmit={handleEvaluateAnswer} className="space-y-4">
                  <Textarea
                    label="Your Response"
                    placeholder="Type your structured answer here. Practice using concrete frameworks (STAR method for behavioral, architectural trade-offs for technical)..."
                    rows={8}
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    required
                  />

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-xs text-slate-400">
                      Evaluated for depth, missing concepts, and metrics.
                    </span>
                    <Button
                      type="submit"
                      variant="gradient"
                      isLoading={isEvaluating}
                      leftIcon={<Sparkles className="w-4 h-4" />}
                    >
                      Submit for Evaluation
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          ) : (
            <Card className="p-12 text-center text-slate-500">
              Select a question on the left to begin practice.
            </Card>
          )}

          {/* AI Feedback & Model Answer Dossier */}
          {evaluation && (
            <div className="space-y-6 animate-fade-in">
              <Card className="border-brand-500/30 bg-gradient-to-r from-white via-slate-50 to-brand-50/20 dark:from-navy-900 dark:via-navy-900 dark:to-brand-950/30">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <span className="text-xs font-mono uppercase tracking-widest text-brand-500 font-bold">
                      ✦ AI Evaluation Dossier
                    </span>
                    <CardTitle className="text-xl mt-1">Answer Quality Rating</CardTitle>
                  </div>
                  <div className="text-center p-3 rounded-2xl bg-white dark:bg-navy-950 border border-slate-200 dark:border-slate-800 min-w-[100px]">
                    <div className="text-[10px] font-bold uppercase text-slate-400">Score</div>
                    <div
                      className={`text-3xl font-black mt-0.5 ${
                        evaluation.answer_score >= 80
                          ? 'text-emerald-500'
                          : evaluation.answer_score >= 65
                          ? 'text-amber-500'
                          : 'text-rose-500'
                      }`}
                    >
                      {evaluation.answer_score}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950/60 text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed border border-slate-200/60 dark:border-slate-800">
                    <span className="font-semibold text-slate-900 dark:text-white">Coach Feedback: </span>
                    {evaluation.feedback}
                  </div>

                  {/* Strengths & Missing Concepts Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Strengths */}
                    <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-500/20">
                      <div className="text-xs font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" /> Observed Strengths
                      </div>
                      <ul className="space-y-1.5 text-xs text-emerald-900 dark:text-emerald-200">
                        {evaluation.strengths.map((str, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span>✓</span>
                            <span>{str}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Missing Concepts */}
                    <div className="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-500/20">
                      <div className="text-xs font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4" /> Missing Principles
                      </div>
                      <ul className="space-y-1.5 text-xs text-amber-900 dark:text-amber-200">
                        {evaluation.missing_concepts.map((mis, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span>!</span>
                            <span>{mis}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Model Answer */}
                  <div className="pt-2">
                    <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 mb-2 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4" /> Gold-Standard Model Answer:
                    </div>
                    <div className="p-4 rounded-xl bg-brand-50/30 dark:bg-brand-950/40 text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-mono leading-relaxed border border-brand-500/20 whitespace-pre-wrap">
                      {evaluation.suggested_answer}
                    </div>
                  </div>

                  {/* Practice Tasks */}
                  {evaluation.practice_tasks && evaluation.practice_tasks.length > 0 && (
                    <div className="pt-2">
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Next Drill Exercises:
                      </div>
                      <div className="space-y-1.5">
                        {evaluation.practice_tasks.map((task, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-950 text-xs text-slate-700 dark:text-slate-300"
                          >
                            <span className="font-semibold text-brand-500 mr-2">•</span>
                            {task}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
