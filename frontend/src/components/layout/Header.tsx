import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Menu, Sun, Moon, Bell, Sparkles, UserCircle, Settings, LogOut, ChevronRight } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { useAIProvider } from '../../hooks/useAIProvider';

interface HeaderProps {
  onMobileMenuClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMobileMenuClick }) => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const location = useLocation();
  const { providers, preferredProvider, selectProvider, loadingProviders } = useAIProvider();

  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const routeTitles: Record<string, string> = {
    '/app': 'Career Intelligence Dashboard',
    '/app/resume-analyzer': 'Resume Analyzer & Profiler',
    '/app/roadmap': 'Interactive Career Roadmap',
    '/app/job-matcher': 'Job Fit Matcher & Gap Analysis',
    '/app/projects': 'Portfolio Project Recommendations',
    '/app/interview-coach': 'AI Interview Preparation & Coach',
    '/app/profile': 'Candidate Master Profile',
    '/app/reports': 'Saved Intelligence Reports',
    '/app/settings': 'Platform & Model Settings',
  };

  const currentTitle = routeTitles[location.pathname] || 'TalentVerse';

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-navy-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between transition-colors">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMobileMenuClick}
          className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
          <Link to="/app" className="hover:text-slate-600 dark:hover:text-slate-200 hidden sm:inline">
            TalentVerse
          </Link>
          <ChevronRight className="w-3.5 h-3.5 hidden sm:inline" />
          <span className="text-slate-800 dark:text-slate-100 font-semibold truncate text-sm">
            {currentTitle}
          </span>
        </div>
      </div>

      {/* Right: Model Selection, Theme, Notifications, User */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-brand-500 shrink-0" />
          <label htmlFor="header-ai-model" className="sr-only">Preferred AI model</label>
          <select
            id="header-ai-model"
            aria-label="Preferred AI model"
            title="Preferred model is tried first; other configured providers are fallbacks."
            value={preferredProvider}
            onChange={(event) => selectProvider(event.target.value)}
            disabled={loadingProviders || providers.length === 0}
            className="max-w-[150px] sm:max-w-[210px] rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs text-slate-700 dark:text-slate-200 px-2 py-1.5 disabled:opacity-60"
          >
            {providers.length === 0 ? (
              <option value="groq">
                {loadingProviders ? 'Loading AI models…' : 'No configured AI models'}
              </option>
            ) : (
              providers.map((provider) => (
                <option key={provider.name} value={provider.name}>
                  {provider.name.toUpperCase()} · {provider.model}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-brand-600" />}
        </button>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors relative"
          >
            <Bell className="w-4 h-4" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-4 z-50 animate-fade-in">
              <div className="pb-3 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Notifications
                </span>
              </div>
              <div className="py-6 text-center text-xs text-slate-500">
                You’re all caught up. Notifications will appear here when available.
              </div>
            </div>
          )}
        </div>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileMenuOpen(!profileMenuOpen)}
            className="flex items-center gap-2 p-1 pl-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-accent-cyan text-white font-bold text-xs flex items-center justify-center shadow-xs">
              {(user?.full_name || 'U').charAt(0)}
            </div>
          </button>

          {profileMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-2 z-50 animate-fade-in">
              <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                <div className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                  {user?.full_name || 'Candidate'}
                </div>
                <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
              </div>

              <div className="py-1">
                <Link
                  to="/app/profile"
                  onClick={() => setProfileMenuOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <UserCircle className="w-4 h-4" />
                  My Candidate Profile
                </Link>
                <Link
                  to="/app/settings"
                  onClick={() => setProfileMenuOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <Settings className="w-4 h-4" />
                  Settings & API Keys
                </Link>
              </div>

              <div className="pt-1 border-t border-slate-100 dark:border-slate-800">
                <button
                  onClick={() => {
                    setProfileMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
