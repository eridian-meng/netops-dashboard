export type ProviderName = "aws" | "azure" | "gcp" | "generic";
export type CatalogItemType = "folder" | "service" | "script";
export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface CatalogItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  type: CatalogItemType;
  provider: ProviderName;
  path: string;
  scriptPath?: string;
  scriptGroupPath?: string;
  auth?: {
    required?: boolean;
    provider?: ProviderName;
  };
  children?: CatalogItem[];
}

export interface AuthProviderStatus {
  provider: ProviderName;
  available: boolean;
  authenticated: boolean;
  operator: string;
  profile?: string;
  identity?: Record<string, unknown>;
  message: string;
  loginLog: string;
}

export interface AuthStartResponse {
  provider: ProviderName;
  operator: string;
  started: boolean;
  message: string;
  logPath?: string;
}

export interface SessionInfo {
  operatorKey: string;
  operatorLabel: string;
  source: string;
}

export interface JobArtifact {
  id: string;
  name: string;
  size: number;
}

export interface JobRecord {
  id: string;
  catalogItemId: string;
  catalogItemName: string;
  provider: ProviderName;
  operator: string;
  status: JobStatus;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  exitCode?: number;
  stdout: string;
  stderr: string;
  artifacts: JobArtifact[];
  message: string;
}
