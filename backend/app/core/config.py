import re
import unicodedata
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single runtime configuration source for the API process."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Policy Service"
    app_env: str = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    host: str = "127.0.0.1"
    port: int = 8000

    auth_required: bool = True
    supabase_url: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_leeway_seconds: int = Field(default=30, ge=0, le=300)
    database_url: str | None = None

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allow_cors_wildcard: bool = False
    enable_mocks: bool = False
    policy_fixture_path: str | None = "app/modules/policy/fixtures/policies.jsonl"
    historical_qa_fixture_path: str | None = "app/modules/historical_qa/fixtures/historical_qa.jsonl"

    classifier_model_path: str | None = None
    classifier_tokenizer_path: str | None = None
    classifier_label_bindings_path: str | None = None
    classifier_department_embeddings_path: str | None = None
    classifier_model_version: str = "sz-tcn-bert-v1"
    classifier_supported_regions: str = "sz"

    iam_demo_individual_user_id: str | None = None
    iam_demo_enterprise_user_id: str | None = None
    iam_demo_government_user_id: str | None = None
    iam_demo_admin_user_id: str | None = None

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return "/api/v1"
        return "/" + value.strip("/")

    @field_validator(
        "supabase_url",
        "supabase_jwks_url",
        "supabase_jwt_issuer",
        "database_url",
        "iam_demo_individual_user_id",
        "iam_demo_enterprise_user_id",
        "iam_demo_government_user_id",
        "iam_demo_admin_user_id",
        "policy_fixture_path",
        "historical_qa_fixture_path",
        mode="before",
    )
    @classmethod
    def normalize_optional_runtime_value(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @property
    def parsed_cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        if self.allow_cors_wildcard and self.app_env == "development":
            return ["*"]
        return origins

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def classifier_configured(self) -> bool:
        values = (
            self.classifier_model_path,
            self.classifier_tokenizer_path,
            self.classifier_label_bindings_path,
            self.classifier_department_embeddings_path,
        )
        return all(isinstance(value, str) and bool(value.strip()) for value in values)

    @property
    def classifier_supported_region_ids(self) -> tuple[str, ...]:
        """Return the explicit, fail-closed region registry for the adapter."""

        pattern = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
        regions: list[str] = []
        for raw_region in self.classifier_supported_regions.split(","):
            region = unicodedata.normalize("NFKC", raw_region).strip().lower()
            if not region or not pattern.fullmatch(region) or region in regions:
                continue
            regions.append(region)
        return tuple(regions)

    @property
    def resolved_supabase_jwks_url(self) -> str | None:
        value = self.supabase_jwks_url
        if not value and self.supabase_url:
            value = f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return self._valid_http_url(value)

    @property
    def resolved_supabase_jwt_issuer(self) -> str | None:
        value = self.supabase_jwt_issuer
        if not value and self.supabase_url:
            value = f"{self.supabase_url.rstrip('/')}/auth/v1"
        return self._valid_http_url(value)

    @staticmethod
    def _valid_http_url(value: str | None) -> str | None:
        if not value:
            return None
        candidate = value.rstrip("/")
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return candidate

    @property
    def resolved_supabase_jwt_audience(self) -> str | None:
        audience = self.supabase_jwt_audience.strip()
        return audience or None

    @property
    def auth_configuration_status(self) -> str:
        if not self.auth_required:
            return "invalid_production_bypass" if self.is_production else "development_bypass"
        if (
            self.resolved_supabase_jwks_url
            and self.resolved_supabase_jwt_issuer
            and self.resolved_supabase_jwt_audience
        ):
            return "configured"
        return "not_configured"

    @property
    def normalized_database_url(self) -> str | None:
        """Use the installed psycopg driver for common PostgreSQL URL forms."""

        if not self.database_url:
            return None
        if self.database_url.startswith("postgres://"):
            return "postgresql+psycopg://" + self.database_url[len("postgres://") :]
        if self.database_url.startswith("postgresql://"):
            return "postgresql+psycopg://" + self.database_url[len("postgresql://") :]
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
