"""Run summary output helpers."""

from __future__ import annotations

import json
from pathlib import Path

from agent.models import RunSummary


def write_run_summary(summary: RunSummary, path: Path) -> None:
    path.write_text(json.dumps(summary.model_dump(mode="json"), indent=2), encoding="utf-8")
