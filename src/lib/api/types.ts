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
