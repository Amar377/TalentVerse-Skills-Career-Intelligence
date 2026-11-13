import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';

import { LandingPage } from './pages/LandingPage';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResumeAnalyzerPage } from './pages/ResumeAnalyzerPage';
import { CareerRoadmapPage } from './pages/CareerRoadmapPage';
import { JobMatcherPage } from './pages/JobMatcherPage';
import { ProjectRecommendationsPage } from './pages/ProjectRecommendationsPage';
import { InterviewCoachPage } from './pages/InterviewCoachPage';
import { ProfilePage } from './pages/ProfilePage';
import { SavedReportsPage } from './pages/SavedReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Landing & Marketing */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/auth" element={<AuthPage />} />

              {/* Protected App Workspace */}
              <Route path="/app" element={<AppLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="resume-analyzer" element={<ResumeAnalyzerPage />} />
                <Route path="roadmap" element={<CareerRoadmapPage />} />
                <Route path="job-matcher" element={<JobMatcherPage />} />
                <Route path="projects" element={<ProjectRecommendationsPage />} />
                <Route path="interview-coach" element={<InterviewCoachPage />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="reports" element={<SavedReportsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
};

export default App;
