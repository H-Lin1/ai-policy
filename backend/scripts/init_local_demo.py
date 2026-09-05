"""Create idempotent local demonstration accounts for standalone PostgreSQL only."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid5

from sqlalchemy import insert, select, text

from app.core.config import Settings
from app.core.database import database_engine
from app.core.local_auth import hash_password
from app.modules.iam.models import Organization, Profile, Region, Role, User, UserRole

APPLY = "--apply-local-demo"
CONFIRM = "--confirm"
REVISION = "0005_consultation_workflow"
NAMESPACE = UUID("a980f1fb-e8e7-4e5d-b8c5-5c1c5908b965")
PASSWORD_ENV = "LOCAL_DEMO_PASSWORD"


@dataclass(frozen=True)
class DemoAccount:
    role: str
    username: str
    display_name: str
    organization_code: str | None

    @property
    def id(self) -> UUID:
        return uuid5(NAMESPACE, f"user:{self.username}")


ACCOUNTS = (
    DemoAccount("individual", "individual_demo", "个人演示用户", None),
    DemoAccount("enterprise", "enterprise_demo", "企业演示用户", "sz-demo-enterprise"),
    DemoAccount("government", "government_demo", "政府演示用户", "sz-demo-government"),
    DemoAccount("admin", "admin_demo", "管理员演示用户", "sz-platform"),
)
REGION_ID = UUID("10000000-0000-4000-8000-000000000001")
ROLE_IDS = {account.role: uuid5(NAMESPACE, f"role:{account.role}") for account in ACCOUNTS}
ORGANIZATIONS = {
    "sz-platform": (uuid5(NAMESPACE, "organization:platform"), "深圳政策服务平台", "platform", False),
    "sz-demo-government": (uuid5(NAMESPACE, "organization:government"), "深圳政策服务演示部门", "government", True),
    "sz-demo-enterprise": (uuid5(NAMESPACE, "organization:enterprise"), "深圳演示企业", "enterprise", True),
}


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if set(arguments) != {APPLY, CONFIRM}:
        print("local_demo: not_requested")
        return 0 if not arguments else 2
    runtime = settings or Settings()
    if runtime.database_mode != "standalone" or not runtime.normalized_database_url:
        print("local_demo: standalone_database_required")
        return 2
    password = os.environ.get(PASSWORD_ENV, "")
    if len(password) < 12:
        print("local_demo: password_not_configured")
        return 2
    engine = database_engine(runtime)
    if engine is None:
        print("local_demo: database_unavailable")
        return 2
    try:
        with engine.begin() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            if revision != REVISION:
                print("local_demo: revision_mismatch")
                return 2
            existing = connection.execute(select(User.id).where(User.username.in_([a.username for a in ACCOUNTS]))).scalars().all()
            if existing:
                print("local_demo: already_applied" if len(existing) == len(ACCOUNTS) else "local_demo: account_conflict")
                return 0 if len(existing) == len(ACCOUNTS) else 1
            connection.execute(insert(Region.__table__), [{"id": REGION_ID, "code": "sz", "name": "深圳市", "parent_id": None, "level": "city", "is_active": True}])
            connection.execute(insert(Role.__table__), [{"id": ROLE_IDS[a.role], "code": a.role, "name": {"individual": "个人", "enterprise": "企业", "government": "政府", "admin": "管理员"}[a.role], "description": f"{a.display_name}工作区", "is_active": True} for a in ACCOUNTS])
            connection.execute(insert(Organization.__table__), [{"id": item[0], "code": code, "name": item[1], "organization_type": item[2], "region_id": REGION_ID, "parent_id": None, "is_active": True, "is_demo": item[3]} for code, item in ORGANIZATIONS.items()])
            password_hash = hash_password(password)
            connection.execute(insert(User.__table__), [{"id": a.id, "username": a.username, "password_hash": password_hash, "email": None, "display_name": a.display_name, "is_active": True} for a in ACCOUNTS])
            connection.execute(insert(Profile.__table__), [{"user_id": a.id, "display_name": a.display_name, "region_id": REGION_ID, "organization_id": ORGANIZATIONS[a.organization_code][0] if a.organization_code else None, "status": "active", "is_demo": True} for a in ACCOUNTS])
            connection.execute(insert(UserRole.__table__), [{"user_id": a.id, "role_id": ROLE_IDS[a.role], "is_active": True} for a in ACCOUNTS])
    except Exception:
        print("local_demo: failed")
        return 1
    print("local_demo: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
