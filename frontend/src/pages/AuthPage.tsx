import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Sparkles, ArrowRight, Lock, Mail, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, loginDemo, isLoading } = useAuth();

  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (mode === 'signin') {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      navigate('/app');
    } catch {
      // toast shown in auth context
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoClick = async () => {
    await loginDemo();
    navigate('/app');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative selection:bg-brand-500 selection:text-white">
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-brand-500/10 blur-[120px] rounded-full pointer-events-none" />

      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8 relative z-10">
        <Link to="/" className="inline-flex items-center gap-2.5 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-accent-cyan flex items-center justify-center text-white font-bold text-lg shadow-glow">
            ✦
          </div>
          <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
            TalentVerse 2.0
          </span>
        </Link>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Your Skills. Your Potential. Your Career, Intelligently Connected.
        </p>
      </div>

      {/* Main Form Card */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <Card className="p-2 sm:p-4 shadow-xl border-slate-200/90 dark:border-slate-800">
          {/* Mode Tabs */}
          <div className="flex border-b border-slate-100 dark:border-slate-800 p-2 gap-1 mb-4">
            <button
              onClick={() => setMode('signin')}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signin'
                  ? 'bg-brand-500 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode('signup')}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signup'
                  ? 'bg-brand-500 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          <CardContent className="pt-2">
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <Input
                  label="Full Name"
                  type="text"
                  placeholder="Alex Morgan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  leftIcon={<UserIcon className="w-4 h-4" />}
                  required
                />
              )}

              <Input
                label="Email Address"
                type="email"
                placeholder="alex.morgan@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={<Mail className="w-4 h-4" />}
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={<Lock className="w-4 h-4" />}
                required
              />

              <Button
                type="submit"
                variant="gradient"
                size="md"
                className="w-full mt-2"
                isLoading={submitting}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {mode === 'signin' ? 'Sign In to Workspace' : 'Create Free Account'}
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-slate-800" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-2 bg-white dark:bg-navy-900 text-slate-400">
                  Or test immediately
                </span>
              </div>
            </div>

            {/* Instant Demo Button */}
            <Button
              onClick={handleDemoClick}
              variant="secondary"
              size="md"
              className="w-full border-brand-500/20 text-brand-600 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-950/40 hover:bg-brand-100/50"
              leftIcon={<Sparkles className="w-4 h-4 text-brand-500" />}
              isLoading={isLoading}
            >
              Explore Sandbox with Pre-loaded Profile
            </Button>
          </CardContent>
        </Card>

        {/* Back Link */}
        <div className="text-center mt-6">
          <Link
            to="/"
            className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            ← Back to TalentVerse Home
          </Link>
        </div>
      </div>
    </div>
  );
};
