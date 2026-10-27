"""전체 곡 평가를 조건별로 비교하고 최상 checkpoint 경로를 기록한다."""
import argparse
import json
import math
from pathlib import Path


def summarize(directory):
    groups = {}
    for path in sorted(Path(directory).glob("*.events.json")):
        data = json.loads(path.read_text())
        metrics = data.get("episode_metrics", {})
        required = ("f1_l", "sustain_event_success_rate", "wrong_press_rate")
        if not all(k in metrics and math.isfinite(float(metrics[k])) for k in required):
            continue
        protocol = {k: data.get(k) for k in (
            "input_hashes", "evaluation_mode", "evaluation_seed", "preparation_frames",
            "evaluation_contract_sha256", "start_frame", "initial_pose",
            "extra_preparation_frames", "evaluation_scope", "hold_preparation_pose",
            "cached_preparation_action", "restore_source_state", "diagnostic_probe")}
        key = json.dumps(protocol, sort_keys=True)
        group = groups.setdefault(key, {"protocol": protocol, "evaluations": []})
        group["evaluations"].append({
            "checkpoint": data["checkpoint"], "report": str(path.resolve()),
            "completed": bool(data.get("goal_finished", False)),
            **{k: float(metrics[k]) for k in required},
            "fingers": [{"finger": i,
                         "success": metrics.get(f"press_finger_{i}_success"),
                         "count": metrics.get(f"press_finger_{i}_count")}
                        for i in range(1, 5)],
        })
    for group in groups.values():
        eligible = [r for r in group["evaluations"] if r["completed"]]
        group["best_completed"] = max(eligible, key=lambda r: (
            r["sustain_event_success_rate"], r["f1_l"], -r["wrong_press_rate"]
        ), default=None)
    return {"selection_order": ["completed", "sustain_event_success_rate", "f1_l",
                                "lower_wrong_press_rate"],
            "note": "단일 rollout 비교이며 안전 인증이나 다중 seed 통계 평가는 아니다. 계약 hash가 없는 과거 결과는 조건 일치를 보장하지 않는다.",
            "groups": list(groups.values())}


def save_summary(directory):
    output = Path(directory) / "evaluation_summary.json"
    output.write_text(json.dumps(summarize(directory), indent=2, ensure_ascii=False,
                                 allow_nan=False))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", type=Path)
    print(save_summary(parser.parse_args().videos))
