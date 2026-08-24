from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.supabase_target import (
    supabase_api_project_ref,
    supabase_database_project_ref,
    supabase_target_binding_state,
)

PROJECT_REF = "abcdefghijklmnopqrst"
OTHER_PROJECT_REF = "zyxwvutsrqponmlkjihg"


def settings_for(database_url: str, **overrides) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
        **overrides,
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (f"https://{PROJECT_REF}.supabase.co", PROJECT_REF),
        (f"https://{PROJECT_REF}.supabase.co/auth/v1", PROJECT_REF),
        ("https://custom.example.com", None),
        ("not-a-url", None),
        (None, None),
    ],
)
def test_supabase_api_project_ref_accepts_only_standard_hosts(url, expected) -> None:
    assert supabase_api_project_ref(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            f"postgresql+psycopg://postgres@db.{PROJECT_REF}.supabase.co/postgres",
            PROJECT_REF,
        ),
        (
            f"postgresql://postgres.{PROJECT_REF}@aws-0-us-east-1.pooler.supabase.com/postgres",
            PROJECT_REF,
        ),
        (
            f"postgres://postgres.{PROJECT_REF}%40ignored@aws-0.pooler.supabase.com/postgres",
            None,
        ),
        ("postgresql://postgres@example.invalid/postgres", None),
        ("sqlite:///runtime.db", None),
        (None, None),
    ],
)
def test_supabase_database_project_ref_handles_direct_and_pooler_urls(url, expected) -> None:
    assert supabase_database_project_ref(url) == expected


def test_supabase_target_binding_requires_every_endpoint_and_database_to_match() -> None:
    direct = f"postgresql+psycopg://postgres@db.{PROJECT_REF}.supabase.co/postgres"
    pooler = (
        f"postgresql+psycopg://postgres.{PROJECT_REF}"
        "@aws-0-ap-southeast-1.pooler.supabase.com/postgres"
    )
    assert supabase_target_binding_state(settings_for(direct)) == "ok"
    assert supabase_target_binding_state(settings_for(pooler)) == "ok"

    mismatch = f"postgresql+psycopg://postgres@db.{OTHER_PROJECT_REF}.supabase.co/postgres"
    assert supabase_target_binding_state(settings_for(mismatch)) == "project_mismatch"

    unresolved = "postgresql+psycopg://postgres@example.invalid/postgres"
    assert supabase_target_binding_state(settings_for(unresolved)) == "project_unresolved"

    wrong_jwks = settings_for(
        direct,
        supabase_jwks_url=(
            f"https://{OTHER_PROJECT_REF}.supabase.co/auth/v1/.well-known/jwks.json"
        ),
    )
    assert supabase_target_binding_state(wrong_jwks) == "project_mismatch"


def test_supabase_target_binding_handles_missing_and_invalid_configuration() -> None:
    assert supabase_target_binding_state(Settings(_env_file=None)) == "not_configured"

    class BrokenSettings:
        @property
        def normalized_database_url(self):
            raise RuntimeError("private-configuration-detail")

    assert supabase_target_binding_state(BrokenSettings()) == "configuration_invalid"


def test_alembic_environment_requires_the_shared_binding_before_configuring_url() -> None:
    source = (Path(__file__).parents[1] / "migrations" / "env.py").read_text(encoding="utf-8")
    binding_check = source.index("supabase_target_binding_state(settings)")
    configure_url = source.index("config.set_main_option")
    assert binding_check < configure_url
    assert "target_binding_state != \"ok\"" in source
