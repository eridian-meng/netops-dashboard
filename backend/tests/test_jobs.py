import json
from pathlib import Path

from app.catalog import CatalogService
from app.config import Settings
from app.jobs import JobStore, run_job
from app.providers.registry import build_providers


def make_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.catalog_path = tmp_path / "catalog.json"
    settings.services_root = tmp_path / "services"
    settings.jobs_root = tmp_path / "jobs"
    settings.auth_root = tmp_path / "auth"
    settings.services_root.mkdir()
    return settings


def test_job_runs_registered_script_and_collects_artifact(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    script = settings.services_root / "demo" / "run.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import os\n"
        "from pathlib import Path\n"
        "Path(os.environ['NETOPS_ARTIFACT_DIR'], 'result.txt').write_text('done')\n"
        "print('ran script')\n"
    )
    settings.catalog_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "demo",
                        "name": "Demo",
                        "type": "script",
                        "provider": "generic",
                        "path": "/demo",
                        "scriptPath": "demo/run.py",
                    }
                ]
            }
        )
    )

    catalog = CatalogService(settings)
    item = catalog.find_item("demo")
    store = JobStore(settings)
    job = store.create(item, "tester")

    run_job(job.id, catalog, store, build_providers(settings))
    completed = store.get(job.id)

    assert completed.status == "succeeded"
    assert completed.exitCode == 0
    assert "ran script" in completed.stdout
    assert [artifact.name for artifact in completed.artifacts] == ["result.txt"]
    assert store.artifact_path(completed.id, "result.txt").read_text() == "done"
