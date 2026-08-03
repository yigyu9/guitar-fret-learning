"""대형 JSONL에서 그래프에 필요한 열만 읽는다."""
from __future__ import annotations

import json
from pathlib import Path


def load_metric_rows(path, keys):
    keys = tuple(keys)
    rows = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                source = json.loads(line)
                rows.append({key: source[key] for key in keys if key in source})
    return rows
