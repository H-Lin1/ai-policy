from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.iam.models import Region
from app.modules.iam.service import IdentityContext

from .markdown import parse_markdown
from .models import PolicyDocument, PolicyDocumentEvent
from .schemas import (
    AdminPolicyCreateRequest,
    AdminPolicyRecord,
    MarkdownBatchRequest,
    MarkdownBatchResponse,
)


def admin_actor(identity: IdentityContext) -> UUID:
    if "admin" not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "只有管理员可以管理政策", status_code=403)
    try:
        return UUID(identity.subject)
    except ValueError as exc:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def parse_batch(payload: MarkdownBatchRequest) -> MarkdownBatchResponse:
    return MarkdownBatchResponse(items=[parse_markdown(item.filename, item.content) for item in payload.files])


def _record(model: PolicyDocument) -> AdminPolicyRecord:
    return AdminPolicyRecord(
        id=model.id, title=model.title, document_no=model.document_no,
        issuing_organization=model.issuing_organization, source_url=model.source_url,
        document_url=model.document_url, published_date=model.published_date,
        effective_status=model.effective_status, content_text=model.content_text,
        source_type=model.source_type, raw_markdown=model.raw_markdown,
        publication_status=model.publication_status, content_sha256=model.content_sha256,
        created_at=model.created_at, published_at=model.published_at, withdrawn_at=model.withdrawn_at,
    )


def list_admin_policies(session: Session, status: str | None = None) -> list[AdminPolicyRecord]:
    statement = select(PolicyDocument).order_by(PolicyDocument.created_at.desc())
    if status in {"draft", "published", "withdrawn"}:
        statement = statement.where(PolicyDocument.publication_status == status)
    return [_record(item) for item in session.execute(statement).scalars()]


def get_admin_policy(session: Session, policy_id: UUID, *, lock: bool = False) -> PolicyDocument:
    statement = select(PolicyDocument).where(PolicyDocument.id == policy_id)
    if lock:
        statement = statement.with_for_update()
    item = session.execute(statement).scalar_one_or_none()
    if item is None:
        raise AppError("POLICY_NOT_FOUND", "政策记录不存在", status_code=404)
    return item


def create_policy(*, session: Session, payload: AdminPolicyCreateRequest, actor_id: UUID) -> AdminPolicyRecord:
    title = payload.title.strip()
    body = payload.content_text.strip()
    source_url = payload.source_url.strip() if payload.source_url else None
    document_url = payload.document_url.strip() if payload.document_url else None
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    raw_digest = hashlib.sha256(payload.raw_markdown.encode("utf-8")).hexdigest() if payload.raw_markdown else None
    conflicts = [PolicyDocument.content_sha256 == digest]
    if raw_digest:
        conflicts.append(PolicyDocument.raw_markdown_sha256 == raw_digest)
    if payload.document_no:
        conflicts.append(PolicyDocument.document_no == payload.document_no.strip())
    if source_url:
        conflicts.append(PolicyDocument.source_url == source_url)
    if session.execute(select(PolicyDocument.id).where(or_(*conflicts))).scalar_one_or_none():
        raise AppError("POLICY_DUPLICATE", "政策内容或标识已存在", status_code=409)
    region = session.execute(select(Region).where(Region.code == "sz", Region.is_active.is_(True))).scalar_one_or_none()
    if region is None:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503)
    now = datetime.now(UTC)
    status = "published" if payload.action == "publish" else "draft"
    item = PolicyDocument(
        region_id=region.id, region_code="sz", title=title,
        document_no=payload.document_no.strip() if payload.document_no else None,
        issuing_organization=payload.issuing_organization.strip(), source_url=source_url,
        document_url=document_url, published_date=payload.published_date, collected_at=now,
        content_text=body, content_sha256=digest, effective_status=payload.effective_status,
        requested_title=title, source_type=payload.source_type, publication_status=status,
        raw_markdown=payload.raw_markdown, raw_markdown_sha256=raw_digest, created_by=actor_id,
        published_by=actor_id if status == "published" else None,
        published_at=now if status == "published" else None,
    )
    try:
        session.add(item); session.flush()
        session.add(PolicyDocumentEvent(policy_id=item.id, event_type="published" if status == "published" else "drafted", actor_user_id=actor_id))
        session.commit(); session.refresh(item)
        return _record(item)
    except IntegrityError as exc:
        session.rollback()
        raise AppError("POLICY_DUPLICATE", "政策内容或标识已存在", status_code=409) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503) from exc


def publish_policy(*, session: Session, policy_id: UUID, actor_id: UUID) -> AdminPolicyRecord:
    item = get_admin_policy(session, policy_id, lock=True)
    if item.publication_status != "draft":
        raise AppError("POLICY_NOT_EDITABLE", "仅草稿可以发布", status_code=409)
    now = datetime.now(UTC); item.publication_status = "published"; item.published_by = actor_id; item.published_at = now
    session.add(PolicyDocumentEvent(policy_id=item.id, event_type="published", actor_user_id=actor_id)); session.commit(); session.refresh(item)
    return _record(item)


def withdraw_policy(*, session: Session, policy_id: UUID, actor_id: UUID, reason: str) -> AdminPolicyRecord:
    item = get_admin_policy(session, policy_id, lock=True)
    if item.publication_status != "published":
        raise AppError("POLICY_NOT_EDITABLE", "仅已发布政策可以撤回", status_code=409)
    now = datetime.now(UTC); item.publication_status = "withdrawn"; item.withdrawn_by = actor_id; item.withdrawn_at = now
    session.add(PolicyDocumentEvent(policy_id=item.id, event_type="withdrawn", actor_user_id=actor_id, reason=reason.strip())); session.commit(); session.refresh(item)
    return _record(item)
