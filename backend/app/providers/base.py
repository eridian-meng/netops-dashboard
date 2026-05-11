from abc import ABC, abstractmethod
from typing import Mapping

from ..models import AuthProviderStatus, AuthStartResponse, ProviderName


class ProviderAdapter(ABC):
    name: ProviderName

    @abstractmethod
    def status(self, operator: str) -> AuthProviderStatus:
        raise NotImplementedError

    def start_login(self, operator: str) -> AuthStartResponse:
        return AuthStartResponse(
            provider=self.name,
            operator=operator,
            started=False,
            message=f"{self.name.value} interactive login is not implemented yet.",
        )

    def job_environment(self, operator: str) -> Mapping[str, str]:
        return {}
