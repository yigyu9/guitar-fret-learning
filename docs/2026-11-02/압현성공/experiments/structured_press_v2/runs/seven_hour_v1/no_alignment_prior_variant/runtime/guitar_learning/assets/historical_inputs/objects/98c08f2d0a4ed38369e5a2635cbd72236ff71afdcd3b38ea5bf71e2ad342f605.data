"""Read two illustrative source contracts; no simulator or model inference."""
import argparse
import hashlib
import json
from pathlib import Path

import torch

from tab2body.learning.checkpoint_contract import validate_contract_document


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    "fret": "fret/training/runs/20261001_2232_02_Jazz1-200-B_solo_synergy/checkpoints/fret_047500.pt",
    "strike": "strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010708.pt",
}
INITIAL = ROOT / "docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/initial_values.json"
REFERENCES = (
    "tab2body/env/base.py", "tab2body/env/tasks/task_fret.py",
    "tab2body/env/tasks/task_strike.py", "tab2body/full/source_policies.py",
    "tab2body/full/action.py", "tab2body/full/postprocessing.py",
    "tab2body/fret_v2_contract.py", "tab2body/strike_v2_contract.py",
    "tab2body/learning/checkpoint_contract.py", "tab2body/learning/models.py",
    "tab2body/learning/fret_v2_model.py", "tab2body/learning/strike_v2_model.py",
    "stability_adapter_2/control.py", "full/03_implementation/STATUS.md",
)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    inputs = [Path(__file__).resolve(), INITIAL]
    inputs += [ROOT / name for name in REFERENCES]
    inputs += [ROOT / name for name in EXAMPLES.values()]
    before = {str(path): sha(path) for path in inputs}
    initial = json.loads(INITIAL.read_text())
    native_names = initial["human_joint_names"]
    main_names = initial["main_control_joint_names"]
    assert len(native_names) == 81 and len(main_names) == 66
    rows = []
    for task, relative in EXAMPLES.items():
        checkpoint = torch.load(ROOT / relative, map_location="cpu", weights_only=True)
        contract = validate_contract_document(checkpoint["checkpoint_contract"])
        payload = contract["payload"]
        assert payload["task"] == task
        names = payload["control"]["controlled_dof_names"]
        assert len(names) == len(set(names)) == 30
        assert set(names) <= set(main_names)
        observation_schema = payload.get("observation", {}).get("schema", payload["config"].get("strike", {}).get("observation_contract"))
        assert observation_schema == task + ".observation.v2"
        width = payload["model"]["num_obs"]
        assert width == {"fret": 420, "strike": 303}[task]
        buffers = {}
        for name in ("mean", "var", "count"):
            value = checkpoint["model"]["obs_rms." + name]
            assert torch.isfinite(value).all()
            assert tuple(value.shape) == (() if name == "count" else (width,))
            if name == "var":
                assert (value >= 0).all()
            buffers[name] = {"shape": list(value.shape), "min": value.min().item(),
                             "max": value.max().item()}
        config = payload["config"]
        rows.append({
            "task": task, "path": str(ROOT / relative),
            "checkpoint_sha256": before[str(ROOT / relative)],
            "contract_sha256": contract["sha256"], "schema": payload["schema"],
            "model": payload["model"], "control": payload["control"],
            "inputs": payload["inputs"], "timing": config.get("timing"),
            "observation_schema": observation_schema,
            "observation_manifest": payload.get("observation", {}).get("manifest",
                                               config.get("observation_manifest")),
            "training_stage": checkpoint["training_context"].get("curriculum_stage"),
            "iteration": checkpoint["iteration"], "normalization_buffers": buffers,
            "native_indices_by_source_order": [native_names.index(n) for n in names],
            "selected_for_playing": False,
        })
    source_names = [n for row in rows for n in row["control"]["controlled_dof_names"]]
    assert len(set(source_names)) == 60
    extra = [n for n in main_names if n not in source_names]
    assert len(extra) == 6 and all("Thorax" in n for n in extra)
    after = {str(path): sha(path) for path in inputs}
    assert before == after
    report = {"scope": "illustrative ABI inspection, not source qualification",
              "torch_version": str(torch.__version__), "native_initializations": 0,
              "physics_steps": 0, "training_updates": 0, "model_inference_calls": 0,
              "checks": {"contract_integrity": True, "dimensions_and_named_mapping": True,
                         "normalization_buffers_finite": True, "observation_schema_explicit": True, "input_SHA_unchanged": True},
              "input_sha256_before": before, "input_sha256_after": after,
              "examples": rows, "extra_main_control_names": extra}
    (args.out / "contract_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"checks": report["checks"], "extra": extra,
                      "stages": {r["task"]: r["training_stage"] for r in rows}}))


if __name__ == "__main__":
    main()
