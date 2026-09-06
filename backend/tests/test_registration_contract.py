from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.modules.iam.router import _admin_identity
from app.modules.iam.schemas import IndividualRegistrationRequest
from app.modules.iam.service import IdentityContext


def identity(role: str) -> IdentityContext:
    return IdentityContext(
        subject="00000000-0000-4000-8000-000000000111",
        email=None,
        display_name="tester",
        roles=(type("Role", (), {"code": role, "name": role})(),),
        region_code="sz",
        region_name="深圳市",
        organization_code=None,
        organization_name=None,
        organization_type=None,
    )


def test_registration_request_forbids_role_escalation() -> None:
    with pytest.raises(ValidationError):
        IndividualRegistrationRequest.model_validate(
            {
                "username": "person@example.test",
                "password": "long-test-password",
                "password_confirmation": "long-test-password",
                "display_name": "个人用户",
                "terms_accepted": True,
                "role": "admin",
            }
        )


def test_admin_review_rejects_non_admin() -> None:
    with pytest.raises(AppError) as error:
        _admin_identity(identity("individual"))
    assert error.value.code == "ROLE_FORBIDDEN"
    assert error.value.status_code == 403
    assert _admin_identity(identity("admin")) == UUID("00000000-0000-4000-8000-000000000111")
