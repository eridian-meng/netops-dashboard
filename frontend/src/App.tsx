import { useEffect, useMemo, useState } from "react";
import {
  artifactUrl,
  createJob,
  getAuthProviders,
  getCatalog,
  getJob,
  getSession,
  startAwsLogin
} from "./api";
import type { AuthProviderStatus, CatalogItem, JobRecord, ProviderName, SessionInfo } from "./types";

const RUNNING_STATUSES = new Set(["queued", "running"]);

function App() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [catalogError, setCatalogError] = useState("");
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [authProviders, setAuthProviders] = useState<AuthProviderStatus[]>([]);
  const [authMessage, setAuthMessage] = useState("");
  const [latestJob, setLatestJob] = useState<JobRecord | null>(null);
  const [jobError, setJobError] = useState("");
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    getCatalog().then(setItems).catch((error: Error) => setCatalogError(error.message));
    getSession().then(setSession).catch(() => setSession(null));
  }, []);

  useEffect(() => {
    getAuthProviders().then(setAuthProviders).catch(() => setAuthProviders([]));
  }, [session]);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!latestJob || !RUNNING_STATUSES.has(latestJob.status)) {
      return;
    }
    const interval = window.setInterval(() => {
      getJob(latestJob.id).then(setLatestJob).catch((error: Error) => setJobError(error.message));
    }, 2000);
    return () => window.clearInterval(interval);
  }, [latestJob]);

  const route = useMemo(() => findRoute(items, path), [items, path]);
  const currentItem = route.length ? route[route.length - 1] : undefined;
  const viewItems: CatalogItem[] = currentItem?.children?.length ? currentItem.children : path === "/" ? items : [];
  const serviceItem = currentItem && !currentItem.children?.length ? currentItem : null;
  const statusByProvider = useMemo(() => {
    return new Map(authProviders.map((status) => [status.provider, status]));
  }, [authProviders]);

  function navigate(nextPath: string) {
    window.history.pushState({}, "", nextPath);
    setPath(nextPath);
    setLatestJob(null);
    setJobError("");
    setAuthMessage("");
  }

  async function refreshAuth() {
    const providers = await getAuthProviders();
    setAuthProviders(providers);
  }

  async function handleStartAuth(provider: ProviderName) {
    setAuthMessage("");
    if (provider !== "aws") {
      setAuthMessage(`${provider.toUpperCase()} authentication is reserved for a future provider adapter.`);
      return;
    }
    const response = await startAwsLogin();
    setAuthMessage(response.message);
    await refreshAuth();
  }

  async function handleRun(item: CatalogItem) {
    setJobError("");
    setLatestJob(null);
    try {
      const job = await createJob(item.id);
      setLatestJob(job);
    } catch (error) {
      setJobError(error instanceof Error ? error.message : "Failed to start job.");
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate("/")}>
          <span className="brand-mark">N</span>
          <span>
            <strong>NetOps Dashboard</strong>
            <small>Private automation portal</small>
          </span>
        </button>
        <div className="operator">
          <span>Session</span>
          <strong>{session?.operatorLabel ?? "Initializing"}</strong>
          <small>{session?.source ?? "server-bound"}</small>
        </div>
      </header>

      <main className="content">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <button onClick={() => navigate("/")}>Home</button>
          {route.map((item) => (
            <button key={item.id} onClick={() => navigate(item.path)}>
              {item.name}
            </button>
          ))}
        </nav>

        {catalogError ? <div className="notice error">{catalogError}</div> : null}

        {viewItems.length ? (
          <>
            <section className="section-heading">
              <h1>{currentItem?.name ?? "Services"}</h1>
              <p>{currentItem?.description ?? "Select a service or folder to open its automation workspace."}</p>
            </section>
            <section className="grid" aria-label="Service catalog">
              {viewItems.map((item) => (
                <ServiceTile
                  key={item.id}
                  item={item}
                  status={statusByProvider.get(item.provider)}
                  onOpen={() => navigate(item.path)}
                />
              ))}
            </section>
          </>
        ) : null}

        {serviceItem ? (
          <ServiceDetail
            item={serviceItem}
            authStatus={statusByProvider.get(serviceItem.provider)}
            authMessage={authMessage}
            latestJob={latestJob}
            jobError={jobError}
            onStartAuth={() => handleStartAuth(serviceItem.provider)}
            onRefreshAuth={refreshAuth}
            onRun={() => handleRun(serviceItem)}
          />
        ) : null}
      </main>
    </div>
  );
}

function ServiceTile({
  item,
  status,
  onOpen
}: {
  item: CatalogItem;
  status?: AuthProviderStatus;
  onOpen: () => void;
}) {
  const runnable = Boolean(item.scriptPath || item.scriptGroupPath);
  const authText = item.provider === "generic" ? "No cloud auth" : status?.authenticated ? "Authenticated" : "Auth required";
  return (
    <button className="tile" onClick={onOpen}>
      <img src={item.icon} alt="" />
      <span className="tile-body">
        <strong>{item.name}</strong>
        <small>{item.description}</small>
      </span>
      <span className="tile-footer">
        <span className={`pill provider-${item.provider}`}>{item.provider.toUpperCase()}</span>
        <span className={runnable ? "pill runnable" : "pill reserved"}>{runnable ? "Runnable" : authText}</span>
      </span>
    </button>
  );
}

function ServiceDetail({
  item,
  authStatus,
  authMessage,
  latestJob,
  jobError,
  onStartAuth,
  onRefreshAuth,
  onRun
}: {
  item: CatalogItem;
  authStatus?: AuthProviderStatus;
  authMessage: string;
  latestJob: JobRecord | null;
  jobError: string;
  onStartAuth: () => void;
  onRefreshAuth: () => void;
  onRun: () => void;
}) {
  const runnable = Boolean(item.scriptPath || item.scriptGroupPath);
  const authRequired = item.provider !== "generic" && item.auth?.required;
  const authenticated = !authRequired || Boolean(authStatus?.authenticated);
  const isRunning = latestJob ? RUNNING_STATUSES.has(latestJob.status) : false;

  return (
    <section className="detail">
      <div className="detail-header">
        <img src={item.icon} alt="" />
        <div>
          <h1>{item.name}</h1>
          <p>{item.description}</p>
        </div>
      </div>

      <div className="status-row">
        <StatusCard title="Provider" value={item.provider.toUpperCase()} detail={authStatus?.profile ?? "Catalog managed"} />
        <StatusCard
          title="Authentication"
          value={authenticated ? "Ready" : "Required"}
          detail={authStatus?.message ?? "No provider adapter required."}
        />
        <StatusCard title="Execution" value={runnable ? "Registered" : "Reserved"} detail={item.scriptPath ?? item.scriptGroupPath ?? "No script mapped yet."} />
      </div>

      <div className="actions">
        {authRequired ? (
          <>
            <button className="secondary" onClick={onStartAuth}>
              Authenticate
            </button>
            <button className="secondary" onClick={onRefreshAuth}>
              Refresh status
            </button>
          </>
        ) : null}
        <button className="primary" onClick={onRun} disabled={!runnable || !authenticated || isRunning}>
          {isRunning ? "Running" : "Run"}
        </button>
      </div>

      {authMessage ? <div className="notice">{authMessage}</div> : null}
      {authStatus?.loginLog ? (
        <pre className="log" aria-label="Cloud login log">
          {authStatus.loginLog}
        </pre>
      ) : null}
      {jobError ? <div className="notice error">{jobError}</div> : null}
      {latestJob ? <JobPanel job={latestJob} /> : null}
    </section>
  );
}

function StatusCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="status-card">
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function JobPanel({ job }: { job: JobRecord }) {
  return (
    <section className="job-panel">
      <div className="job-heading">
        <div>
          <span className={`job-status status-${job.status}`}>{job.status}</span>
          <strong>{job.catalogItemName}</strong>
        </div>
        <small>{job.id}</small>
      </div>
      {job.message ? <p>{job.message}</p> : null}
      {job.stdout ? <pre className="log">{job.stdout}</pre> : null}
      {job.stderr ? <pre className="log error-log">{job.stderr}</pre> : null}
      {job.artifacts.length ? (
        <div className="artifacts">
          {job.artifacts.map((artifact) => (
            <a key={artifact.id} href={artifactUrl(job.id, artifact.id)} download>
              {artifact.name}
              <span>{formatBytes(artifact.size)}</span>
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function findRoute(items: CatalogItem[], currentPath: string): CatalogItem[] {
  for (const item of items) {
    if (item.path === currentPath) {
      return [item];
    }
    const childRoute = findRoute(item.children ?? [], currentPath);
    if (childRoute.length) {
      return [item, ...childRoute];
    }
  }
  return [];
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default App;
