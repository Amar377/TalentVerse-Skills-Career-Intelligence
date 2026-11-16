export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_demo: boolean;
  created_at?: string;
}

export interface ResumeExperienceAnalysis {
  company?: string | null;
  job_title?: string | null;
  duration?: string | null;
  responsibilities: string[];
  achievements: string[];
  missing_measurable_results: string[];
  suggestions: string[];
}

export interface ResumeEducationAnalysis {
  degree?: string | null;
  institution?: string | null;
  graduation_year?: string | null;
}

export interface ResumeProjectAnalysis {
  name?: string | null;
  technologies: string[];
  description?: string | null;
  achievements: string[];
  suggestions: string[];
}

export interface ResumeAnalysisDetails {
  current_role?: string | null;
  total_experience?: string | null;
  summary_quality_analysis: string;
  summary_improvement_suggestions: string[];
  skills_by_category: Record<string, string[]>;
  target_role_skill_alignment: string[];
  experience_analysis: ResumeExperienceAnalysis[];
  education_analysis: ResumeEducationAnalysis[];
  projects_analysis: ResumeProjectAnalysis[];
  project_improvement_suggestions: string[];
  ats_score?: number | null;
  ats_score_explanation: string;
  ats_matched_keywords: string[];
  ats_missing_keywords: string[];
  ats_formatting_issues: string[];
  ats_section_completeness: Record<string, boolean>;
}

export interface CandidateProfile {
  id?: string;
  user_id?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  target_role?: string;
  experience_level: string;
  summary: string;
  skills: string[];
  soft_skills: string[];
  experience: string[];
  education: string[];
  certifications: string[];
  projects: string[];
  missing_information: string[];
  strengths: string[];
  improvement_recommendations: string[];
  readiness_score: number;
  current_role?: string | null;
  total_experience?: string | null;
  summary_quality_analysis?: string;
  summary_improvement_suggestions?: string[];
  skills_by_category?: Record<string, string[]>;
  target_role_skill_alignment?: string[];
  experience_analysis?: ResumeExperienceAnalysis[];
  education_analysis?: ResumeEducationAnalysis[];
  projects_analysis?: ResumeProjectAnalysis[];
  project_improvement_suggestions?: string[];
  ats_score?: number | null;
  ats_score_explanation?: string;
  ats_matched_keywords?: string[];
  ats_missing_keywords?: string[];
  ats_formatting_issues?: string[];
  ats_section_completeness?: Record<string, boolean>;
  resume_analysis?: ResumeAnalysisDetails;
}

export interface MilestoneItem {
  week: number;
  title: string;
  learning_tasks: string[];
  deliverable: string;
  success_criteria: string[];
  completed: boolean;
}

export interface CareerRoadmap {
  id: string;
  user_id?: string;
  career_goal: string;
  experience_level: string;
  duration_weeks: number;
  skill_gaps: string[];
  milestones: MilestoneItem[];
  assumptions_or_missing_information: string[];
  recommended_resources: { title: string; type: string; link?: string }[];
  progress_percent: number;
  created_at?: string;
  updated_at?: string;
}

export interface JobMatch {
  id: string;
  user_id?: string;
  target_role: string;
  company?: string;
  job_description: string;
  match_score_percent: number;
  matching_skills: string[];
  missing_or_unverified_skills: string[];
  experience_relevance: string[];
  education_relevance: string[];
  strengths: string[];
  evidence: string[];
  improvement_actions: string[];
  caveat: string;
  created_at?: string;
}

export interface ProjectBrief {
  id: string;
  user_id?: string;
  title: string;
  problem_statement: string;
  domain: string;
  difficulty: string;
  target_users: string[];
  core_features: string[];
  suggested_tech_stack: string[];
  implementation_milestones: string[];
  evaluation_metrics: string[];
  portfolio_description?: string;
  created_at?: string;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  type: string;
  difficulty: string;
  key_topics: string[];
  tips?: string;
}

export interface InterviewAnalysis {
  id: string;
  user_id?: string;
  target_role: string;
  interview_type: string;
  question: string;
  user_answer: string;
  answer_score: number;
  feedback: string;
  strengths: string[];
  improvement_areas: string[];
  missing_concepts: string[];
  suggested_answer: string;
  practice_tasks: string[];
  next_session_focus: string;
  created_at?: string;
}

export interface SavedReport {
  id: string;
  user_id?: string;
  report_type: 'resume' | 'roadmap' | 'job_match' | 'project' | 'interview';
  title: string;
  summary?: string;
  score?: number;
  tags: string[];
  data: any;
  created_at?: string;
}

export interface SkillDistribution {
  category: string;
  name: string;
  type: 'technical' | 'soft';
}

export interface RecentActivity {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  score?: number;
}

export interface DashboardStats {
  candidate_name: string;
  target_role: string;
  career_readiness_score: number;
  skills_count: number;
  completed_milestones: number;
  total_milestones: number;
  recent_job_fit_score?: number;
  skills_distribution: SkillDistribution[];
  recent_activities: RecentActivity[];
  recommended_actions: { title: string; action: string; reason: string; urgency: string }[];
}

export interface ProviderInfo {
  name: string;
  model: string;
  configured: boolean;
  key_name: string;
}

export interface SystemStatus {
  priority: string[];
  providers: ProviderInfo[];
  active_provider?: string;
  active_model?: string;
  status: string;
}
