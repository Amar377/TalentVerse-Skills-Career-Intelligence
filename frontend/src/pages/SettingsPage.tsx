import React, { useState, useEffect } from 'react';
import { Sun, Moon, Sparkles, ShieldCheck, CheckCircle2, Trash2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { SystemStatus } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();

  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  useEffect(() => {
    async function loadSystem() {
      try {
        const s = await api.system.getStatus();
        setSystemStatus(s);
      } catch (err) {
        console.error('Failed to load system status', err);
      } finally {
        setLoadingStatus(false);
      }
    }
    loadSystem();
  }, []);

  const handleClearSession = () => {
    logout();
    window.location.assign('/');
  };

  return (
    <div className="space-y-8 pb-16 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Platform & Model Settings
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Configure appearance, view multi-provider AI engine fallback status, and manage account security.
        </p>
      </div>

      {/* 1. Appearance Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sun className="w-4 h-4 text-amber-500" /> Interface Appearance
          </CardTitle>
          <CardDescription>Select your preferred color theme.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 max-w-md">
            <button
              onClick={() => setTheme('light')}
              className={`p-4 rounded-2xl border text-left flex flex-col justify-between transition-all ${
                theme === 'light'
                  ? 'border-brand-500 bg-brand-50/20 text-brand-900 dark:text-brand-100 ring-2 ring-brand-500/20'
                  : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
              }`}
            >
              <Sun className="w-6 h-6 text-amber-500 mb-2" />
              <div className="font-bold text-sm">Light Mode</div>
              <div className="text-xs text-slate-400 mt-0.5">Crisp, high-contrast daylight theme</div>
            </button>

            <button
              onClick={() => setTheme('dark')}
              className={`p-4 rounded-2xl border text-left flex flex-col justify-between transition-all ${
                theme === 'dark'
                  ? 'border-brand-500 bg-brand-950/20 text-brand-100 ring-2 ring-brand-500/20'
                  : 'border-slate-200 dark:border-slate-800 hover:border-slate-700'
              }`}
            >
              <Moon className="w-6 h-6 text-brand-400 mb-2" />
              <div className="font-bold text-sm">Dark Mode</div>
              <div className="text-xs text-slate-400 mt-0.5">Deep navy & obsidian studio theme</div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* 2. AI Multi-Provider Status Dashboard */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-500" /> Multi-Provider AI Fallback Engine
            </CardTitle>
            <Badge
              variant={loadingStatus ? 'outline' : systemStatus?.providers.some((provider) => provider.configured) ? 'success' : 'warning'}
              size="sm"
            >
              {loadingStatus
                ? 'Checking'
                : !systemStatus
                  ? 'Status unavailable'
                  : systemStatus.providers.some((provider) => provider.configured)
                    ? 'Provider keys loaded'
                    : 'No provider configured'}
            </Badge>
          </div>
          <CardDescription>
            TalentVerse dynamically cascades requests across configured providers in priority order.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/60 dark:border-slate-800 text-xs font-mono">
            <span className="text-slate-400 block mb-1">Configured Priority Cascade:</span>
            <span className="text-brand-600 dark:text-brand-400 font-semibold">
              {systemStatus?.priority.join('  →  ')}
            </span>
          </div>

          <div className="space-y-2.5">
            {systemStatus?.providers.map((p) => (
              <div
                key={p.name}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200/70 dark:border-slate-800 bg-white dark:bg-navy-900"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      p.configured ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300 dark:bg-slate-700'
                    }`}
                  />
                  <div>
                    <div className="font-bold text-xs uppercase text-slate-800 dark:text-slate-200">
                      {p.name}
                    </div>
                    <div className="text-[11px] font-mono text-slate-400">{p.model}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  {p.configured ? (
                    <Badge variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3" /> Key Loaded ({p.key_name})
                    </Badge>
                  ) : (
                    <Badge variant="outline" size="sm">
                      Not Configured in .env
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 3. Account Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" /> Account Security & Session
          </CardTitle>
          <CardDescription>Current signed in credentials and sandbox management.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950">
              <span className="text-slate-400 block">User Name</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {user?.full_name || 'Candidate'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950">
              <span className="text-slate-400 block">Email</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{user?.email}</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Clear your active session and reset local workspace state.
            </span>
            <Button onClick={handleClearSession} variant="danger" size="sm" leftIcon={<Trash2 className="w-3.5 h-3.5" />}>
              Reset Local Session
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
