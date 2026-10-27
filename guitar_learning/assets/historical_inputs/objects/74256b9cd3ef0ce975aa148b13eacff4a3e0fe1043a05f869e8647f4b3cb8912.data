"""CPU regressions for mixed episode success and quality diagnostics."""
import ast
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import torch
from tab2body.strike_metrics import pool_strike_raw_count_rates
from tab2body.tools.diagnose_strike_stall import (
    _metric_rows, _quality_maintenance_diagnostics, _repeated_evaluations,
)


def main():
    tree = ast.parse((ROOT / "tab2body/env/tasks/task_strike.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "StrikeTask")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_episode_metrics")
    dispatch = next(n for n in method.body if isinstance(n, ast.If)
                    and any(isinstance(child, ast.Name)
                            and child.id == "curriculum_success"
                            for child in ast.walk(n)))
    stages = ("A0_PICK_GRIP", "A1_TIP_READY", "A2_SINGLE_CROSSING",
              "A3_TIMED_SINGLE", "A4_STRUM_CONTEXT_RECOVERY",
              "S0_TWO_STRING_STRUM", "S1_STRUM_SPAN", "S2_TIMED_STRUM")
    ns = {name: name for name in stages}
    ns.update({
        "self": SimpleNamespace(curriculum_stage="S3_SONG_INTEGRATION",
                                curriculum_song_f1_gate=0.99),
        "common_crossing": torch.tensor([True, True, True, True, False]),
        "strum_events": torch.tensor([0., 2., 2., 0., 0.]),
        "strum_gate": torch.tensor([False, True, False, False, False]),
        "strum_microtiming_gate": torch.tensor([False, True, True, False, False]),
        "timed_gate": torch.tensor([True, True, True, False, True]),
        "f1": torch.ones(5),
    })
    exec(compile(ast.Module(body=[dispatch], type_ignores=[]),
                 "task_episode_success", "exec"), ns)
    assert ns["curriculum_success"].tolist() == [True, True, False, False, False]

    pooled = pool_strike_raw_count_rates({
        "strike_true_positive_count": 5., "strike_false_positive_count": 0.,
        "strike_false_negative_count": .5, "strike_episode_f1": .5,
        "strike_release_recall": .5,
    })
    assert abs(pooled["strike_episode_f1"] - 20. / 21.) < 1e-9
    assert pooled["strike_episode_f1_macro"] == .5
    assert abs(pooled["strike_release_recall"] - 10. / 11.) < 1e-9
    recovery = pool_strike_raw_count_rates({
        "strike_handoff_recovery_completed_count": 4.,
        "strike_handoff_recovery_event_count": 4.,
        "strike_handoff_recovery_completion_rate": .75,
        "strike_full_recovery_completed_count": 1.,
        "strike_full_recovery_event_count": 2.,
        "strike_full_recovery_completion_rate": .25,
    })
    assert recovery["strike_handoff_recovery_completion_rate"] == 1.
    assert recovery["strike_handoff_recovery_completion_rate_macro"] == .75
    assert recovery["strike_full_recovery_completion_rate"] == .5
    pool_strike_raw_count_rates(recovery)
    assert recovery["strike_handoff_recovery_completion_rate_macro"] == .75
    assert pool_strike_raw_count_rates({
        "strike_handoff_recovery_completed_count": 0.,
        "strike_handoff_recovery_event_count": 0.,
    })["strike_handoff_recovery_completion_rate"] == -1.

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / "metrics.jsonl"
        row = {"iteration": 1, "curriculum_stage": "S3_SONG_INTEGRATION"}
        path.write_text(json.dumps(row) + "\n{bad\n")
        try:
            list(_metric_rows(path))
        except ValueError as exc:
            assert ":2:" in str(exc)
        else:
            raise AssertionError("damaged evidence must not be silently omitted")
        path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
        try:
            list(_metric_rows(path))
        except ValueError as exc:
            assert "non-increasing" in str(exc)
        else:
            raise AssertionError("duplicate iterations must be reported")
        (root / "evaluations").mkdir()
        report = {"iteration": 10, "episodes": 64, "metrics": {
            "strike_f1": .97, "release_recall": .95,
            "end_to_end_recovery_completion_rate": .94, "timing_p95_ms": 4.0}}
        (root / "evaluations/strike_000010.full_song.eval.json").write_text(
            json.dumps(report))
        reports = _repeated_evaluations(root)
        assert reports[0]["f1"] == .97
        rows = [{"iteration": i, "curriculum_complete": True,
                 "curriculum_gate_evaluation_count": 5} for i in (1, 10)]
        result = _quality_maintenance_diagnostics(rows, reports)
        assert result["gate_stopped_after_mastery"]
        assert result["post_mastery_evaluations_below_f1_gate"] == 1
        assert not result["fixed_case_evaluation_available"]
        unfinished = _quality_maintenance_diagnostics(
            [{"iteration": 10, "curriculum_complete": False}], reports)
        assert unfinished["post_mastery_evaluation_count"] == 0
    print("PASS: optional strum success, pooled reporting and explicit diagnosis")


if __name__ == "__main__":
    main()
