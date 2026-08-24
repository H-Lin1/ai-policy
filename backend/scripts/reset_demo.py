from __future__ import annotations

import sys
from collections.abc import Sequence

CONFIRM = "--confirm"


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Acknowledge the deliberate Stage 0 no-op without touching managed data."""

    arguments = _arguments(argv)
    if any(argument != CONFIRM for argument in arguments):
        print("demo_reset: invalid_arguments")
        return 2
    if CONFIRM not in arguments:
        print("demo_reset: confirmation_required")
        return 2

    print("demo_reset: no_stage_zero_business_data")
    print("No reset, deletion, filesystem change, or database operation was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
