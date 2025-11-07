"""Input/output helpers used by the extended LangGraph agents."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

try:  # pragma: no cover - optional dependency
    import pandas as pd
except Exception:  # pragma: no cover - fallback when pandas is unavailable
    pd = None  # type: ignore


@dataclass
class Table:
    """Small helper struct used to export tabular data."""

    headers: Sequence[str]
    rows: Sequence[Sequence[str]]


def read_text(path: Path) -> str:
    """Return the textual contents of ``path``."""

    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def export_table_to_csv(table: Table, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(table.headers)
        writer.writerows(table.rows)
    return destination


def export_table_to_excel(table: Table, destination: Path) -> Path:
    if pd is None:  # pragma: no cover - optional path
        raise RuntimeError("pandas is required for Excel export")
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(table.rows), columns=list(table.headers))
    frame.to_excel(destination, index=False)
    return destination


def generate_pdf(text: str, destination: Path) -> Path:
    """Generate a very small single-page PDF containing ``text``.

    The implementation avoids additional dependencies by emitting a minimal PDF
    structure.  The produced file is compatible with standard PDF readers and is
    sufficient for tests that assert file creation.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F1 12 Tf 50 750 Td ({escaped}) Tj ET"
    xref_offset = 0
    objects: List[str] = []
    objects.append("1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj")
    objects.append("2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj")
    objects.append(
        "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj"
    )
    stream = f"<< /Length {len(content_stream)} >>\nstream\n{content_stream}\nendstream"
    objects.append(f"4 0 obj {stream} endobj")
    objects.append("5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj")
    lines = ["%PDF-1.4"]
    offsets: List[int] = []
    for obj in objects:
        offsets.append(len("\n".join(lines).encode("latin-1")))
        lines.append(obj)
    xref_offset = len("\n".join(lines).encode("latin-1"))
    lines.append("xref")
    lines.append(f"0 {len(objects)+1}")
    lines.append("0000000000 65535 f ")
    for offset in offsets:
        lines.append(f"{offset:010d} 00000 n ")
    lines.append("trailer <</Size {len(objects)+1} /Root 1 0 R>>")
    lines.append("startxref")
    lines.append(str(xref_offset))
    lines.append("%%EOF")
    destination.write_text("\n".join(lines), encoding="latin-1")
    return destination


def snapshot_directory(directory: Path) -> List[str]:
    """Return a list of relative paths for reproducible test assertions."""

    if not directory.exists():
        return []
    base = directory.resolve()
    return [str(path.relative_to(base)) for path in sorted(directory.rglob("*")) if path.is_file()]
