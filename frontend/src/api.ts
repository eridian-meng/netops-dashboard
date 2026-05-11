import type { AuthProviderStatus, AuthStartResponse, CatalogItem, JobRecord, SessionInfo } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    }
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function getSession(): Promise<SessionInfo> {
  return request<SessionInfo>("/api/session");
}

export async function getCatalog(): Promise<CatalogItem[]> {
  const response = await request<{ items: CatalogItem[] }>("/api/catalog");
  return response.items;
}

export async function getAuthProviders(): Promise<AuthProviderStatus[]> {
  const response = await request<{ providers: AuthProviderStatus[] }>("/api/auth/providers");
  return response.providers;
}

export async function startAwsLogin(): Promise<AuthStartResponse> {
  return request<AuthStartResponse>("/api/auth/aws/start", {
    method: "POST"
  });
}

export async function getAwsStatus(): Promise<AuthProviderStatus> {
  return request<AuthProviderStatus>("/api/auth/aws/status");
}

export async function createJob(catalogItemId: string): Promise<JobRecord> {
  return request<JobRecord>("/api/jobs", {
    method: "POST",
    body: JSON.stringify({ catalogItemId })
  });
}

export async function getJob(jobId: string): Promise<JobRecord> {
  return request<JobRecord>(`/api/jobs/${jobId}`);
}

export function artifactUrl(jobId: string, artifactId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/artifacts/${artifactId}`;
}
