from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.modules.consultation.repository import ConsultationRecord
from app.modules.consultation.service import reply_to_consultation
from app.modules.iam.repository import RoleRecord
from app.modules.iam.service import IdentityContext

REQUESTER = UUID("00000000-0000-4000-8000-000000000111")
ASSIGNEE = UUID("00000000-0000-4000-8000-000000000222")
OTHER_DEPARTMENT = UUID("00000000-0000-4000-8000-000000000333")


class Session:
    def rollback(self) -> None: pass
    def commit(self) -> None: pass


@dataclass
class Repository:
    record: ConsultationRecord
    dedicated: bool = True

    def __post_init__(self) -> None:
        self.session = Session()
        self.calls: list[dict[str, object]] = []

    def assert_dedicated_government_account(self, **_: object) -> bool:
        return self.dedicated

    def get(self, _: UUID, *, lock: bool = False) -> ConsultationRecord | None:
        return self.record

    def complete_reply(self, **kwargs: object) -> ConsultationRecord:
        self.calls.append(kwargs)
        return self.record


def government(subject: UUID) -> IdentityContext:
    return IdentityContext(
        str(subject), None, "部门办理账号", (RoleRecord("government", "政府", True, True),),
        "sz", "深圳市", "dep-a", "部门 A", "government",
    )


def assigned_record() -> ConsultationRecord:
    return ConsultationRecord(
        id=uuid4(), requester_user_id=REQUESTER, selected_department_id="dept-a", selected_department_name="部门 A",
        assigned_organization_id=uuid4(), assigned_user_id=ASSIGNEE, question_text="含个人信息的原始咨询",
        status="assigned", classification_predictions={"items": [{"department_id": "dept-a", "department_name": "部门 A", "confidence": 0.9}]},
        answer_text=None, publish_to_history=False, historical_qa_id=None, created_at=datetime.now(UTC), replied_at=None, closed_at=None,
    )


def test_other_department_cannot_reply() -> None:
    repository = Repository(assigned_record())
    with pytest.raises(AppError) as raised:
        reply_to_consultation(identity=government(OTHER_DEPARTMENT), repository=repository, consultation_id=repository.record.id, answer="答复", publish_to_history=False, public_question=None, public_answer=None)
    assert raised.value.code == "CONSULTATION_FORBIDDEN"
    assert repository.calls == []


def test_public_reply_requires_explicit_deidentified_projection() -> None:
    repository = Repository(assigned_record())
    with pytest.raises(AppError) as raised:
        reply_to_consultation(identity=government(ASSIGNEE), repository=repository, consultation_id=repository.record.id, answer="内部答复", publish_to_history=True, public_question=None, public_answer=None)
    assert raised.value.code == "CONSULTATION_PUBLIC_PROJECTION_REQUIRED"
    assert repository.calls == []


def test_private_reply_has_no_public_projection() -> None:
    repository = Repository(assigned_record())
    reply_to_consultation(identity=government(ASSIGNEE), repository=repository, consultation_id=repository.record.id, answer="内部答复", publish_to_history=False, public_question=None, public_answer=None)
    assert repository.calls[0]["historical_qa"] is None


def test_public_reply_uses_only_explicit_public_text() -> None:
    repository = Repository(assigned_record())
    reply_to_consultation(identity=government(ASSIGNEE), repository=repository, consultation_id=repository.record.id, answer="内部答复", publish_to_history=True, public_question="已去标识问题", public_answer="已去标识答复")
    historical = repository.calls[0]["historical_qa"]
    assert historical is not None
    assert historical.question_text == "已去标识问题"
    assert historical.answer_text == "已去标识答复"
    assert "原始咨询" not in historical.question_text
