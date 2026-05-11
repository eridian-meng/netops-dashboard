import json
import os
import shutil
import subprocess
from pathlib import Path

from ..config import Settings
from ..models import AuthProviderStatus, AuthStartResponse, ProviderName
from .base import ProviderAdapter


class AwsProvider(ProviderAdapter):
    name = ProviderName.aws

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def status(self, operator: str) -> AuthProviderStatus:
        if not shutil.which("aws"):
            return AuthProviderStatus(
                provider=self.name,
                available=False,
                authenticated=False,
                operator=operator,
                profile=self.settings.aws_profile,
                message="AWS CLI v2 is not installed or not on PATH.",
                loginLog=self._login_log(operator),
            )

        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--profile", self.settings.aws_profile, "--output", "json"],
            env={**os.environ, **self.job_environment(operator)},
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout or "{}")
            return AuthProviderStatus(
                provider=self.name,
                available=True,
                authenticated=True,
                operator=operator,
                profile=self.settings.aws_profile,
                identity=identity,
                message="AWS SSO session is authenticated.",
                loginLog=self._login_log(operator),
            )
        return AuthProviderStatus(
            provider=self.name,
            available=True,
            authenticated=False,
            operator=operator,
            profile=self.settings.aws_profile,
            message=(result.stderr or result.stdout or "AWS SSO session is not authenticated.").strip(),
            loginLog=self._login_log(operator),
        )

    def start_login(self, operator: str) -> AuthStartResponse:
        if not shutil.which("aws"):
            return AuthStartResponse(
                provider=self.name,
                operator=operator,
                started=False,
                message="AWS CLI v2 is not installed or not on PATH.",
            )

        workspace = self._workspace(operator)
        workspace.mkdir(parents=True, exist_ok=True)
        self._ensure_config(workspace)
        log_path = workspace / "sso-login.log"
        with log_path.open("w") as log_file:
            subprocess.Popen(
                ["aws", "sso", "login", "--no-browser", "--profile", self.settings.aws_profile],
                env={**os.environ, **self.job_environment(operator)},
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=workspace,
                text=True,
            )
        return AuthStartResponse(
            provider=self.name,
            operator=operator,
            started=True,
            message="AWS SSO login started. Poll status and follow the URL/code shown in the login log.",
            logPath=str(log_path),
        )

    def job_environment(self, operator: str) -> dict[str, str]:
        workspace = self._workspace(operator)
        return {
            "AWS_CONFIG_FILE": str(workspace / "config"),
            "AWS_SHARED_CREDENTIALS_FILE": str(workspace / "credentials"),
            "AWS_PROFILE": self.settings.aws_profile,
        }

    def _workspace(self, operator: str) -> Path:
        return self.settings.auth_root / "aws" / operator

    def _ensure_config(self, workspace: Path) -> None:
        config_path = workspace / "config"
        if config_path.exists():
            return
        template = self.settings.aws_config_template
        if template and Path(template).exists():
            shutil.copyfile(template, config_path)
            return
        config_path.write_text(
            "[profile netops]\n"
            "# Replace this file or set NETOPS_AWS_CONFIG_TEMPLATE with your AWS SSO profile.\n"
            "sso_session = netops\n"
            "sso_account_id = 000000000000\n"
            "sso_role_name = ReadOnlyAccess\n"
            "region = us-east-1\n"
            "output = json\n"
            "\n"
            "[sso-session netops]\n"
            "sso_start_url = https://example.awsapps.com/start\n"
            "sso_region = us-east-1\n"
            "sso_registration_scopes = sso:account:access\n"
        )

    def _login_log(self, operator: str) -> str:
        log_path = self._workspace(operator) / "sso-login.log"
        if not log_path.exists():
            return ""
        return log_path.read_text(errors="replace")[-4000:]
