from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        default_runtime_root = repo_root / ".netops"

        self.root_dir = Path(os.getenv("NETOPS_ROOT", repo_root)).resolve()
        self.catalog_path = Path(
            os.getenv("NETOPS_CATALOG_PATH", self.root_dir / "catalog" / "services.json")
        ).resolve()
        self.services_root = Path(
            os.getenv("NETOPS_SERVICES_ROOT", self.root_dir / "services")
        ).resolve()
        self.jobs_root = Path(
            os.getenv("NETOPS_JOBS_ROOT", default_runtime_root / "jobs")
        ).resolve()
        self.auth_root = Path(
            os.getenv("NETOPS_AUTH_ROOT", default_runtime_root / "auth")
        ).resolve()
        self.aws_profile = os.getenv("NETOPS_AWS_PROFILE", "netops")
        self.aws_config_template = os.getenv("NETOPS_AWS_CONFIG_TEMPLATE")
        self.frontend_origin = os.getenv("NETOPS_FRONTEND_ORIGIN", "http://localhost:5173")


@lru_cache
def get_settings() -> Settings:
    return Settings()
