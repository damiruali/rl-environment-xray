"""Strict JSONL I/O. Never persists prompts, credentials or model reasoning."""

import json
from pathlib import Path

from xray.models import Transition


def write_jsonl(path: Path, rows: list[Transition]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(row.model_dump_json() + "\n")
    temporary.replace(path)


def read_jsonl(path: Path) -> list[Transition]:
    result = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                result.append(Transition.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{line_no}: invalid transition: {exc}") from exc
    if not result:
        raise ValueError("no transitions; insufficient evidence, not PASS")
    return result


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
