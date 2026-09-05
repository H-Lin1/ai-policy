from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from .config import Settings
from .errors import AppError

PASSWORD_PREFIX = "scrypt"
PASSWORD_N = 32768
PASSWORD_R = 8
PASSWORD_P = 1
PASSWORD_MAXMEM = 64 * 1024 * 1024


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("password does not meet the minimum length")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=PASSWORD_N,
        r=PASSWORD_R,
        p=PASSWORD_P,
        maxmem=PASSWORD_MAXMEM,
    )
    return "$".join(
        (
            PASSWORD_PREFIX,
            str(PASSWORD_N),
            str(PASSWORD_R),
            str(PASSWORD_P),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        prefix, raw_n, raw_r, raw_p, raw_salt, raw_digest = password_hash.split("$", 6)
        if prefix != PASSWORD_PREFIX:
            return False
        salt = base64.urlsafe_b64decode(raw_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(raw_digest.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(raw_n),
            r=int(raw_r),
            p=int(raw_p),
            maxmem=PASSWORD_MAXMEM,
        )
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False


def issue_token(*, user_id: UUID, username: str, settings: Settings) -> tuple[str, int]:
    secret = settings.local_auth_jwt_secret
    if not secret or len(secret) < 32:
        raise AppError("AUTH_NOT_CONFIGURED", "本地登录服务尚未配置", status_code=503)
    now = datetime.now(UTC)
    expires_in = settings.local_auth_token_ttl_seconds
    token = jwt.encode(
        {
            "sub": str(user_id),
            "username": username,
            "iss": settings.local_auth_jwt_issuer,
            "aud": settings.local_auth_jwt_audience,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        },
        secret,
        algorithm="HS256",
    )
    return token, expires_in


def decode_token(token: str, settings: Settings) -> dict[str, object]:
    secret = settings.local_auth_jwt_secret
    if not secret or len(secret) < 32:
        raise AppError("AUTH_NOT_CONFIGURED", "本地登录服务尚未配置", status_code=503)
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=settings.local_auth_jwt_audience,
            issuer=settings.local_auth_jwt_issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError("AUTH_INVALID", "登录令牌无效或已过期", status_code=401) from exc
