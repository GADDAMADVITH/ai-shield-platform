/** Shared API types matching the FastAPI backend. */

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type BackendUser = {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "member" | "viewer" | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  user: BackendUser;
  tokens: TokenPair;
};

export type PageMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ProjectEnvironment = "development" | "staging" | "production";
export type ProjectStatus = "connected" | "disconnected" | "error" | "archived";

export type BackendProject = {
  id: string;
  owner_id: string;
  name: string;
  environment: ProjectEnvironment;
  application_type: string;
  connection_method: string;
  status: ProjectStatus;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = {
  items: BackendProject[];
  meta: PageMeta;
};

export type ConnectionMethodApi =
  | "rest_api"
  | "openapi"
  | "localhost"
  | "playwright"
  | "sdk"
  | "webhook";

export type ConnectionStatusApi = "unverified" | "healthy" | "unhealthy" | "error";

export type BackendConnection = {
  id: string;
  project_id: string;
  name: string;
  connection_method: ConnectionMethodApi;
  base_url: string | null;
  health_endpoint: string | null;
  api_key_set: boolean;
  headers: Record<string, unknown>;
  timeout_seconds: number;
  verify_ssl: boolean;
  playwright_entry_url: string | null;
  notes: string | null;
  status: ConnectionStatusApi;
  last_verified_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ConnectionListResponse = {
  items: BackendConnection[];
  meta: PageMeta;
};

export type ConnectionTestResponse = {
  reachable: boolean;
  status_code: number | null;
  response_time_ms: number;
  message: string;
  timestamp: string;
  connection: BackendConnection;
};

export type SeverityApi = "critical" | "high" | "medium" | "low" | "info";
export type ScanStatusApi =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type DashboardOverview = {
  total_projects: number;
  total_scans: number;
  successful_scans: number;
  failed_scans: number;
  average_risk_score: number;
  average_security_score: number;
  critical_findings: number;
  high_findings: number;
  medium_findings: number;
  low_findings: number;
  total_findings: number;
  overall_security_posture: string;
  overall_severity: SeverityApi;
  latest_activity: Array<{
    type: string;
    scan_id: string;
    project_id: string;
    project_name: string | null;
    status: string;
    total_findings: number;
    overall_risk_score: number;
    overall_security_score: number;
    created_at: string;
  }>;
};

export type DashboardRecentScan = {
  id: string;
  project_id: string;
  project_name: string | null;
  status: ScanStatusApi;
  profile: string;
  overall_security_score: number | null;
  overall_risk_score: number | null;
  total_findings: number;
  critical: number;
  high: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type SeverityDistribution = {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
};

export type DashboardStatistics = {
  overview: DashboardOverview;
  risk: {
    overall_risk_score: number;
    average_risk_score: number;
    average_security_score: number;
    highest_risk_scan: Record<string, unknown> | null;
    risk_trend: Array<{ date: string; average_risk_score: number }>;
    assessment_distribution: Record<string, number>;
    severity_distribution: SeverityDistribution;
    scan_status_distribution: Record<string, number>;
  };
  severity_distribution: SeverityDistribution;
  assessment_results: Array<Record<string, unknown>>;
  latest_findings: Array<{
    id: string;
    title: string;
    severity: SeverityApi;
    category?: string | null;
    assessment_key?: string | null;
    assessment_name?: string | null;
    description?: string;
  }>;
};

export type BackendReport = {
  id: string;
  project_id: string;
  scan_id: string;
  title: string;
  status: "pending" | "generating" | "ready" | "failed";
  summary: string | null;
  created_at: string;
  updated_at: string;
  project_name: string | null;
  overall_security_score: number | null;
  overall_risk_score: number | null;
  total_findings: number | null;
  overall_severity: SeverityApi | null;
  executive_summary?: Record<string, unknown>;
  risk_summary?: Record<string, unknown>;
  findings_count?: number;
};

export type ReportListResponse = {
  items: BackendReport[];
  meta: PageMeta;
};

export type ScanHistoryItem = {
  id: string;
  project_id: string;
  project_name: string | null;
  environment: string | null;
  status: ScanStatusApi;
  profile: string;
  overall_security_score: number | null;
  overall_risk_score: number | null;
  total_findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  execution_time_ms: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type ScanHistoryResponse = {
  items: ScanHistoryItem[];
  meta: PageMeta;
};

export type BackendNotification = {
  id: string;
  user_id: string;
  project_id: string | null;
  title: string;
  description: string;
  category: "security" | "system" | "reports" | "projects";
  severity: SeverityApi;
  level: "info" | "warning" | "critical";
  is_read: boolean;
  created_at: string;
  updated_at: string;
};

export type NotificationListResponse = {
  items: BackendNotification[];
  meta: PageMeta;
};

export type FindingsExplorerResponse = {
  total: number;
  items: Array<Record<string, unknown>>;
  by_severity: Record<string, Array<Record<string, unknown>>>;
  by_category: Record<string, Array<Record<string, unknown>>>;
  by_assessment: Record<string, Array<Record<string, unknown>>>;
};
