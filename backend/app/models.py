from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CatalogItemType(str, Enum):
    folder = "folder"
    service = "service"
    script = "script"


class ProviderName(str, Enum):
    aws = "aws"
    azure = "azure"
    gcp = "gcp"
    generic = "generic"


class CatalogItem(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "/icons/default.svg"
    type: CatalogItemType
    provider: ProviderName = ProviderName.generic
    path: str = ""
    scriptPath: Optional[str] = None
    scriptGroupPath: Optional[str] = None
    auth: dict[str, Any] = Field(default_factory=dict)
    children: list["CatalogItem"] = Field(default_factory=list)


class CatalogResponse(BaseModel):
    items: list[CatalogItem]


class AuthProviderStatus(BaseModel):
    provider: ProviderName
    available: bool
    authenticated: bool
    operator: str
    profile: Optional[str] = None
    identity: Optional[dict[str, Any]] = None
    message: str = ""
    loginLog: str = ""


class AuthStartResponse(BaseModel):
    provider: ProviderName
    operator: str
    started: bool
    message: str
    logPath: Optional[str] = None


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class JobCreateRequest(BaseModel):
    catalogItemId: str


class JobArtifact(BaseModel):
    id: str
    name: str
    size: int


class JobRecord(BaseModel):
    id: str
    catalogItemId: str
    catalogItemName: str
    provider: ProviderName
    operator: str
    status: JobStatus
    createdAt: datetime
    startedAt: Optional[datetime] = None
    finishedAt: Optional[datetime] = None
    exitCode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    artifacts: list[JobArtifact] = Field(default_factory=list)
    message: str = ""
