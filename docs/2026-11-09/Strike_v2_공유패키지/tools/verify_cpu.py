"""Run the packaged, asset-independent Strike checks in fresh CPU processes.

The historical checks are assert/main scripts, not unittest discovery tests.
Counts below refer to completed scripts and explicitly selected functions, not
to individual assertions. Native simulation and checkpoint compatibility are
outside this check's scope.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "tab2body" / "tests"
SCRIPTS = (
    "artifact_contract", "comparison", "detector", "direction_planner",
    "evaluation_gates", "event_logic", "failure_mining", "goal_timing",
    "maintenance", "microtiming", "paired_rollout", "periodic_checkpoint_video",
    "plan_validation",
    "quality_reporting", "recovery_context",
    "repeat_evaluation", "reward_alignment_monitor", "runner_lazy_import",
    "stage_curriculum", "timing_boundary", "transition_contract",
    "transition_sampling_audit",
    "v2_contract", "visualized_rollout",
)
PARTIAL_SCRIPT = "goal_quality_audit"
PARTIAL_FUNCTIONS = (
    "test_clean_bundle_passes_without_gpu_imports",
    "test_noncontiguous_inferred_strum_is_ambiguous_without_provenance",
    "test_actual_edge_gap_and_reversal_make_dense_transition_infeasible",
    "test_reference_onset_delta_is_reported_and_classified",
    "test_proposed_reviewed_override_is_valid_but_remains_ambiguous",
    "test_all_bundle_summary_and_strict_cli_exit",
)
EXCLUDED = {
    "test_strike_preflight_layout.py": (
        "Before its resource-preflight mock is reached, train_strike.main "
        "requires the omitted default song strike_plan.json and "
        "strike/02_physical_control/pick-grip-reference.json, then validates "
        "the song goal. The initial CPU attempt confirmed FileNotFoundError."),
    "test_strike_training_runtime.py": (
        "Requires omitted data/song_bundles/{00_SS1-68-E_comp,"
        "02_Jazz1-200-B_solo}/training/strike_plan.json."),
    "test_strike_reward_staging.py": (
        "Requires omitted strike/02_physical_control/pick-grip-reference.json."),
    "test_strike_goal_quality_audit.py::"
    "test_current_promoted_song_is_physically_feasible_read_only": (
        "Requires the omitted data/song_bundles/00_SS1-68-E_comp bundle, "
        "including its source/plan/reviewed-override inputs."),
}
COMPLETED = "STRIKE_CPU_CHECK_COMPLETED"
CHILD = """
import runpy
import sys
assert __debug__, 'assert checks must not be disabled'
name = '__main__' if len(sys.argv) == 2 else 'strike_cpu_subset'
scope = runpy.run_path(sys.argv[1], run_name=name)
for function in sys.argv[2:]:
    scope[function]()
print('STRIKE_CPU_CHECK_COMPLETED')
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0,
                        help="Maximum seconds per child process (default: 120).")
    args = parser.parse_args()
    if not 0 < args.timeout < float("inf"):
        parser.error("--timeout must be finite and positive")

    jobs = [("test_strike_" + name + ".py", ()) for name in SCRIPTS]
    jobs.append(("test_strike_" + PARTIAL_SCRIPT + ".py", PARTIAL_FUNCTIONS))
    expected = {name for name, _ in jobs} | {
        name for name in EXCLUDED if "::" not in name}
    actual = {path.name for path in TEST_ROOT.glob("test_strike_*.py")}
    if actual != expected or not jobs:
        parser.error("test inventory differs from the reviewed whitelist: "
                     + repr(sorted(actual ^ expected)))

    output = ROOT / "verification"
    logs = output / "cpu_logs"
    logs.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.pop("PYTHONOPTIMIZE", None)
    environment.update({
        "CUDA_VISIBLE_DEVICES": "", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    })
    results = []
    with tempfile.TemporaryDirectory(prefix="strike_cpu_mpl_") as cache:
        environment["MPLCONFIGDIR"] = cache
        for name, functions in jobs:
            path = TEST_ROOT / name
            tree = ast.parse(path.read_text(encoding="utf-8"))
            if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
                parser.error(name + " contains no assert checks")
            started = time.monotonic()
            try:
                process = subprocess.run(
                    [sys.executable, "-B", "-c", CHILD, str(path), *functions],
                    cwd=ROOT, env=environment, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=args.timeout, check=False)
                text = process.stdout
                returncode = process.returncode
                status = ("passed" if returncode == 0
                          and COMPLETED in text.splitlines() else "failed")
            except subprocess.TimeoutExpired as exc:
                text = exc.stdout or ""
                if isinstance(text, bytes):
                    text = text.decode("utf-8", errors="replace")
                returncode, status = None, "timeout"
            log = logs / (path.stem + ".log")
            log.write_text(text, encoding="utf-8")
            results.append({
                "script": str(path.relative_to(ROOT)), "status": status,
                "mode": "selected_functions" if functions else "full_script",
                "selected_functions": list(functions), "returncode": returncode,
                "seconds": round(time.monotonic() - started, 3),
                "log": str(log.relative_to(ROOT)),
            })
            print(status.upper() + " " + name, flush=True)

    versions = {}
    for package in ("torch", "numpy", "Pillow", "matplotlib"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    failed = sum(result["status"] != "passed" for result in results)
    report = {
        "schema": "strike_v2_share.cpu_verification.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0], "dependency_versions": versions,
        "scope": "CPU synthetic/fixture checks; no native simulation, GPU, "
                 "training, or original-checkpoint compatibility validation.",
        "cuda_visible_devices": "", "threads": 1,
        "total_processes": len(results), "passed_processes": len(results) - failed,
        "failed_processes": failed, "full_scripts": len(SCRIPTS),
        "selected_functions": len(PARTIAL_FUNCTIONS),
        "excluded_reason": EXCLUDED, "results": results,
    }
    report_path = output / "cpu_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("{} / {} CPU processes passed; report: {}".format(
        len(results) - failed, len(results), report_path.relative_to(ROOT)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
