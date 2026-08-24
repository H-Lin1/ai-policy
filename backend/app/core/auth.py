from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from .config import Settings, get_settings
from .errors import AppError

bearer_scheme = HTTPBearer(auto_error=False)
JWT_ALGORITHMS = ("ES256", "RS256")


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    email: str | None = None
    development_bypass: bool = False


@lru_cache(maxsize=8)
def _get_jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(
        jwks_url,
        cache_keys=True,
        cache_jwk_set=True,
        lifespan=300,
        timeout=5,
    )


def _decode_token(token: str, settings: Settings) -> dict[str, Any]:
    jwks_url = settings.resolved_supabase_jwks_url
    issuer = settings.resolved_supabase_jwt_issuer
    audience = settings.resolved_supabase_jwt_audience
    if not jwks_url or not issuer or not audience:
        raise AppError(
            "AUTH_NOT_CONFIGURED",
            "服务端尚未配置 Supabase JWKS 验证信息",
            status_code=503,
        )

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") not in JWT_ALGORITHMS:
            raise jwt.InvalidAlgorithmError("unsupported signing algorithm")
        key_id = header.get("kid")
        if not isinstance(key_id, str) or not key_id.strip():
            raise jwt.InvalidTokenError("missing signing key id")
    except jwt.PyJWTError as exc:
        raise AppError(
            "AUTH_INVALID",
            "登录令牌无效或已过期",
            status_code=401,
        ) from exc

    try:
        signing_key = _get_jwks_client(jwks_url).get_signing_key(key_id)
    except jwt.PyJWKClientConnectionError as exc:
        raise AppError(
            "AUTH_NOT_CONFIGURED",
            "无法连接 Supabase JWKS 验证端点",
            status_code=503,
        ) from exc
    except jwt.PyJWKClientError as exc:
        if "Unable to find a signing key that matches" in str(exc):
            raise AppError("AUTH_INVALID", "登录令牌的签名密钥无效", status_code=401) from exc
        raise AppError(
            "AUTH_NOT_CONFIGURED",
            "Supabase JWKS 验证端点返回了无效配置",
            status_code=503,
        ) from exc
    except (jwt.PyJWKSetError, TypeError, ValueError) as exc:
        raise AppError(
            "AUTH_NOT_CONFIGURED",
            "Supabase JWKS 验证端点返回了无效配置",
            status_code=503,
        ) from exc

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(JWT_ALGORITHMS),
            audience=audience,
            issuer=issuer,
            leeway=settings.supabase_jwt_leeway_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError(
            "AUTH_INVALID",
            "登录令牌无效或已过期",
            status_code=401,
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise AppError("AUTH_INVALID", "登录令牌缺少有效主体", status_code=401)
    return payload


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if not settings.auth_required:
        if settings.is_production:
            raise AppError(
                "AUTH_NOT_CONFIGURED",
                "生产环境禁止绕过身份验证",
                status_code=503,
            )
        return Principal(subject="local-dev", development_bypass=True)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("AUTH_REQUIRED", "需要有效的 Bearer 登录令牌", status_code=401)
    payload = _decode_token(credentials.credentials, settings)
    email = payload.get("email")
    return Principal(
        subject=payload["sub"].strip(),
        email=email if isinstance(email, str) else None,
    )
