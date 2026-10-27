"""학습 종료 후에만 실행하는 자원·수명 분석. 기존 원자료는 읽기 전용이다."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

GIB = 1024 ** 3
PHASE = Path(__file__).resolve().parent
OLD = PHASE.parent / "guitar_learning_long_B_8env_dense_v2_20261018_130137"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_new(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def ols(points):
    result = {"n": len(points), "slope_GiB_per_hour": None, "r_squared": None}
    if not points:
        return result
    result.update(start_s=points[0][0], end_s=points[-1][0],
                  span_s=points[-1][0] - points[0][0])
    result["limited_window"] = len(points) < 20 or result["span_s"] < 300
    if len(points) < 2:
        return result
    mx = sum(x for x, _ in points) / len(points)
    my = sum(y for _, y in points) / len(points)
    xx = sum((x - mx) ** 2 for x, _ in points)
    yy = sum((y - my) ** 2 for _, y in points)
    xy = sum((x - mx) * (y - my) for x, y in points)
    if xx:
        result["slope_GiB_per_hour"] = xy / xx * 3600
        result["r_squared"] = max(0.0, min(1.0, xy * xy / (xx * yy))) if yy else None
    return result


def endpoint(row):
    return {key: row.get(key) for key in (
        "elapsed_s", "wall_time_utc", "phase", "operation", "update_index", "ticks",
        "worker_current_rss_GiB", "worker_current_pss_GiB", "worker_peak_rss_sum_GiB",
        "parent_current_rss_GiB", "parent_current_pss_GiB", "parent_peak_rss_GiB")}


def analyze_resources(rows, expected=8):
    complete = []
    signature = None
    rejected = {"incomplete_workers_or_current_memory": 0, "changed_worker_pids": 0}
    for raw in rows:
        workers = raw.get("workers", [])
        ids = [w.get("worker_id") for w in workers]
        if (len(workers) != expected or set(ids) != set(range(expected)) or
                any(not isinstance(w.get("memory", {}).get(k), (int, float))
                    for w in workers for k in ("rss_current_bytes", "pss_current_bytes"))):
            rejected["incomplete_workers_or_current_memory"] += 1
            continue
        current = tuple(sorted((w["worker_id"], w.get("pid")) for w in workers))
        if signature is None:
            signature = current
        if current != signature:
            rejected["changed_worker_pids"] += 1
            continue
        row = {key: raw.get(key) for key in (
            "elapsed_s", "wall_time_utc", "phase", "operation", "update_index", "ticks")}
        for metric, key in (("rss", "rss_current_bytes"), ("pss", "pss_current_bytes")):
            row["worker_current_" + metric + "_GiB"] = sum(w["memory"][key] for w in workers) / GIB
        peaks = [w["memory"].get("rss_peak_bytes") for w in workers]
        row["worker_peak_rss_sum_GiB"] = sum(peaks) / GIB if all(isinstance(x, (int, float)) for x in peaks) else None
        for name, key in (("current_rss", "rss_current_bytes"),
                          ("current_pss", "pss_current_bytes"), ("peak_rss", "rss_peak_bytes")):
            value = raw.get("parent_memory", {}).get(key)
            row["parent_" + name + "_GiB"] = value / GIB if isinstance(value, (int, float)) else None
        complete.append(row)
    complete.sort(key=lambda r: r["elapsed_s"])
    last_time = complete[-1]["elapsed_s"] if complete else 0
    windows = {
        "after_60s": [r for r in complete if r["elapsed_s"] >= 60],
        "latter_half_of_observed_elapsed_time": [r for r in complete if r["elapsed_s"] >= max(60, last_time / 2)],
        "last_600s": [r for r in complete if r["elapsed_s"] >= max(60, last_time - 600)],
    }
    fits = {}
    for name, window in windows.items():
        fits[name] = {metric: ols([(r["elapsed_s"], r[metric]) for r in window])
                      for metric in ("worker_current_rss_GiB", "worker_current_pss_GiB")}
    available = [r["available_memory_bytes"] for r in rows if isinstance(r.get("available_memory_bytes"), (int, float))]
    minima = [r["min_available_memory_bytes"] for r in rows if isinstance(r.get("min_available_memory_bytes"), (int, float))]
    post60 = windows["after_60s"]
    return {
        "resource_rows": len(rows), "complete_same_eight_worker_samples": len(complete),
        "worker_pid_signature": signature, "rejected_samples": rejected,
        "first_complete": endpoint(complete[0]) if complete else None,
        "first_complete_after_60s": endpoint(post60[0]) if post60 else None,
        "last_complete": endpoint(complete[-1]) if complete else None,
        "global_MemAvailable_min_GiB": min(available + minima) / GIB if available or minima else None,
        "fits": fits, "complete_series": complete,
        "scope": "RSS includes shared pages; PSS apportions them. Worker peak sum is a sum of per-process high-water marks, not simultaneous current usage. OLS is descriptive: serially correlated samples are not independent evidence or a leak-free guarantee. Missing/dead worker samples are excluded, never treated as zero.",
    }


def summarize_report(report, status):
    timers = report.get("timers", {})
    wall = report.get("wall_s")
    updates = report.get("updates", [])
    close = report.get("pool_close_diagnostics", [])
    ranges = {}
    for key in ("collection_s", "update_s"):
        values = [u[key] for u in updates if isinstance(u.get(key), (int, float))]
        ranges[key] = {"n": len(values), "min_s": min(values) if values else None,
                       "max_s": max(values) if values else None,
                       "mean_s": sum(values) / len(values) if values else None}
    return {
        "canonical_completed": report.get("completed"), "stopped": report.get("stopped"),
        "failure": report.get("failure"), "wall_s": wall, "transitions": report.get("transitions"),
        "updates_in_this_run": len(updates), "completed_episodes_in_committed_updates": sum(len(u.get("completed_episodes", [])) for u in updates),
        "timers": timers,
        "committed_update_duration_ranges": ranges,
        "timer_wall_fractions": {k: v / wall for k, v in timers.items() if isinstance(v, (int, float)) and isinstance(wall, (int, float)) and wall > 0},
        "timer_scope": "startup/reset/step are parent wall-clock operations, not sums of worker CPU time. reset includes initial and episode physical preparation. collection overlaps step and episode reset; never sum collection with those. update_s is PPO optimization only. Report wall_s need not include final close/audit; resource stopped status is core runner state before final persistent audit.",
        "cleanup_errors": report.get("cleanup_errors"), "pool_close_diagnostics": close,
        "all_reported_children_closed": bool(close) and all(d.get("final_alive") is False for d in close),
        "worker_failures": report.get("worker_failures"), "core_status": {k: status.get(k) for k in ("phase", "stopped", "elapsed_s", "update_index", "ticks")},
        "integrity_fields": {k: report.get(k) for k in ("changed_inputs", "missing_import_pins", "original_source_parity_errors", "missing_worker_audits", "worker_audit_read_errors", "guard_violations", "physical_flags_errors")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=PHASE / "run_v1")
    parser.add_argument("--old-run", type=Path, default=OLD)
    parser.add_argument("--out", type=Path, default=PHASE)
    args = parser.parse_args()
    run, old, out = args.run.resolve(), args.old_run.resolve(), args.out.resolve()
    if not out.is_dir():
        raise ValueError("Output directory must already exist")
    targets = [out / n for n in ("runtime_inputs_before.json", "runtime_analysis.json", "runtime_verification.json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Runtime analysis outputs already exist; use a new output directory")
    expected = [Path(__file__).resolve()]
    for directory in (old, run):
        expected.extend(directory / n for n in ("report.json", "resources.jsonl", "status.json", "settings.json"))
    expected.extend(run / n for n in ("core_report.json", "persistent_audit.json"))
    expected.extend(sorted(run.glob("worker_*/environment/persistent_lifecycle.json")))
    # Hash every input before parsing any report/resource content.
    pins = {str(p): sha(p) if p.is_file() else None for p in expected}
    write_new(targets[0], {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sha256": pins})
    errors = []

    def load(path, lines=False):
        try:
            if str(path) not in pins or pins[str(path)] is None:
                raise FileNotFoundError(str(path))
            text = path.read_text(encoding="utf-8")
            return [json.loads(line) for line in text.splitlines() if line.strip()] if lines else json.loads(text)
        except Exception as exc:
            errors.append({"path": str(path), "type": type(exc).__name__, "message": str(exc)})
            return [] if lines else {}

    status = load(run / "status.json")
    pid = status.get("parent_pid")
    process_cmd = Path("/proc") / str(pid) / "cmdline"
    if process_cmd.exists() and b"guitar_learning.train_" in process_cmd.read_bytes():
        raise RuntimeError("Training parent is still running; analysis is termination-only")
    report, core, audit = (load(run / n) for n in ("report.json", "core_report.json", "persistent_audit.json"))
    old_report, old_status = load(old / "report.json"), load(old / "status.json")
    new_resources = analyze_resources(load(run / "resources.jsonl", lines=True))
    old_resources = analyze_resources(load(old / "resources.jsonl", lines=True))
    lifecycle = []
    for path in sorted(run.glob("worker_*/environment/persistent_lifecycle.json")):
        value = load(path)
        calls = value.get("native_calls", {})
        lifecycle.append({"path": str(path), "native_calls": calls,
                          "closed": value.get("closed"), "episodes_started": value.get("episode_index", -1) + 1,
                          "forbidden_calls_total": value.get("forbidden_calls_total"),
                          "passed": value.get("closed") is True and calls == {"create_sim": 1, "create_env": 1, "load_asset": 2, "destroy_sim": 1} and value.get("forbidden_calls_total") == 0})
    new_fit = new_resources["fits"]["after_60s"]["worker_current_rss_GiB"]["slope_GiB_per_hour"]
    old_fit = old_resources["fits"]["after_60s"]["worker_current_rss_GiB"]["slope_GiB_per_hour"]
    canonical_core_sha = report.get("core_report", {}).get("sha256")
    core_sha_matches = canonical_core_sha is not None and canonical_core_sha == pins.get(str(run / "core_report.json"))
    audit_embedded = report.get("persistent_audit", {})
    lifecycle_passed = len(lifecycle) == 8 and all(w["passed"] for w in lifecycle)
    result = {
        "run": str(run), "old_run": str(old), "errors": errors,
        "new": {"resources": new_resources, "report": summarize_report(report, status)},
        "old": {"resources": old_resources, "report": summarize_report(old_report, old_status)},
        "lifecycle": {"workers": lifecycle, "worker_count": len(lifecycle), "passed": lifecycle_passed,
                      "total_episodes_started": sum(w["episodes_started"] for w in lifecycle),
                      "scope": "Includes final prepared/partial episode, not only completed training episodes. Initial scene is episode index 0."},
        "persistent_finalization": {"canonical_completed": report.get("completed"), "core_completed": core.get("completed"),
                                    "audit_completed": audit.get("completed"), "audit_errors": audit.get("errors"),
                                    "embedded_audit_completed": audit_embedded.get("completed"), "core_sha_matches": core_sha_matches},
        "comparison": {"new_minus_old_RSS_OLS_GiB_per_hour": new_fit - old_fit if new_fit is not None and old_fit is not None else None,
                       "historical_reference": "Old run was about one hour; worker current RSS previously summarized as 5.093→13.953 GiB (~9 GiB/hour). Exact OLS and endpoints above are recalculated from original complete samples.",
                       "limits": ["New run resumes policy update 25; old run began from an untrained policy.",
                                  "Different duration, contemporaneous machine load, memory sharing, allocator history and policy trajectories prevent a controlled causal speed/memory benchmark.",
                                  "Last-ten-minute and latter-half windows overlap. OLS slopes and R² are descriptive; even low/negative slope does not prove absence of longer-term leaks.",
                                  "Only samples with all same eight worker PIDs and both current RSS/PSS are summed. Parent current and peak, and worker per-process peak sums, are reported separately."]},
    }
    write_new(targets[1], result)
    changed = [str(p) for p in expected if (sha(p) if p.is_file() else None) != pins[str(p)]]
    missing = [p for p, digest in pins.items() if digest is None]
    verification = {
        "inputs_unchanged": not changed, "changed_inputs": changed, "missing_inputs": missing, "read_errors": errors,
        "analysis_written": True, "analysis_sha256": sha(targets[1]),
        "training_completed_and_persistent_audit_passed": report.get("completed") is True and audit.get("completed") is True and audit_embedded.get("completed") is True and core_sha_matches and lifecycle_passed,
        "analysis_integrity_passed": not changed and not missing and not errors,
        "scope": "Analysis integrity and training completion are independent. Failure/interruption is retained in analysis; no assertion converts it to success.",
    }
    write_new(targets[2], verification)
    print(json.dumps({"out": str(out), "verification": verification}, ensure_ascii=False))


if __name__ == "__main__":
    main()
