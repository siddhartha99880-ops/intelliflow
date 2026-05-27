const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type WorkflowCreateRequest = {
  name: string;
  description?: string | null;
  nodes: Array<{
    id: string;
    type:
      | "trigger"
      | "llm_agent"
      | "decision"
      | "api_action"
      | "slack"
      | "notion"
      | "email"
      | "delay"
      | "human_approval";
    label: string;
    position_x?: number;
    position_y?: number;
    data?: Record<string, any>;
  }>;
  edges: Array<{
    id?: string | null;
    from_node_id: string;
    to_node_id: string;
    condition_key?: string | null;
  }>;
};

export type ExecuteWorkflowRequest = {
  input_payload: Record<string, any>;
};

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token: string | null = null,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function login(email: string, password: string) {
  return apiFetch<AuthTokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function signup(input: {
  email: string;
  password: string;
  full_name?: string | null;
  team_name: string;
}) {
  return apiFetch<AuthTokenResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getWorkflows(token: string) {
  return apiFetch<any[]>("/api/workflows", { method: "GET" }, token);
}

export async function createWorkflow(token: string, req: WorkflowCreateRequest) {
  return apiFetch<any>("/api/workflows", { method: "POST", body: JSON.stringify(req) }, token);
}

export async function executeWorkflow(token: string, workflowId: string, req: ExecuteWorkflowRequest) {
  return apiFetch<any>(`/api/workflows/${workflowId}/execute`, { method: "POST", body: JSON.stringify(req) }, token);
}

export async function getExecution(token: string, executionId: string) {
  return apiFetch<any>(`/api/executions/${executionId}`, { method: "GET" }, token);
}

export async function listExecutions(token: string, limit = 20) {
  const url = `/api/executions?limit=${encodeURIComponent(String(limit))}`;
  return apiFetch<any[]>(url, { method: "GET" }, token);
}

