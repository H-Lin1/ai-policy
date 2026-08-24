from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from app.core.config import Settings

PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")


def _project_ref(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip().lower()
    return candidate if PROJECT_REF_PATTERN.fullmatch(candidate) else None


def supabase_api_project_ref(url: str | None) -> str | None:
    """Resolve the project ref only from the standard Supabase API hostname."""

    if not isinstance(url, str) or not url.strip():
        return None
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return None
    hostname = (parsed.hostname or "").lower()
    suffix = ".supabase.co"
    if parsed.scheme not in {"http", "https"} or not hostname.endswith(suffix):
        return None
    prefix = hostname[: -len(suffix)]
    if "." in prefix:
        return None
    return _project_ref(prefix)


def supabase_database_project_ref(url: str | None) -> str | None:
    """Resolve a project ref from a standard direct or Supavisor database URL."""

    if not isinstance(url, str) or not url.strip():
        return None
    normalized = re.sub(r"^postgresql\+[a-z0-9_]+://", "postgresql://", url.strip(), count=1)
    try:
        parsed = urlsplit(normalized)
    except ValueError:
        return None
    if parsed.scheme not in {"postgres", "postgresql"}:
        return None

    hostname = (parsed.hostname or "").lower()
    direct_suffix = ".supabase.co"
    if hostname.startswith("db.") and hostname.endswith(direct_suffix):
        direct_ref = hostname[len("db.") : -len(direct_suffix)]
        if "." not in direct_ref:
            return _project_ref(direct_ref)

    if hostname.endswith(".pooler.supabase.com"):
        username = unquote(parsed.username or "").lower()
        prefix = "postgres."
        if username.startswith(prefix):
            return _project_ref(username[len(prefix) :])
    return None


def supabase_target_binding_state(settings: Settings) -> str:
    """Return a stable state without exposing either configured target."""

    try:
        database_url = settings.normalized_database_url
        api_url = settings.supabase_url
        jwks_url = settings.resolved_supabase_jwks_url
        issuer_url = settings.resolved_supabase_jwt_issuer
    except Exception:  # noqa: BLE001 - configuration parsing may contain private values.
        return "configuration_invalid"

    if not database_url or not api_url:
        return "not_configured"

    database_ref = supabase_database_project_ref(database_url)
    endpoint_refs = [
        supabase_api_project_ref(api_url),
        supabase_api_project_ref(jwks_url),
        supabase_api_project_ref(issuer_url),
    ]
    if database_ref is None or any(project_ref is None for project_ref in endpoint_refs):
        return "project_unresolved"
    if len({database_ref, *endpoint_refs}) != 1:
        return "project_mismatch"
    return "ok"
