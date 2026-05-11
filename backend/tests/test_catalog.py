import json
from pathlib import Path

import pytest

from app.catalog import CatalogError, CatalogService
from app.config import Settings


def make_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.catalog_path = tmp_path / "catalog.json"
    settings.services_root = tmp_path / "services"
    settings.jobs_root = tmp_path / "jobs"
    settings.auth_root = tmp_path / "auth"
    settings.services_root.mkdir()
    return settings


def test_loads_nested_catalog_and_resolves_script(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    script = settings.services_root / "architecture-diagram" / "aws" / "generate.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('ok')")
    settings.catalog_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "architecture-diagram",
                        "name": "Architecture Diagram",
                        "type": "folder",
                        "path": "/architecture-diagram",
                        "children": [
                            {
                                "id": "architecture-diagram-aws",
                                "name": "AWS Architecture Diagram",
                                "type": "script",
                                "provider": "aws",
                                "path": "/architecture-diagram/aws",
                                "scriptPath": "architecture-diagram/aws/generate.py",
                            }
                        ],
                    }
                ]
            }
        )
    )

    service = CatalogService(settings)
    item = service.find_item("architecture-diagram-aws")

    assert item.name == "AWS Architecture Diagram"
    assert service.resolve_script(item) == script.resolve()


def test_rejects_script_path_outside_services_root(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    settings.catalog_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "unsafe",
                        "name": "Unsafe",
                        "type": "script",
                        "path": "/unsafe",
                        "scriptPath": "../outside.py",
                    }
                ]
            }
        )
    )

    with pytest.raises(CatalogError):
        CatalogService(settings).load()
