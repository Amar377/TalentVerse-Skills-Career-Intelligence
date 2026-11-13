import {
  User,
  CandidateProfile,
  CareerRoadmap,
  JobMatch,
  ProjectBrief,
  InterviewQuestion,
  InterviewAnalysis,
  SavedReport,
  DashboardStats,
  SystemStatus,
} from '../types';

const API_BASE = '/api/v1';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('talentverse_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = 'An unexpected error occurred.';
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorData.message || errorMsg;
    } catch {
      errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    }
    throw new ApiError(errorMsg, response.status);
  }

  // Handle 204 or empty response
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Authentication
  auth: {
    async register(data: { email: string; password: string; full_name: string }) {
      return request<{ access_token: string; user: User }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async login(data: { email: string; password: string }) {
      return request<{ access_token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async demoLogin() {
      return request<{ access_token: string; user: User }>('/auth/demo', {
        method: 'POST',
      });
    },
    async getMe(): Promise<User> {
      return request<User>('/auth/me');
    },
  },

  // Resumes
  resumes: {
    async upload(file: File): Promise<{ profile: CandidateProfile; raw_text: string; provider_used: string | null; model_used: string | null }> {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('talentverse_token');
      const response = await fetch(`${API_BASE}/resumes/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!response.ok) {
        let msg = 'Failed to analyze resume file.';
        try {
          const err = await response.json();
          msg = err.detail || msg;
        } catch {}
        throw new ApiError(msg, response.status);
      }
      return response.json();
    },

    async analyzeText(resume_text: string) {
      return request<{ profile: CandidateProfile; raw_text: string; provider_used: string | null; model_used: string | null }>('/resumes/analyze-text', {
        method: 'POST',
        body: JSON.stringify({ resume_text }),
      });
    },

    async getLatest() {
      return request<{ profile: CandidateProfile; raw_text: string; provider_used: string | null; model_used: string | null } | null>('/resumes/latest');
    },
  },

  // Career Roadmaps
  roadmaps: {
    async generate(data: { skills: string[]; career_goal: string; experience_level: string; duration_weeks: number }): Promise<CareerRoadmap> {
      return request<CareerRoadmap>('/roadmaps/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async getLatest(): Promise<CareerRoadmap | null> {
      return request<CareerRoadmap | null>('/roadmaps/latest');
    },
    async list(): Promise<CareerRoadmap[]> {
      return request<CareerRoadmap[]>('/roadmaps');
    },
    async toggleMilestone(roadmapId: string, week: number, completed: boolean): Promise<CareerRoadmap> {
      return request<CareerRoadmap>(`/roadmaps/${roadmapId}/milestone`, {
        method: 'PUT',
        body: JSON.stringify({ week, completed }),
      });
    },
  },

  // Job Matcher
  jobs: {
    async match(data: { job_description: string; target_role?: string; company?: string; profile_id?: string; custom_profile?: any }): Promise<JobMatch> {
      return request<JobMatch>('/jobs/match', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async getLatest(): Promise<JobMatch> {
      return request<JobMatch>('/jobs/latest');
    },
    async list(): Promise<JobMatch[]> {
      return request<JobMatch[]>('/jobs');
    },
  },

  // Projects
  projects: {
    async generate(data: { interests: string[]; skills?: string[]; domain?: string; difficulty?: string }): Promise<ProjectBrief[]> {
      return request<ProjectBrief[]>('/projects/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async list(): Promise<ProjectBrief[]> {
      return request<ProjectBrief[]>('/projects');
    },
  },

  // Interviews
  interviews: {
    async getQuestions(data: { target_role: string; interview_type: string; level: string }): Promise<{ target_role: string; questions: InterviewQuestion[] }> {
      return request<{ target_role: string; questions: InterviewQuestion[] }>('/interviews/questions', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async evaluate(data: { target_role: string; interview_type: string; question: string; user_answer: string }): Promise<InterviewAnalysis> {
      return request<InterviewAnalysis>('/interviews/evaluate', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    async history(): Promise<InterviewAnalysis[]> {
      return request<InterviewAnalysis[]>('/interviews/history');
    },
  },

  // Candidate Profiles
  profiles: {
    async getMyProfile(): Promise<CandidateProfile> {
      return request<CandidateProfile>('/profiles/me');
    },
    async updateMyProfile(data: Partial<CandidateProfile>): Promise<CandidateProfile> {
      return request<CandidateProfile>('/profiles/me', {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },
    async list(): Promise<CandidateProfile[]> {
      return request<CandidateProfile[]>('/profiles');
    },
  },

  // Saved Reports
  reports: {
    async list(report_type?: string): Promise<SavedReport[]> {
      const query = report_type ? `?report_type=${report_type}` : '';
      return request<SavedReport[]>(`/reports${query}`);
    },
    async get(id: string): Promise<SavedReport> {
      return request<SavedReport>(`/reports/${id}`);
    },
    async delete(id: string): Promise<{ status: string }> {
      return request<{ status: string }>(`/reports/${id}`, {
        method: 'DELETE',
      });
    },
  },

  // Analytics
  analytics: {
    async getDashboard(): Promise<DashboardStats> {
      return request<DashboardStats>('/analytics/dashboard');
    },
  },

  // System
  system: {
    async getStatus(): Promise<SystemStatus> {
      return request<SystemStatus>('/system/status');
    },
  },
};
