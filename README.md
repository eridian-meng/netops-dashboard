# NetOps Automation Dashboard

Internal Heimdall-style dashboard for launching catalog-registered NetOps Python automation from a private EC2 Linux instance.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI
- Runtime: Nginx serves the frontend and proxies `/api` to FastAPI
- Process: systemd
- Auth boundary v1: private VPN/private EC2 IP
- Cloud auth v1: per-operator AWS SSO workspace

## Features

- Catalog-driven dashboard tiles with custom names and icons.
- Nested folders such as `Architecture Diagram > AWS Architecture Diagram`.
- Backend-controlled script execution so users cannot run arbitrary filesystem paths.
- Async job tracking with status, stdout, stderr, exit code, and downloadable artifacts.
- Per-browser-session AWS SSO isolation for the VPN-only first release.
- Future-ready identity resolver for Okta, Keycloak, or oauth2-proxy trusted headers.

## Local Development

Backend:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

Frontend:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

## Catalog-Driven Services

Services are defined in `catalog/services.json`. Add folders or runnable services there and place scripts under `services/`.

Runnable scripts must be registered by catalog `scriptPath` or `scriptGroupPath`; the backend rejects arbitrary paths.

## AWS SSO

AWS SSO uses an isolated workspace under `NETOPS_AUTH_ROOT` for each app identity. In the VPN-only v1, identity is a server-issued HTTP-only browser session cookie. When Okta, Keycloak, or oauth2-proxy is added, the backend will automatically prefer trusted user headers such as `X-Auth-Request-Email` or `X-Forwarded-User`.

This means one user's `aws sso login` never shares credentials with another user's browser session or SSO-authenticated app identity.

Set these backend environment variables on EC2:

```bash
NETOPS_AWS_PROFILE=netops
NETOPS_AWS_CONFIG_TEMPLATE=/opt/netops-dashboard/config/aws-config
```

The template file should contain the SSO profile configuration shared by operators. The backend copies it into each operator workspace before running `aws sso login --no-browser --profile <profile>`.

## Deployment

See:

- `deploy/netops-dashboard-backend.service`
- `deploy/nginx-netops-dashboard.conf`
- `deploy/install-ec2.sh`
- `deploy/ubuntu-from-scratch.md`
