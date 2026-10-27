"""Paired whole-song evaluation, or comparison of existing fixed-case reports."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def compare_reports(reference, candidate):
    protocol = reference.get("case_protocol")
    if not protocol or protocol != candidate.get("case_protocol"):
        raise ValueError("paired comparison requires identical case_protocol")
    for key in ("evaluation_scope", "tempo_lambda", "stage", "goal_sha256",
                "evaluation_contract_sha256", "timing_tolerance_ms"):
        if reference.get(key) != candidate.get(key):
            raise ValueError("evaluation context mismatch: " + key)
    def indexed(report):
        rows = report.get("cases", [])
        result = {int(row["case"]["case_id"]): row for row in rows}
        if not result or len(result) != len(rows):
            raise ValueError("case IDs must be nonempty and unique")
        if len(result) != int(protocol["episodes"]):
            raise ValueError("case count does not match protocol")
        return result
    left, right = indexed(reference), indexed(candidate)
    if left.keys() != right.keys():
        raise ValueError("paired reports have different case IDs")
    case_changes = []
    for case_id in sorted(left):
        a, b = left[case_id], right[case_id]
        initial_a = {k: v for k, v in a["case"].items()
                     if k not in ("event_reconciliation", "event_diagnostics")}
        initial_b = {k: v for k, v in b["case"].items()
                     if k not in ("event_reconciliation", "event_diagnostics")}
        if initial_a != initial_b:
            raise ValueError("initial conditions differ for case " + str(case_id))
        case_changes.append({
            "case_id": case_id,
            "f1_delta": float(b["strike_episode_f1"]) - float(a["strike_episode_f1"]),
            "reference_f1": float(a["strike_episode_f1"]),
            "candidate_f1": float(b["strike_episode_f1"]),
        })
    keys = ("strike_f1", "release_recall", "false_positive_rate", "timing_p95_ms")
    return {
        "case_protocol": protocol,
        "context_verification": (
            "goal_and_runtime_verified" if all(reference.get(key) is not None
                for key in ("goal_sha256", "evaluation_contract_sha256", "timing_tolerance_ms"))
            else "legacy_context_incomplete_goal_or_runtime_identity_unverifiable"),
        "metric_deltas_candidate_minus_reference": {
            key: float(candidate["metrics"][key]) - float(reference["metrics"][key])
            for key in keys if key in reference["metrics"] and key in candidate["metrics"]},
        "case_summary_reference": reference.get("case_summary"),
        "case_summary_candidate": candidate.get("case_summary"),
        "regressed_cases": sum(row["f1_delta"] < 0 for row in case_changes),
        "improved_cases": sum(row["f1_delta"] > 0 for row in case_changes),
        "case_changes": case_changes,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-report", type=Path)
    parser.add_argument("--candidate-report", type=Path)
    parser.add_argument("--reference-checkpoint", type=Path)
    parser.add_argument("--candidate-checkpoint", type=Path)
    parser.add_argument("--song")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1729, 2718, 3141])
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--num-envs", type=int, default=64)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--policy-transfer-evaluation", action="store_true",
                        help="Explicit actor/normalization-only transfer into current environment; not strict old-runtime replay")
    parser.add_argument("--out", type=Path, required=True,
                        help="New output directory, outside original run directories")
    return parser


def evaluation_command(args, checkpoint, seed, output):
    command = [sys.executable, "-m", "tab2body.train_strike", "--song", args.song,
               "--out", str(output), "--eval-seed", str(seed), "--seed", str(seed),
               "--eval-episodes", str(args.episodes), "--num-envs", str(args.num_envs),
               "--device", args.device, "--no-auto-video", "--no-auto-artifacts"]
    if args.policy_transfer_evaluation:
        command += ["--eval-policy-transfer", "--initialize-from", str(checkpoint)]
    else:
        command += ["--eval", "--checkpoint", str(checkpoint), "--eval-metrics-only",
                    "--curriculum-stage", "S3_SONG_INTEGRATION"]
    return command


def main(argv=None):
    args = build_parser().parse_args(argv)
    reports = bool(args.reference_report or args.candidate_report)
    checkpoints = bool(args.reference_checkpoint or args.candidate_checkpoint)
    if reports == checkpoints:
        raise ValueError("choose a pair of reports OR checkpoints")
    inputs = ((args.reference_report, args.candidate_report) if reports else
              (args.reference_checkpoint, args.candidate_checkpoint))
    if any(path is None or not path.is_file() for path in inputs):
        raise ValueError("both input files must exist")
    if not reports and (not args.song or args.episodes < 1 or args.num_envs < 1):
        raise ValueError("checkpoint evaluation requires song and positive episode/env counts")
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        raise ValueError("seeds must be unique and nonnegative")
    output = args.out.resolve()
    for path in inputs:
        source_root = path.resolve().parent
        while source_root.name in ("checkpoints", "evaluations"):
            source_root = source_root.parent
        if output == source_root or source_root in output.parents:
            raise ValueError("output must be outside the original run directory")
    output.mkdir(parents=True, exist_ok=False)
    results = []
    if reports:
        pairs = [inputs]
    else:
        pairs = []
        for seed in args.seeds:
            pair = []
            for label, checkpoint in zip(("reference", "candidate"), inputs):
                destination = output / (label + "_seed_" + str(seed))
                command = evaluation_command(args, checkpoint.resolve(), seed, destination)
                with (output / (label + "_seed_" + str(seed) + ".log")).open("w") as log:
                    subprocess.run(command, cwd=Path(__file__).resolve().parents[2],
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
                pair.append(destination / "evaluations" / (checkpoint.stem + ".eval.json"))
            pairs.append(pair)
    for left, right in pairs:
        result = compare_reports(json.loads(left.read_text()), json.loads(right.read_text()))
        result.update(reference_report=str(left.resolve()), candidate_report=str(right.resolve()))
        results.append(result)
    target = output / "comparison.json"
    target.write_text(json.dumps({"schema": "strike.paired_comparison.v1", "comparisons": results,
                                 "interpretation": "Positive delta means candidate minus reference; lower timing/error is better. Multi-seed results are separate, not pooled."}, indent=2) + "\n")
    print(target)
    return target


if __name__ == "__main__":
    main()
