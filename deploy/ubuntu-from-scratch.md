# Ubuntu EC2 Install From Scratch

These commands assume Ubuntu 22.04 or 24.04 on a private EC2 instance reachable only through VPN.

## Prerequisites

- Private EC2 instance with inbound HTTP allowed only from VPN/internal CIDRs.
- Ubuntu user with sudo access.
- Python 3.10+.
- Node.js 20+.
- Nginx.
- AWS CLI v2.
- A real AWS IAM Identity Center profile config for the shared profile name `netops`.

## Install OS Packages

```bash
sudo apt-get update
sudo apt-get install -y curl unzip git nginx python3 python3-venv python3-pip rsync
```

## Install Node.js 22 LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
```

## Install AWS CLI v2

```bash
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip -q awscliv2.zip
sudo ./aws/install
aws --version
```

For ARM-based EC2 instances, use the `awscli-exe-linux-aarch64.zip` download instead.

## Install App

```bash
cd /tmp
git clone <your-repo-url> netops-dashboard-src
cd netops-dashboard-src

sudo useradd --system --create-home --shell /usr/sbin/nologin netops || true
sudo mkdir -p /opt/netops-dashboard/{app,backend,catalog,services,jobs,auth,config}
sudo mkdir -p /etc/netops-dashboard
sudo chown -R netops:netops /opt/netops-dashboard

npm install
npm run build
sudo rsync -av --delete dist/ /opt/netops-dashboard/app/

sudo rsync -av --delete backend/ /opt/netops-dashboard/backend/
sudo rsync -av --delete catalog/ /opt/netops-dashboard/catalog/
sudo rsync -av --delete services/ /opt/netops-dashboard/services/

sudo python3 -m venv /opt/netops-dashboard/.venv
sudo /opt/netops-dashboard/.venv/bin/python -m pip install --upgrade pip
sudo /opt/netops-dashboard/.venv/bin/python -m pip install -r /opt/netops-dashboard/backend/requirements.txt
sudo chown -R netops:netops /opt/netops-dashboard
```

## Configure AWS SSO Template

```bash
sudo cp deploy/aws-config.example /opt/netops-dashboard/config/aws-config
sudo nano /opt/netops-dashboard/config/aws-config
sudo chown netops:netops /opt/netops-dashboard/config/aws-config
sudo chmod 0640 /opt/netops-dashboard/config/aws-config
```

Edit `sso_start_url`, `sso_region`, `sso_account_id`, `sso_role_name`, and `region`.

Each app session or future Okta/Keycloak user gets a separate workspace under:

```text
/opt/netops-dashboard/auth/aws/<operator-key>
```

## Configure Environment and Services

```bash
sudo cp deploy/backend.env.example /etc/netops-dashboard/backend.env
sudo nano /etc/netops-dashboard/backend.env
sudo chmod 0640 /etc/netops-dashboard/backend.env

sudo cp deploy/netops-dashboard-backend.service /etc/systemd/system/netops-dashboard-backend.service
sudo cp deploy/nginx-netops-dashboard.conf /etc/nginx/sites-available/netops-dashboard
sudo ln -sf /etc/nginx/sites-available/netops-dashboard /etc/nginx/sites-enabled/netops-dashboard
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now netops-dashboard-backend
sudo systemctl restart nginx
```

Set `NETOPS_FRONTEND_ORIGIN` to the private URL users will open, for example `http://10.10.20.50`.

## Smoke Test

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1/api/catalog
curl http://<ec2-private-ip>/api/health
```

Open `http://<ec2-private-ip>/` over VPN.

## Operations

```bash
sudo journalctl -u netops-dashboard-backend -f
sudo systemctl restart netops-dashboard-backend
sudo nginx -t
sudo systemctl restart nginx
```

## Future Okta or Keycloak Integration

Put an OIDC-aware reverse proxy in front of the app, such as oauth2-proxy, and configure it to pass a trusted user header to FastAPI:

```text
X-Auth-Request-Email: user@example.com
```

The backend already prefers that header over the browser session cookie, so AWS SSO workspaces become bound to the real authenticated app user.
