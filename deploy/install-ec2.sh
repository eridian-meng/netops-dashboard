#!/usr/bin/env bash
set -euo pipefail

APP_ROOT=${APP_ROOT:-/opt/netops-dashboard}
APP_USER=${APP_USER:-netops}

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /sbin/nologin "$APP_USER"
fi

mkdir -p "$APP_ROOT"/{app,backend,catalog,services,jobs,auth,config}
chown -R "$APP_USER:$APP_USER" "$APP_ROOT"

cp deploy/netops-dashboard-backend.service /etc/systemd/system/netops-dashboard-backend.service
cp deploy/nginx-netops-dashboard.conf /etc/nginx/conf.d/netops-dashboard.conf

if [ ! -f /etc/netops-dashboard/backend.env ]; then
  mkdir -p /etc/netops-dashboard
  cp deploy/backend.env.example /etc/netops-dashboard/backend.env
fi

systemctl daemon-reload
systemctl enable netops-dashboard-backend

echo "Build frontend with npm run build, copy dist/* to $APP_ROOT/app, copy backend/catalog/services, then restart:"
echo "  systemctl restart netops-dashboard-backend nginx"
