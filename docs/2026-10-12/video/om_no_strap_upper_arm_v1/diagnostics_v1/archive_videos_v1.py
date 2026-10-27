#!/usr/bin/env python3
"""Copy four completed no-strap trials' whole-body and hands videos byte-for-byte."""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path("/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1")
DEST = ROOT / "diagnostics_v1"
VERIFY = Path("/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/verification_v4.json")
CASES = {
    "pilot_left_away": ("pilot_left_away", "시험 1: 왼팔 이격 파일럿"),
    "pilot_left_high": ("pilot_left_high", "시험 2: 왼팔 높이 파일럿"),
    "upper_arm_close": ("upper_arm_close", "시험 3: 오른상완 근접 조건"),
    "upper_arm_preload_pi": ("upper_arm_preload_pi", "시험 4: 오른상완 preload 및 PI 조건"),
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    before_verify = sha(VERIFY)
    verified = json.loads(VERIFY.read_text(encoding="utf-8"))
    entries = []
    source_before = {}
    for key, (label_key, label) in CASES.items():
        case = verified["cases"][key]
        for view in ("whole_body", "hands"):
            item = case["videos"][view]
            src = Path(item["path"])
            expected = item["sha256"]
            actual_before = sha(src)
            if actual_before != expected:
                raise RuntimeError(f"source SHA mismatch: {src}")
            source_before[str(src)] = actual_before
            target = DEST / f"{label_key}_{view}.mp4"
            shutil.copyfile(src, target)
            copied = sha(target)
            if copied != expected:
                raise RuntimeError(f"copy SHA mismatch: {target}")
            entries.append({
                "source": str(src),
                "source_sha256": actual_before,
                "destination": str(target),
                "copy_sha256": copied,
                "label": label,
                "view": view,
            })
    source_after = {path: sha(Path(path)) for path in source_before}
    if source_before != source_after:
        raise RuntimeError("a source changed during archiving")
    if sha(VERIFY) != before_verify:
        raise RuntimeError("verification input changed during archiving")
    manifest = {"videos": entries}
    (ROOT / "manifest_v1.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verification_sha256": before_verify, "source_before": source_before, "source_after": source_after, "videos": entries}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
