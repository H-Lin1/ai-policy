"""One registry for every feature flag the service exposes.

Business code resolves flags through this module instead of reading settings
attributes directly, so what is open is decided in one place and an unregistered
name fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings, get_settings

MOCKS = "mocks"


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    settings_attribute: str
    description: str
    production_forced_off: bool = False


FEATURE_FLAGS: tuple[FeatureFlag, ...] = (
    FeatureFlag(
        name=MOCKS,
        settings_attribute="enable_mocks",
        description="演示用 Mock 数据总闸，生产环境强制关闭",
        production_forced_off=True,
    ),
)

_FLAGS_BY_NAME = {flag.name: flag for flag in FEATURE_FLAGS}


def feature_enabled(name: str, settings: Settings | None = None) -> bool:
    """Resolve one flag, returning False for names that are not registered."""

    flag = _FLAGS_BY_NAME.get(name)
    if flag is None:
        return False
    settings = settings or get_settings()
    if flag.production_forced_off and settings.is_production:
        # A demonstration deployment must not serve Mock data even if misconfigured.
        return False
    return bool(getattr(settings, flag.settings_attribute, False))


def feature_snapshot(settings: Settings | None = None) -> dict[str, bool]:
    settings = settings or get_settings()
    return {flag.name: feature_enabled(flag.name, settings) for flag in FEATURE_FLAGS}


def non_compliant_flags(settings: Settings | None = None) -> list[str]:
    """Flags whose configured value is unsafe for the current environment.

    Forcing the safe value alone would hide the misconfiguration, so readiness
    reports the mismatch separately.
    """

    settings = settings or get_settings()
    if not settings.is_production:
        return []
    return [
        flag.name
        for flag in FEATURE_FLAGS
        if flag.production_forced_off and bool(getattr(settings, flag.settings_attribute, False))
    ]
