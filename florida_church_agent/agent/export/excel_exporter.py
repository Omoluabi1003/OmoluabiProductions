"""Excel export support."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from agent.models import CleanChurchRecord


def export_excel(records: list[CleanChurchRecord], path: Path) -> None:
    data = [record.model_dump() for record in records]
    pd.DataFrame(data).to_excel(path, index=False)
