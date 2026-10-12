const BASE = "";
const TOKEN_KEY = "cv_parser_token";

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export interface WorkerSummary {
  id: number;
  name: string;
  email: string;
  location: string;
  education_level: string;
  education_field: string;
  years_of_experience: number | null;
  domain_expertise_rating: number | null;
  overall_score: number | null;
  status: string;
  skill_count: number;
  domain_score: number | null;
  subdomain_score: number | null;
  processed_at: string | null;
  created_at: string | null;
}

export interface WorkerDetail extends WorkerSummary {
  summary: string;
  reasoning: string;
  cv_url: string;
  skills: SkillOut[];
}

export interface SkillOut {
  id: number;
  category: string;
  skill_name: string;
  proficiency: string;
  context: string;
}

export interface WorkerListResponse {
  items: WorkerSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SkillCategory {
  category: string;
  skills: string[];
}

export interface StatsResponse {
  total_workers: number;
  completed_workers: number;
  pending_workers: number;
  avg_overall_score: number | null;
  avg_domain_expertise: number | null;
  score_distribution: { range: string; count: number }[];
  experience_brackets: { bracket: string; count: number }[];
  education_breakdown: { level: string; count: number }[];
  top_skills: { skill: string; count: number }[];
  category_coverage: { category: string; workers: number }[];
}

export interface SkillCondition {
  skill_name: string;
  min_proficiency: string;
  category?: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  total: number;
  completed: number;
  failed: number;
  message: string;
}

export interface IngestResponse {
  job_id: string;
  message: string;
  workers_queued: number;
}

export interface WorkerSkillsGrouped {
  worker_id: number;
  skills_by_category: Record<string, { skill_name: string; proficiency: string; context: string }[]>;
}

// Workers
export function fetchWorkers(params: Record<string, string | number>): Promise<WorkerListResponse> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== "" && v !== undefined && v !== null) qs.set(k, String(v));
  }
  return request(`/api/workers?${qs}`);
}

export function fetchWorker(id: number): Promise<WorkerDetail> {
  return request(`/api/workers/${id}`);
}

export function fetchWorkerSkills(id: number): Promise<WorkerSkillsGrouped> {
  return request(`/api/workers/${id}/skills`);
}

// Skills
export function fetchSkillCategories(): Promise<SkillCategory[]> {
  return request("/api/skills");
}

export function fetchSkillNames(): Promise<string[]> {
  return request("/api/skills/names");
}

export function queryBySkills(body: {
  conditions: SkillCondition[];
  match_all: boolean;
  page: number;
  page_size: number;
}): Promise<WorkerListResponse> {
  return request("/api/skills/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// Stats
export function fetchStats(): Promise<StatsResponse> {
  return request("/api/stats");
}

// Export
export function getExportCsvUrl(workerIds?: number[]): string {
  const ids = workerIds?.join(",") ?? "";
  return `/api/export/csv?worker_ids=${ids}`;
}

export function getExportJsonUrl(workerIds?: number[]): string {
  const ids = workerIds?.join(",") ?? "";
  return `/api/export/json?worker_ids=${ids}`;
}

export function exportToSheets(sheetUrl?: string, workerIds?: number[]): Promise<{ message: string }> {
  const qs = new URLSearchParams();
  if (sheetUrl) qs.set("sheet_url", sheetUrl);
  if (workerIds?.length) qs.set("worker_ids", workerIds.join(","));
  return request(`/api/export/sheets?${qs}`, { method: "POST" });
}

// Ingest
export function triggerIngest(): Promise<IngestResponse> {
  return request("/api/ingest", { method: "POST" });
}

export function triggerRefresh(): Promise<IngestResponse> {
  return request("/api/refresh", { method: "POST" });
}

export function fetchJobs(): Promise<JobStatus[]> {
  return request("/api/jobs");
}

export function fetchJob(jobId: string): Promise<JobStatus> {
  return request(`/api/jobs/${jobId}`);
}

// ── Data Sources ────────────────────────────────────────────────────────────

export interface DataSource {
  id: number;
  name: string;
  sheet_url: string;
  sheet_id: string;
  gid: string;
  tab_name: string;
  created_by: string;
  last_synced_at: string | null;
  worker_count: number;
  created_at: string | null;
}

export interface SheetTab {
  gid: string;
  title: string;
  row_count: number;
}

export function fetchSources(): Promise<DataSource[]> {
  return request("/api/sources");
}

export function createSource(body: {
  name: string;
  sheet_url: string;
  gid?: string;
  tab_name?: string;
}): Promise<DataSource> {
  return request("/api/sources", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function deleteSource(id: number): Promise<void> {
  return request(`/api/sources/${id}`, { method: "DELETE" });
}

export function fetchSourceTabs(id: number): Promise<SheetTab[]> {
  return request(`/api/sources/${id}/tabs`);
}

export function fetchTabsFromUrl(sheetUrl: string): Promise<SheetTab[]> {
  const qs = new URLSearchParams({ sheet_url: sheetUrl });
  return request(`/api/sources/from-url/tabs?${qs}`);
}

export function updateSourceTab(id: number, gid: string, tabName: string): Promise<DataSource> {
  const qs = new URLSearchParams({ gid, tab_name: tabName });
  return request(`/api/sources/${id}?${qs}`, { method: "PATCH" });
}

export function ingestFromSource(id: number): Promise<IngestResponse> {
  return request(`/api/sources/${id}/ingest`, { method: "POST" });
}

// ── Saved Views ─────────────────────────────────────────────────────────────

export interface SavedView {
  id: number;
  name: string;
  description: string;
  view_type: string;
  filters: string;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
}

export function fetchViews(viewType?: string): Promise<SavedView[]> {
  const qs = viewType ? `?view_type=${viewType}` : "";
  return request(`/api/views${qs}`);
}

export function createView(body: {
  name: string;
  description?: string;
  view_type: string;
  filters: string;
}): Promise<SavedView> {
  return request("/api/views", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function deleteView(id: number): Promise<void> {
  return request(`/api/views/${id}`, { method: "DELETE" });
}

// ── Domain Scoring ──────────────────────────────────────────────────────────

export interface DomainScore {
  domain: string;
  score: number;
}

export function fetchDomains(): Promise<string[]> {
  return request("/api/domains");
}

export function fetchWorkerDomainScores(id: number): Promise<DomainScore[]> {
  return request(`/api/workers/${id}/domain-scores`);
}

// ── Subdomain Scoring ────────────────────────────────────────────────────────

export interface SubdomainScore {
  subdomain: string;
  tier: string;
  score: number;
}

export function fetchSubdomains(): Promise<{ subdomain: string; tier: string }[]> {
  return request("/api/subdomains");
}

export function fetchWorkerSubdomainScores(id: number): Promise<SubdomainScore[]> {
  return request(`/api/workers/${id}/subdomain-scores`);
}
