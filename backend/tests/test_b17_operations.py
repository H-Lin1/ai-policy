from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from scripts import integration_acceptance, reset_b17_demo


def test_b17_reset_requires_both_apply_flags(monkeypatch, capsys) -> None:
    called: list[bool] = []

    def fake_reset(*, settings, apply):
        called.append(apply)
        return True, "already_clean", reset_b17_demo.ResetCounts(0, 0, 0)

    monkeypatch.setattr(reset_b17_demo, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(reset_b17_demo, "reset", fake_reset)
    assert reset_b17_demo.main([reset_b17_demo.CONFIRM]) == 2
    assert called == []
    assert "invalid_arguments" in capsys.readouterr().out


def test_b17_reset_preflight_is_read_only(monkeypatch, capsys) -> None:
    calls: list[bool] = []

    def fake_reset(*, settings, apply):
        calls.append(apply)
        return True, "already_clean", reset_b17_demo.ResetCounts(0, 0, 0)

    monkeypatch.setattr(reset_b17_demo, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(reset_b17_demo, "reset", fake_reset)
    assert reset_b17_demo.main([]) == 0
    assert calls == [False]
    output = capsys.readouterr().out
    assert "already_clean" in output
    assert "consultations=0" in output


def test_b17_reset_marker_and_deletion_scope_are_explicit() -> None:
    source = Path(reset_b17_demo.__file__).read_text(encoding="utf-8")
    assert reset_b17_demo.MARKER in source
    assert "app.consultation_events" in source
    assert "app.consultations" in source
    assert "app.historical_qa" in source
    assert "auth.users" not in source
    assert "policy_documents" not in source
    assert "TRUNCATE" not in source.upper()


def test_b17_audit_combines_named_checks(monkeypatch) -> None:
    monkeypatch.setattr(integration_acceptance, "_database_checks", lambda settings: {"database": True})
    monkeypatch.setattr(integration_acceptance, "_route_checks", lambda settings: {"routes": True})
    monkeypatch.setattr(integration_acceptance, "_local_gates", lambda: {"tests": True})
    assert integration_acceptance.run(settings=Settings(_env_file=None)) == {
        "database": True,
        "routes": True,
        "tests": True,
    }
