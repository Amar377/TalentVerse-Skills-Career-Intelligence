import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Compass, Crosshair, Sparkles, Mic2, UserCircle, BookmarkCheck, Settings, ChevronLeft, ChevronRight, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}) => {
  const { user, logout } = useAuth();

  const navigationSections = [
    {
      title: 'OVERVIEW',
      items: [
        { name: 'Dashboard', path: '/app', icon: LayoutDashboard },
      ],
    },
    {
      title: 'CAREER INTELLIGENCE',
      items: [
        { name: 'Resume Analyzer', path: '/app/resume-analyzer', icon: FileText },
        { name: 'Career Roadmap', path: '/app/roadmap', icon: Compass },
        { name: 'Job Matcher', path: '/app/job-matcher', icon: Crosshair },
        { name: 'Project Briefs', path: '/app/projects', icon: Sparkles },
        { name: 'Interview Coach', path: '/app/interview-coach', icon: Mic2 },
      ],
    },
    {
      title: 'ACCOUNT',
      items: [
        { name: 'My Profile', path: '/app/profile', icon: UserCircle },
        { name: 'Saved Reports', path: '/app/reports', icon: BookmarkCheck },
        { name: 'Settings', path: '/app/settings', icon: Settings },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 flex flex-col border-r border-brand-800 bg-brand-900 text-slate-100 backdrop-blur-xl transition-all duration-300 ${
          collapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-brand-800">
          <NavLink to="/app" className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-accent-amber flex items-center justify-center text-brand-900 font-bold text-lg shrink-0">
              ✦
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight text-slate-50 flex items-center gap-1.5">
                  TalentVerse
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-white/10 text-accent-amber font-semibold border border-white/10">
                    2.0
                  </span>
                </span>
                <span className="text-[11px] text-slate-300 font-medium">Career Intelligence</span>
              </div>
            )}
          </NavLink>

          {/* Desktop Collapse Button */}
          <button
            onClick={onToggle}
            className="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navigationSections.map((sec) => (
            <div key={sec.title} className="space-y-1">
              {!collapsed && (
                <div className="px-3 text-[10px] font-semibold tracking-[0.16em] text-slate-300/70 uppercase">
                  {sec.title}
                </div>
              )}
              {sec.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/app'}
                    onClick={onMobileClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                        isActive
                          ? 'bg-white/10 text-white font-semibold border border-white/10'
                          : 'text-slate-300 hover:text-white hover:bg-white/5'
                      }`
                    }
                    title={collapsed ? item.name : undefined}
                  >
                    <Icon className="w-5 h-5 shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </div>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-brand-800">
          <div
            className={`flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/10 ${
              collapsed ? 'flex-col gap-2' : ''
            }`}
          >
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-accent-amber text-brand-900 font-semibold text-xs flex items-center justify-center shrink-0">
                {(user?.full_name || 'U').charAt(0)}
              </div>
              {!collapsed && (
                <div className="flex flex-col truncate">
                  <span className="text-xs font-semibold text-slate-50 truncate">
                    {user?.full_name || 'Candidate'}
                  </span>
                  <span className="text-[10px] text-slate-300/70 truncate">{user?.email}</span>
                </div>
              )}
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

