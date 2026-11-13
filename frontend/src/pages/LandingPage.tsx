import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, FileText, Compass, Crosshair, Code2, Mic2, CheckCircle2, ChevronDown, ShieldCheck, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Button } from '../components/ui/Button';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, loginDemo, isLoading } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const handleDemoStart = async () => {
    if (user) {
      navigate('/app');
    } else {
      await loginDemo();
      navigate('/app');
    }
  };

  const faqs = [
    {
      q: 'How does TalentVerse analyze my resume?',
      a: 'TalentVerse extracts text from PDF, DOCX, or text resumes, then uses structured AI analysis to identify listed skills, experience, and information gaps.',
    },
    {
      q: 'Which AI providers are supported?',
      a: 'TalentVerse can try configured Google Gemini, Groq, OpenAI, and Mistral providers in order. If every configured provider is unavailable, it reports that AI analysis cannot run.',
    },
    {
      q: 'Can I track my learning milestones over time?',
      a: 'Yes! The Career Roadmap generates chronological weekly milestones with concrete learning tasks, deliverables, and success criteria. You can check off completed milestones and track your overall job-readiness progress.',
    },
    {
      q: 'How is the Job Match score calculated?',
      a: 'The Job Matcher compares your verified candidate profile against specific job descriptions, evaluating required technical stacks, experience relevance, and education alignment. It explicitly separates matching skills from missing gaps and provides actionable next steps.',
    },
    {
      q: 'Is my data private and secure?',
      a: 'Workspace data is associated with your account. Resume text is sent to the AI providers configured by the operator for analysis; review those providers’ data policies before submitting sensitive information.',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 selection:bg-brand-500 selection:text-white transition-colors">
      {/* 1. Header Navigation */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-navy-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-accent-cyan flex items-center justify-center text-white font-bold text-base shadow-glow">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
              TalentVerse
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-brand-50 dark:bg-brand-950/70 text-brand-600 dark:text-brand-300 font-semibold border border-brand-200 dark:border-brand-800">
                2.0
              </span>
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600 dark:text-slate-400">
            <a href="#features" className="hover:text-slate-900 dark:hover:text-white transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
              How It Works
            </a>
            <a href="#benefits" className="hover:text-slate-900 dark:hover:text-white transition-colors">
              Benefits
            </a>
            <a href="#faq" className="hover:text-slate-900 dark:hover:text-white transition-colors">
              FAQ
            </a>
          </nav>

          {/* CTA Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {user ? (
              <Button onClick={() => navigate('/app')} variant="gradient" size="sm">
                Open Workspace <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            ) : (
              <>
                <Link to="/auth">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Button onClick={handleDemoStart} variant="gradient" size="sm" isLoading={isLoading}>
                  Explore Demo <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative pt-20 pb-28 md:pt-28 md:pb-36 overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-brand-500/15 dark:bg-brand-600/20 blur-[130px] rounded-full pointer-events-none" />
        <div className="absolute top-1/3 left-1/3 w-[400px] h-[300px] bg-accent-cyan/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-50 dark:bg-brand-950/60 border border-brand-200/80 dark:border-brand-800/80 text-xs font-semibold text-brand-700 dark:text-brand-300 mb-6 shadow-xs animate-fade-in">
            <Sparkles className="w-3.5 h-3.5 text-brand-500 animate-pulse" />
            <span>AI-Powered Career Intelligence SaaS</span>
            <span className="w-1 h-1 rounded-full bg-brand-400"></span>
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">v2.0 Release</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-[1.08] mb-6">
            Turn Your Skills Into Your{' '}
            <span className="bg-gradient-to-r from-brand-600 via-indigo-600 to-accent-cyan bg-clip-text text-transparent">
              Next Career Opportunity.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
            Discover your strengths, identify skill gaps, build your career roadmap, and become job-ready with intelligent AI-powered career guidance.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Button
              onClick={() => navigate('/auth')}
              variant="gradient"
              size="lg"
              className="w-full sm:w-auto px-7"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Get Started Free
            </Button>
            <Link to="/auth" className="w-full sm:w-auto">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto px-7">
                Sign In to Platform
              </Button>
            </Link>
          </div>


        </div>
      </section>

      {/* 3. Platform Capabilities & Credibility */}
      <section className="py-12 border-y border-slate-200/80 dark:border-slate-800/80 bg-white/50 dark:bg-navy-900/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">Multi-AI</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Gemini, Groq & OpenAI Providers</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">Resume Parsing</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">PDF, DOCX & Plain Text Extraction</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">100% Real</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Evidence-Based Matching & Feedback</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">Active Plan</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Interactive Checklists & Progress Telemetry</div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Core Features Grid */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Comprehensive Career Suite
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-2 tracking-tight">
            Everything you need to master your career transition.
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mt-3 text-sm sm:text-base">
            Engineered from the ground up for ambitious engineers, students, and professionals seeking clarity and velocity.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400 mb-5">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Resume Analyzer</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Drag and drop PDF or DOCX resumes. Automatically extract technical skills, soft skills, project highlights, missing data, and targeted improvement actions.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-5">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Career Roadmap</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Generate structured, week-by-week learning milestones based on your target role and experience. Check off milestones as you build deliverables.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-cyan-50 dark:bg-cyan-950 flex items-center justify-center text-cyan-600 dark:text-cyan-400 mb-5">
              <Crosshair className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Job Matcher</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Paste actual job postings to compute fit percentage. Uncover matching skills versus missing competencies, with concrete evidence and preparation tips.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-violet-50 dark:bg-violet-950 flex items-center justify-center text-violet-600 dark:text-violet-400 mb-5">
              <Code2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Portfolio Recommendations</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Discover industry-grade portfolio projects tailored to your interests and level. Includes problem statements, core features, architecture, and evaluation benchmarks.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-5">
              <Mic2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Interview Coach</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Practice role-specific technical and behavioral questions. Submit your responses to receive instant objective ratings, missing concepts, and gold-standard model answers.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="rounded-2xl p-7 bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800/90 shadow-subtle hover:border-brand-500/40 hover:shadow-glow transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950 flex items-center justify-center text-amber-600 dark:text-amber-400 mb-5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Saved Reports & Exports</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Every analysis, roadmap, and interview session is automatically archived. Filter, export, and download your career intelligence dossier anytime.
            </p>
          </div>
        </div>
      </section>

      {/* 5. How It Works (Workflow) */}
      <section id="how-it-works" className="py-24 border-t border-slate-200/80 dark:border-slate-800/80 bg-slate-100/40 dark:bg-navy-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              The Talent Acceleration Loop
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-2 tracking-tight">
              From current skills to hired, in 4 steps.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 relative">
              <span className="text-3xl font-extrabold font-mono text-brand-500/30">01</span>
              <h4 className="text-base font-bold text-slate-900 dark:text-white mt-2 mb-1">Upload & Analyze</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Provide your resume to extract skills, certifications, and calculate your baseline career readiness score.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 relative">
              <span className="text-3xl font-extrabold font-mono text-brand-500/30">02</span>
              <h4 className="text-base font-bold text-slate-900 dark:text-white mt-2 mb-1">Generate Roadmap</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Select your target role and get an actionable week-by-week sprint plan with concrete deliverables.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 relative">
              <span className="text-3xl font-extrabold font-mono text-brand-500/30">03</span>
              <h4 className="text-base font-bold text-slate-900 dark:text-white mt-2 mb-1">Build & Verify</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Develop portfolio projects that demonstrate production skills and practice mock technical interviews.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 relative">
              <span className="text-3xl font-extrabold font-mono text-brand-500/30">04</span>
              <h4 className="text-base font-bold text-slate-900 dark:text-white mt-2 mb-1">Match & Apply</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Benchmark your profile against target jobs to ensure high fit scores before submitting applications.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Benefits for Students & Professionals */}
      <section id="benefits" className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 rounded-3xl bg-gradient-to-br from-brand-950/20 to-slate-900/10 dark:from-brand-950/40 dark:to-navy-900 border border-brand-500/20">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              For Students & New Grads
            </span>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-2 mb-4">
              Bridge the gap between coursework and industry hiring.
            </h3>
            <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Transform academic coursework into high-signal production project descriptions.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Identify specific industry libraries and patterns missing from your curriculum.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Prepare for entry-level and new-grad engineering screenings with structured STAR answers.</span>
              </li>
            </ul>
          </div>

          <div className="p-8 rounded-3xl bg-gradient-to-br from-indigo-950/20 to-slate-900/10 dark:from-indigo-950/40 dark:to-navy-900 border border-indigo-500/20">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              For Working Professionals
            </span>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-2 mb-4">
              Accelerate role promotions and strategic pivots.
            </h3>
            <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>Deconstruct senior job requirements and close unverified system architecture gaps.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>Simulate high-stakes technical deep-dives with AI evaluating trade-offs and metrics.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>Save and organize multiple targeted resume profiles for distinct domain opportunities.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 7. FAQ Section */}
      <section id="faq" className="py-24 border-t border-slate-200/80 dark:border-slate-800/80 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Answers & Clarity
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-2">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 overflow-hidden"
            >
              <button
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full p-5 text-left flex items-center justify-between gap-4 font-semibold text-slate-900 dark:text-white"
              >
                <span>{faq.q}</span>
                <ChevronDown
                  className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                    activeFaq === idx ? 'rotate-180 text-brand-500' : ''
                  }`}
                />
              </button>
              {activeFaq === idx && (
                <div className="px-5 pb-5 text-sm text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800/60 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 8. Final Conversion CTA */}
      <section className="py-20 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative rounded-3xl p-8 sm:p-14 bg-gradient-to-r from-brand-900 via-indigo-900 to-navy-900 border border-brand-500/30 text-center text-white shadow-2xl overflow-hidden">
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-accent-cyan/20 blur-3xl rounded-full"></div>
            <div className="relative z-10 max-w-2xl mx-auto">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
                Ready to take control of your career trajectory?
              </h2>
              <p className="text-sm sm:text-base text-slate-200 mb-8 leading-relaxed">
                Join ambitious engineers using TalentVerse 2.0 to turn raw skills into verifiable job offers.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button
                  onClick={handleDemoStart}
                  variant="gradient"
                  size="lg"
                  className="w-full sm:w-auto px-8"
                  isLoading={isLoading}
                >
                  Explore Live Demo
                </Button>
                <Link to="/auth" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto px-8 text-white border-white/30 hover:bg-white/10">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 9. Professional Footer */}
      <footer className="border-t border-slate-200/80 dark:border-slate-800/80 py-12 bg-white dark:bg-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 to-accent-cyan text-white text-xs font-bold flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-white">TalentVerse</span>
            <span className="text-xs text-slate-400">© 2026. All rights reserved.</span>
          </div>

          <div className="text-xs text-slate-500 flex items-center gap-6">
            <span>Powered by Configured AI Providers</span>
            <a href="#features" className="hover:text-slate-800 dark:hover:text-slate-200">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-slate-800 dark:hover:text-slate-200">
              Workflow
            </a>
            <Link to="/app" className="hover:text-slate-800 dark:hover:text-slate-200">
              Dashboard
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};



