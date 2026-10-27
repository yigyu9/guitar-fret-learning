"""런타임 관절 제한 프로필 로더."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


HUMAN_JOINT_PROFILE_SCHEMA = "tab2body.fret-human-joint-profile.v1"


def apply_joint_limit_profile(dof_names, lower, upper, profile_path):
    """원본 배열을 보존하고 프로필에 명시된 관절만 좁힌다."""
    path = Path(profile_path).expanduser().resolve()
    with path.open(encoding="utf-8") as stream:
        profile = json.load(stream)
    if profile.get("schema") != HUMAN_JOINT_PROFILE_SCHEMA:
        raise ValueError(f"지원하지 않는 관절 제한 프로필: {profile.get('schema')}")
    joints = profile.get("joints")
    if not isinstance(joints, dict) or not joints:
        raise ValueError("관절 제한 프로필의 joints가 비어 있다")

    names = [str(name) for name in dof_names]
    name_to_index = {name: index for index, name in enumerate(names)}
    if len(name_to_index) != len(names):
        raise ValueError("DOF 이름이 중복되어 관절 제한을 적용할 수 없다")
    new_lower = np.asarray(lower, dtype=np.float32).copy()
    new_upper = np.asarray(upper, dtype=np.float32).copy()
    if new_lower.shape != new_upper.shape or new_lower.shape != (len(names),):
        raise ValueError("관절 제한 배열 크기가 DOF 이름과 일치하지 않는다")

    applied = []
    for name, entry in joints.items():
        if name not in name_to_index:
            raise ValueError(f"프로필 관절이 모델에 없다: {name}")
        try:
            lo = math.radians(float(entry["lower_deg"]))
            hi = math.radians(float(entry["upper_deg"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"잘못된 관절 제한 값: {name}") from exc
        if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
            raise ValueError(f"유효하지 않은 관절 제한 범위: {name}")
        index = name_to_index[name]
        authored_lo = float(new_lower[index])
        authored_hi = float(new_upper[index])
        tolerance = math.radians(0.02)
        if lo < authored_lo - tolerance or hi > authored_hi + tolerance:
            raise ValueError(
                f"프로필이 원본 hard limit을 넓힌다: {name} "
                f"[{math.degrees(lo):.3f}, {math.degrees(hi):.3f}]")
        lo = max(lo, authored_lo)
        hi = min(hi, authored_hi)
        if lo >= hi:
            raise ValueError(f"원본 범위와 겹치지 않는 관절 제한: {name}")
        new_lower[index] = lo
        new_upper[index] = hi
        applied.append({
            "name": name,
            "lower_deg": math.degrees(lo),
            "upper_deg": math.degrees(hi),
            "authored_lower_deg": math.degrees(authored_lo),
            "authored_upper_deg": math.degrees(authored_hi),
        })

    return new_lower, new_upper, {
        "enabled": True,
        "profile_path": str(path),
        "profile_schema": profile["schema"],
        "applied_joint_count": len(applied),
        "applied": applied,
    }
