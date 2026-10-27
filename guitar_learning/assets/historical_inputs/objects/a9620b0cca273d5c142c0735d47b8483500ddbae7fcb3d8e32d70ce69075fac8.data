import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tab2body.tools.compare_strike_evaluations import compare_reports, evaluation_command, main
from tab2body.train_strike import build_parser

report = {
    "case_protocol": {"seed": 1729, "episodes": 2, "num_envs": 2},
    "evaluation_scope": "full_song_original_tempo", "stage": "S3_SONG_INTEGRATION",
    "tempo_lambda": 1.0,
    "cases": [{"case": {"case_id": i, "target_lane_y": i}, "strike_episode_f1": 1.0}
              for i in range(2)],
    "metrics": {"strike_f1": 1.0}, "case_summary": {"clean_full_song_rate": 1.0}}
candidate = copy.deepcopy(report)
candidate["cases"][0]["strike_episode_f1"] = 0.8
candidate["cases"][0]["case"]["event_reconciliation"] = {"matches": False}
candidate["metrics"]["strike_f1"] = 0.9
comparison = compare_reports(report, candidate)
assert comparison["regressed_cases"] == 1
assert comparison["improved_cases"] == 0
assert comparison["context_verification"].startswith("legacy_context_incomplete")
complete = copy.deepcopy(report)
complete.update(goal_sha256="goal", evaluation_contract_sha256="runtime", timing_tolerance_ms=50)
assert compare_reports(complete, complete)["context_verification"] == "goal_and_runtime_verified"
different = copy.deepcopy(complete)
different["goal_sha256"] = "different_song"
try:
    compare_reports(complete, different)
except ValueError:
    pass
else:
    raise AssertionError("different songs paired")
for mutate in (
    lambda r: r["case_protocol"].update(seed=1),
    lambda r: r["cases"][0]["case"].update(target_lane_y=100),
    lambda r: r["cases"].pop(),
    lambda r: r.update(tempo_lambda=0.0),
):
    invalid = copy.deepcopy(report)
    mutate(invalid)
    try:
        compare_reports(report, invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("incompatible pairing accepted")
args = SimpleNamespace(song="song", episodes=64, num_envs=64, device="cuda:0",
                       policy_transfer_evaluation=True)
command = evaluation_command(args, Path("/tmp/source.pt"), 2718, Path("/tmp/new_run"))
assert "--eval-policy-transfer" in command and "--initialize-from" in command
assert "--checkpoint" not in command
parsed = build_parser().parse_args(command[3:])
assert parsed.eval_seed == 2718 and parsed.maintenance_lr_scale == 1.0
with tempfile.TemporaryDirectory() as folder:
    directory = Path(folder)
    inputs = directory / "inputs"
    inputs.mkdir()
    left, right = inputs / "left.json", inputs / "right.json"
    left.write_text(json.dumps(report))
    right.write_text(json.dumps(candidate))
    result = main(["--reference-report", str(left), "--candidate-report", str(right),
                   "--out", str(directory / "comparison")])
    assert json.loads(result.read_text())["comparisons"][0]["regressed_cases"] == 1
    assert json.loads(left.read_text()) == report
    snapshots = directory / "run" / "evaluations" / "checkpoints"
    snapshots.mkdir(parents=True)
    saved = snapshots / "strike_009500_hash.pt"
    saved.write_bytes(b"checkpoint")
    try:
        main(["--reference-checkpoint", str(saved), "--candidate-checkpoint", str(saved),
              "--song", "song", "--out", str(directory / "run" / "new")])
    except ValueError as error:
        assert "outside" in str(error)
    else:
        raise AssertionError("immutable snapshot source run not protected")
subprocess.run([sys.executable, "-m", "tab2body.tools.compare_strike_evaluations", "--help"],
               check=True, stdout=subprocess.PIPE)
print("PASS strike paired comparison")
