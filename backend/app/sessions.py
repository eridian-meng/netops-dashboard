from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

SESSION_COOKIE = "netops_session"


@dataclass(frozen=True)
class OperatorIdentity:
    key: str
    label: str
    source: str


class SessionIdentityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        identity, should_set_cookie = resolve_identity(request)
        request.state.operator_identity = identity
        response = await call_next(request)
        if should_set_cookie:
            response.set_cookie(
                SESSION_COOKIE,
                identity.key,
                httponly=True,
                samesite="lax",
                secure=request.url.scheme == "https",
                max_age=60 * 60 * 12,
            )
        return response


def resolve_identity(request: Request) -> tuple[OperatorIdentity, bool]:
    trusted_user = (
        request.headers.get("x-auth-request-email")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-netops-auth-user")
    )
    if trusted_user:
        label = trusted_user.strip()
        return OperatorIdentity(key=f"user-{_safe_key(label)}", label=label, source="trusted-header"), False

    existing_session = request.cookies.get(SESSION_COOKIE)
    if existing_session:
        key = _safe_key(existing_session)
        return OperatorIdentity(key=key, label=f"Session {key[-8:]}", source="session-cookie"), False

    key = f"session-{uuid.uuid4().hex}"
    return OperatorIdentity(key=key, label=f"Session {key[-8:]}", source="session-cookie"), True


def get_operator_identity(request: Request) -> OperatorIdentity:
    return request.state.operator_identity


def get_operator(request: Request) -> str:
    return get_operator_identity(request).key


def _safe_key(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.@-]+", "-", value).strip("-").lower()
    return normalized or f"session-{uuid.uuid4().hex}"
