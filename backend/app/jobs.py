from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .catalog import CatalogService
from .config import Settings
from .models import CatalogItem, JobArtifact, JobRecord, JobStatus, ProviderName
from .providers.base import ProviderAdapter


class JobStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.jobs_root.mkdir(parents=True, exist_ok=True)

    def create(self, item: CatalogItem, operator: str) -> JobRecord:
        job = JobRecord(
            id=str(uuid.uuid4()),
            catalogItemId=item.id,
            catalogItemName=item.name,
            provider=item.provider,
            operator=operator,
            status=JobStatus.queued,
            createdAt=_now(),
        )
        self._job_dir(job.id).mkdir(parents=True, exist_ok=True)
        self.save(job)
        return job

    def get(self, job_id: str) -> JobRecord:
        path = self._metadata_path(job_id)
        if not path.exists():
            raise FileNotFoundError(job_id)
        return JobRecord.model_validate_json(path.read_text())

    def save(self, job: JobRecord) -> None:
        self._metadata_path(job.id).write_text(job.model_dump_json(indent=2))

    def artifact_path(self, job_id: str, artifact_id: str) -> Path:
        candidate = (self._job_dir(job_id) / "artifacts" / artifact_id).resolve()
        artifacts_root = (self._job_dir(job_id) / "artifacts").resolve()
        if artifacts_root not in [candidate, *candidate.parents] or not candidate.is_file():
            raise FileNotFoundError(artifact_id)
        return candidate

    def _job_dir(self, job_id: str) -> Path:
        return self.settings.jobs_root / job_id

    def _metadata_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"


def run_job(
    job_id: str,
    catalog_service: CatalogService,
    store: JobStore,
    providers: dict[ProviderName, ProviderAdapter],
) -> None:
    job = store.get(job_id)
    job.status = JobStatus.running
    job.startedAt = _now()
    store.save(job)

    job_dir = store.settings.jobs_root / job.id
    artifacts_dir = job_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    try:
        item = catalog_service.find_item(job.catalogItemId)
        script_path = catalog_service.resolve_script(item)
        provider = providers.get(item.provider)
        env = {
            **os.environ,
            "NETOPS_JOB_ID": job.id,
            "NETOPS_ARTIFACT_DIR": str(artifacts_dir),
            "NETOPS_OPERATOR": job.operator,
        }
        if provider:
            env.update(provider.job_environment(job.operator))

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,
            env=env,
            text=True,
            capture_output=True,
            timeout=3600,
            check=False,
        )
        job.exitCode = result.returncode
        job.stdout = result.stdout[-20000:]
        job.stderr = result.stderr[-20000:]
        job.status = JobStatus.succeeded if result.returncode == 0 else JobStatus.failed
        job.message = "Completed successfully." if result.returncode == 0 else "Script failed."
    except Exception as exc:
        job.status = JobStatus.failed
        job.stderr = f"{type(exc).__name__}: {exc}"
        job.message = "Job failed before the script completed."
    finally:
        job.finishedAt = _now()
        job.artifacts = _list_artifacts(artifacts_dir)
        store.save(job)


def _list_artifacts(artifacts_dir: Path) -> list[JobArtifact]:
    if not artifacts_dir.exists():
        return []
    artifacts: list[JobArtifact] = []
    for path in sorted(artifacts_dir.iterdir()):
        if path.is_file():
            artifacts.append(JobArtifact(id=path.name, name=path.name, size=path.stat().st_size))
    return artifacts


def _now() -> datetime:
    return datetime.now(timezone.utc)
