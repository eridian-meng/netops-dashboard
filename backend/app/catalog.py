import json
from pathlib import Path
from typing import Iterable

from .config import Settings
from .models import CatalogItem


class CatalogError(RuntimeError):
    pass


class CatalogService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def load(self) -> list[CatalogItem]:
        if not self.settings.catalog_path.exists():
            raise CatalogError(f"Catalog not found: {self.settings.catalog_path}")
        raw = json.loads(self.settings.catalog_path.read_text())
        items = [CatalogItem.model_validate(item) for item in raw.get("items", [])]
        for item in self._walk(items):
            if item.scriptPath:
                self._resolve_registered_path(item.scriptPath, expect_file=True)
            if item.scriptGroupPath:
                self._resolve_registered_path(item.scriptGroupPath, expect_file=False)
        return items

    def find_item(self, item_id: str) -> CatalogItem:
        for item in self._walk(self.load()):
            if item.id == item_id:
                return item
        raise CatalogError(f"Catalog item is not registered: {item_id}")

    def resolve_script(self, item: CatalogItem) -> Path:
        if item.scriptPath:
            return self._resolve_registered_path(item.scriptPath, expect_file=True)
        if item.scriptGroupPath:
            group = self._resolve_registered_path(item.scriptGroupPath, expect_file=False)
            for candidate in ("main.py", "run.py"):
                script = group / candidate
                if script.exists():
                    return script
            raise CatalogError(f"No main.py or run.py found in script group: {item.scriptGroupPath}")
        raise CatalogError(f"Catalog item is not runnable: {item.id}")

    def _resolve_registered_path(self, relative_path: str, expect_file: bool) -> Path:
        candidate = (self.settings.services_root / relative_path).resolve()
        services_root = self.settings.services_root.resolve()
        if services_root not in [candidate, *candidate.parents]:
            raise CatalogError(f"Script path escapes services root: {relative_path}")
        if expect_file and not candidate.is_file():
            raise CatalogError(f"Registered script does not exist: {relative_path}")
        if not expect_file and not candidate.is_dir():
            raise CatalogError(f"Registered script group does not exist: {relative_path}")
        return candidate

    def _walk(self, items: Iterable[CatalogItem]) -> Iterable[CatalogItem]:
        for item in items:
            yield item
            yield from self._walk(item.children)
