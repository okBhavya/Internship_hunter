const API_BASE = '/api';

export interface User {
  id: number;
  name: string;
  email: string;
  phone: string;
  location: string;
  citizenship: string;
  requires_sponsorship: boolean;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  availability: string;
  preferred_job_type: string;
  education_entries: Education[];
  skills: Skill[];
  projects: Project[];
  experiences: Experience[];
  certifications: Certification[];
  resumes: Resume[];
}

export interface Education {
  id: number;
  university: string;
  degree: string;
  field_of_study: string;
  location: string;
  start_date: string;
  end_date: string;
  gpa: string;
  is_current: boolean;
}

export interface Skill {
  id: number;
  name: string;
  category: string;
  proficiency: string;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  technologies: string;
  url: string;
  start_date: string;
  end_date: string;
}

export interface Experience {
  id: number;
  company: string;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  description: string;
  is_current: boolean;
}

export interface Certification {
  id: number;
  name: string;
  issuer: string;
  date_obtained: string;
  url: string;
}

export interface Resume {
  id: number;
  filename: string;
  file_path: string;
  is_primary: boolean;
  uploaded_at: string;
}

export interface Job {
  id: number;
  external_id: string;
  title: string;
  company: string;
  location: string;
  remote_type: string;
  employment_type: string;
  internship_or_fulltime: string;
  country: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  description: string;
  requirements: string;
  skills: string[];
  experience_required: string;
  visa_information: string;
  sponsorship_information: string;
  application_url: string;
  source_name: string;
  source_url: string;
  date_posted: string;
  deadline: string;
  is_duplicate: boolean;
  discovered_at: string;
}

export interface JobMatch {
  id: number;
  job_id: number;
  fit_score: number;
  technical_match: number;
  role_match: number;
  experience_match: number;
  education_match: number;
  location_match: number;
  authorization_match: number;
  project_match: number;
  feasibility_match: number;
  missing_skills: string[];
  strengths: string[];
  concerns: string[];
  recommendation: string;
  explanation: string;
  matched_at: string;
}

export interface Application {
  id: number;
  job_id: number;
  user_id: number;
  status: string;
  resume_version: string;
  cover_letter: string;
  notes: string;
  interview_dates: any[];
  follow_up_date: string;
  date_discovered: string;
  date_applied: string | null;
  last_updated: string;
  job?: Job;
  materials?: ApplicationMaterials;
}

export interface ApplicationMaterials {
  resume: string;
  cover_letter: string;
  summary: string;
  skills_summary: string;
  why_company: string;
  why_role: string;
  recruiter_message: string;
  question_answers: any[];
}

export interface AgentRun {
  id: number;
  agent_name: string;
  status: string;
  task: string;
  input_summary: string;
  actions: any[];
  decisions: any[];
  outputs: any;
  errors: any[];
  blocked_actions: any[];
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface DashboardStats {
  jobs_discovered: number;
  jobs_matching: number;
  applications_prepared: number;
  applications_approved: number;
  applications_submitted: number;
  interview_count: number;
  response_rate: number;
  top_companies: { name: string; count: number }[];
  top_categories: { name: string; count: number }[];
  average_fit_score: number;
}

class ApiClient {
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API Error ${res.status}: ${err}`);
    }
    return res.json();
  }

  // Profile
  getProfile = () => this.request<User>('/profile');
  updateProfile = (data: Partial<User>) =>
    this.request<User>('/profile', { method: 'PUT', body: JSON.stringify(data) });

  addEducation = (data: Partial<Education>) =>
    this.request('/profile/education', { method: 'POST', body: JSON.stringify(data) });
  addSkill = (data: Partial<Skill>) =>
    this.request('/profile/skills', { method: 'POST', body: JSON.stringify(data) });
  addProject = (data: Partial<Project>) =>
    this.request('/profile/projects', { method: 'POST', body: JSON.stringify(data) });
  addExperience = (data: Partial<Experience>) =>
    this.request('/profile/experience', { method: 'POST', body: JSON.stringify(data) });

  deleteSkill = (id: number) => this.request(`/profile/skills/${id}`, { method: 'DELETE' });
  deleteEducation = (id: number) => this.request(`/profile/education/${id}`, { method: 'DELETE' });
  deleteProject = (id: number) => this.request(`/profile/projects/${id}`, { method: 'DELETE' });
  deleteExperience = (id: number) => this.request(`/profile/experience/${id}`, { method: 'DELETE' });

  // Resume
  uploadResume = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/resumes/upload`, { method: 'POST', body: formData });
    return res.json();
  };
  getResumes = () => this.request<any[]>('/resumes');

  // Search Preferences
  getSearchPreferences = () => this.request<any>('/search-preferences');
  updateSearchPreferences = (data: any) =>
    this.request('/search-preferences', { method: 'PUT', body: JSON.stringify(data) });

  // Jobs
  getJobs = (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return this.request<{ jobs: any[]; total: number; page: number; pages: number }>(`/jobs?${qs}`);
  };
  getJob = (id: number) => this.request<{ job: Job; match: JobMatch | null }>(`/jobs/${id}`);
  getTopMatches = (limit = 20) => this.request<any[]>(`/jobs/top-matches?limit=${limit}`);

  // Discovery
  runDiscovery = (keywords?: string[]) => {
    const qs = keywords ? `?${new URLSearchParams({ keywords: keywords.join(',') }).toString()}` : '';
    return this.request<any>(`/discovery/run${qs}`, { method: 'POST' });
  };
  orchestrateDiscovery = () => this.request<any>('/discovery/orchestrate', { method: 'POST' });

  // Applications
  getApplications = (status?: string) => {
    const qs = status ? `?status=${status}` : '';
    return this.request<Application[]>(`/applications${qs}`);
  };
  getApplication = (id: number) => this.request<Application>(`/applications/${id}`);
  createApplication = (jobId: number, mode = 'prepare') =>
    this.request<Application>(`/applications?job_id=${jobId}&mode=${mode}`, { method: 'POST' });
  approveApplication = (id: number) =>
    this.request<Application>(`/applications/${id}/approve`, { method: 'POST' });
  skipApplication = (id: number) =>
    this.request(`/applications/${id}/skip`, { method: 'POST' });
  updateApplication = (id: number, data: any) =>
    this.request(`/applications/${id}`, { method: 'PUT', body: JSON.stringify(data) });

  // Dashboard
  getDashboardStats = () => this.request<DashboardStats>('/dashboard/stats');
  getDashboardOverview = () => this.request<any>('/dashboard/overview');

  // Agent Activity
  getAgentRuns = (limit = 50) => this.request<AgentRun[]>(`/agents/runs?limit=${limit}`);
  getEvents = (limit = 50) => this.request<any[]>(`/events?limit=${limit}`);

  // Notifications
  getNotifications = () => this.request<any[]>('/notifications');

  // Sources
  getSources = () => this.request<any[]>('/sources');

  // Setup
  seedProfile = () => this.request('/seed-profile', { method: 'POST' });
  seedPreferences = () => this.request('/seed-default-preferences', { method: 'POST' });
}

export const api = new ApiClient();
