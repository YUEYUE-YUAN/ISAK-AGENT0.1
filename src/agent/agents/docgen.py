"""Document generation agent."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agent.tools.io_utils import Table, export_table_to_csv, generate_pdf


@dataclass
class DocumentGenerationAgent:
    output_directory: Path

    def create_report(self, title: str, body: str) -> Path:
        destination = self.output_directory / f"{title.replace(' ', '_').lower()}.pdf"
        return generate_pdf(body, destination)

    def export_table(self, name: str, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> Path:
        destination = self.output_directory / f"{name.replace(' ', '_').lower()}.csv"
        table = Table(headers=headers, rows=rows)
        return export_table_to_csv(table, destination)
