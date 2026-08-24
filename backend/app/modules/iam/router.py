from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
)
from app.core.errors import AppError

from .schemas import RoleCode, WorkspaceResponse
from .service import IdentityContext, get_current_identity, role_title

NO_STORE = "no-store"

router = APIRouter(prefix="/iam", tags=["identity-access"])


@router.get(
    "/workspaces/{role}",
    response_model=WorkspaceResponse,
    summary="角色工作区访问检查",
    operation_id="iamWorkspaceAccess",
    responses={**COMMON_ERROR_RESPONSES, **AUTH_ERROR_RESPONSES, **IDENTITY_ERROR_RESPONSES},
)
def workspace_access(
    response: Response,
    role: RoleCode = Path(description="请求进入的稳定角色代码"),
    identity: IdentityContext = Depends(get_current_identity),
) -> WorkspaceResponse:
    response.headers["Cache-Control"] = NO_STORE
    if role not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权进入该工作区", status_code=403)
    return WorkspaceResponse(
        role=role,
        title=role_title(role),
        subject=identity.subject,
        region=(
            {"code": identity.region_code, "name": identity.region_name}
            if identity.region_code and identity.region_name
            else None
        ),
        organization=(
            {
                "code": identity.organization_code,
                "name": identity.organization_name,
                "organization_type": identity.organization_type,
            }
            if identity.organization_code and identity.organization_name and identity.organization_type
            else None
        ),
    )
