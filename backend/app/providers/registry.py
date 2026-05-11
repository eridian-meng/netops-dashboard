from ..config import Settings
from ..models import AuthProviderStatus, ProviderName
from .aws import AwsProvider
from .base import ProviderAdapter


class PlaceholderProvider(ProviderAdapter):
    def __init__(self, name: ProviderName) -> None:
        self.name = name

    def status(self, operator: str) -> AuthProviderStatus:
        return AuthProviderStatus(
            provider=self.name,
            available=False,
            authenticated=False,
            operator=operator,
            message=f"{self.name.value.upper()} provider adapter is reserved for a future implementation.",
        )


def build_providers(settings: Settings) -> dict[ProviderName, ProviderAdapter]:
    return {
        ProviderName.aws: AwsProvider(settings),
        ProviderName.azure: PlaceholderProvider(ProviderName.azure),
        ProviderName.gcp: PlaceholderProvider(ProviderName.gcp),
        ProviderName.generic: PlaceholderProvider(ProviderName.generic),
    }
