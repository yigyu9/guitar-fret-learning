"""CPU-only source evidence and named target/history contract checks."""
import ast
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import torch

from tab2body.full.postprocessing import (
    _mjcf_control_limits, _apply_fret_hard_limit_profile,
)
from tab2body.full.source_policies import inspect_source_checkpoint_metadata
from tab2body.learning.checkpoint_contract import validate_contract_document
from .playing_target_bridge import PlayingTargetBridge

R = Path(__file__).resolve().parents[1]
A = R / "stability_adapter_2"
D = R / "docs/2026-10-12/stability_adapter_2"
P = D / "results/playing_target_bridge_v1"
F = R / "fret/training/runs/20261001_2232_02_Jazz1-200-B_solo_synergy"
S = R / "strike/training/runs/20260920_Jazz1_sync_baseline"
CANDIDATES = {
    "fret47000": R / "fret/training/runs/20260929_1405_02_Jazz1-200-B_solo/checkpoints/fret_047000.pt",
    "fret47500": F / "checkpoints/fret_047500.pt",
    "strike10000": S / "checkpoints/strike_010000.pt",
    "strike10708": S / "checkpoints/strike_010708.pt",
}
EVALUATIONS = {
    "fret47000": F / "videos/condition_only_047000_mean_seed42.events.json",
    "fret47500": F / "videos/fret_047500_rollout.events.json",
    "strike10000": S / "evaluations/strike_010000.full_song.eval.json",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def base_action_function():
    tree = ast.parse((R / "tab2body/env/base.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and any(isinstance(f, ast.FunctionDef) and f.name == "apply_actions"
                       for f in n.body))
    fn = next(f for f in cls.body if isinstance(f, ast.FunctionDef)
              and f.name == "apply_actions")
    namespace = {"torch": torch}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(R / "tab2body/env/base.py"), "exec"), namespace)
    return namespace["apply_actions"]


def main():
    assert not (P / "contract.json").exists()
    initial_path = D / "results/body9_strap_minus2mm_v1/native/initial_values.json"
    profile = R / "tab2body/assets/fret_human_joint_profile.json"
    mjcf = R / "tab2body/assets/smpl_mpl_hands_body.xml"
    helpers = ["tab2body/full/postprocessing.py", "tab2body/full/source_policies.py",
               "tab2body/learning/checkpoint_contract.py", "tab2body/env/base.py",
               "tab2body/env/rewards/fret.py", "tab2body/env/rewards/strike.py",
               "tab2body/fret_v2_contract.py", "tab2body/strike_v2_contract.py",
               "tab2body/learning/fret_v2_model.py", "tab2body/learning/strike_v2_model.py",
               "tab2body/learning/models.py", "tab2body/env/tasks/task_fret.py",
               "tab2body/env/tasks/task_strike.py"]
    inputs = [Path(__file__), A / "playing_target_bridge.py", A / "PLAYING_TARGET_BRIDGE_PLAN.md",
              initial_path, profile, mjcf, S / "evaluations/best_full_song.json",
              S / "logs/interrupted_010708.json", S / "run_manifest.json",
              R / "docs/archive/dated/2026-08-24/FRET_EXPERIMENT_HISTORY.md"]
    inputs += list(CANDIDATES.values()) + list(EVALUATIONS.values()) + [R / n for n in helpers]
    before = {str(p.resolve()): sha(p) for p in inputs}
    initial = read(initial_path)
    names = initial["human_joint_names"]
    main_names = initial["main_control_joint_names"]
    hold = torch.tensor(initial["preserved_absolute_targets_rad"], dtype=torch.float32)
    native_lo = torch.tensor(initial["PD_properties"]["lower"], dtype=torch.float32)
    native_hi = torch.tensor(initial["PD_properties"]["upper"], dtype=torch.float32)
    rows = []
    sources = {}
    for label, path in CANDIDATES.items():
        task = "fret" if label.startswith("fret") else "strike"
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        document = validate_contract_document(checkpoint["checkpoint_contract"])
        qualification, execution = inspect_source_checkpoint_metadata(task, checkpoint, document)
        payload = document["payload"]
        config = payload["control"]
        _, lo, hi = _mjcf_control_limits(mjcf, config["controlled_dof_names"])
        if task == "fret":
            assert payload["config"]["reward_safety"]["human_hard_limits_enabled"]
            assert sha(profile) == payload["config"]["reward_safety"]["human_hard_limit_profile_sha256"]
            _, lo, hi = _apply_fret_hard_limit_profile(profile, config["controlled_dof_names"], lo, hi)
        fingerprint = payload["fingerprints"]["asset"]["manifest"]
        assert next(v["sha256"] for v in fingerprint if v["path"] == "assets/smpl_mpl_hands_body.xml") == sha(mjcf)
        evidence = None
        if label in EVALUATIONS:
            e = read(EVALUATIONS[label])
            if task == "fret":
                assert Path(e["checkpoint"]) == path and e["checkpoint_contract_sha256"] == document["sha256"]
                evidence = dict(path=str(EVALUATIONS[label]), checkpoint_path_and_contract_match=True,
                                checkpoint_file_sha_at_evaluation_available=False, metrics=e["episode_metrics"],
                                event34=e["events"][34], implementation_changes=e["implementation_files_changed_since_checkpoint"],
                                scope=e["evaluation_scope"], seed=e["evaluation_seed"],
                                independent_single_event_evaluation=False)
            else:
                assert e["checkpoint_sha256"] == sha(path)
                evidence = dict(path=str(EVALUATIONS[label]), checkpoint_file_sha_matches=True,
                                metrics=e["metrics"], episodes=e["episodes"], scope=e["evaluation_scope"],
                                wrong_crossing_termination_suppressed=e["wrong_crossing_termination_suppressed"],
                                quality_eligibility=e["quality_eligibility"])
        rows.append(dict(label=label, path=str(path), sha256=sha(path), contract_sha256=document["sha256"],
                         training_stage=checkpoint["training_context"]["curriculum_stage"],
                         strict_G0_qualification=qualification.to_document(), execution_context=execution,
                         evaluation=evidence, selected_for_free_guitar_playing=False))
        if label in ("fret47000", "strike10000"):
            sources[task] = dict(names=config["controlled_dof_names"], lower=lo.float(), upper=hi.float(),
                                 scale=config["action_scale"], alpha=config["action_alpha"])
        del checkpoint
    selected = read(S / "evaluations/best_full_song.json")
    assert selected["checkpoint_sha256"] == sha(CANDIDATES["strike10000"])
    assert sha(CANDIDATES["fret47000"]) == "681e8b6f282f6ac8e02f4959aa225cfa0520deeb6bf8a5b530e8a34663ac99b3"
    bridge = PlayingTargetBridge(names, main_names, hold, native_lo, native_hi, sources)
    def profile_mismatches(values):
        violations = []
        for task, c in bridge.sources.items():
            for n, j in zip(c["names"], c["idx"]):
                gap = max(float(bridge.lower[j] - values[j]), float(values[j] - bridge.upper[j]), 0.)
                if gap > 0:
                    violations.append(dict(task=task, name=n, current_target_rad=float(values[j]),
                                           effective_lower_rad=float(bridge.lower[j]), effective_upper_rad=float(bridge.upper[j]),
                                           required_min_target_change_rad=gap))
        return violations
    violations = profile_mismatches(hold)
    initial_violations = profile_mismatches(torch.tensor(initial["initial_PD_target_rad"], dtype=torch.float32))
    checks = {}
    def check(k, v):
        assert v, k
        checks[k] = True
    check("actual_hold_has_six_fret_profile_mismatches", len(violations) == 6 and all(v["task"] == "fret" for v in violations))
    rng = torch.Generator().manual_seed(42)
    batch = 17
    previous = hold.expand(batch, -1).clone()
    for c in bridge.sources.values():
        previous[:, c["idx"]] = c["mid"]
    reference = {}
    for task, c in bridge.sources.items():
        reference[task] = SimpleNamespace(num_envs=batch, n_dof=81, init_pose=hold,
            prev_action=bridge.source_history(previous)[task].clone(), pd_target=previous.clone(),
            applied_tau=torch.zeros(batch, 81), _nonfinite_action_state=torch.zeros(batch, dtype=torch.bool),
            _clear_step_nonfinite_flags=lambda: None, action_alpha=bridge.alpha, action_scale=c["scale"],
            ctrl_mid=c["mid"], ctrl_half=c["half"], ctrl_lo=sources[task]["lower"],
            ctrl_hi=sources[task]["upper"], ctrl_idx=c["idx"])
    original_apply = base_action_function()
    max_error = 0.
    for _ in range(80):
        actions = {task: torch.rand(batch, 30, generator=rng) * 1.6 - .8 for task in sources}
        saved_previous = previous.clone()
        final, histories, clipped = bridge.compose(actions, torch.zeros(batch, 66), previous, torch.zeros(66))
        for task, c in bridge.sources.items():
            original_apply(reference[task], actions[task])
            error = float((final[:, c["idx"]] - reference[task].pd_target[:, c["idx"]]).abs().max())
            max_error = max(max_error, error)
        assert torch.equal(previous, saved_previous)
        previous = final
    check("zero_residual_matches_original_Base_AST_80steps_batch17", max_error < 2e-6)
    check("held15_exact_and_source60_Thorax6_partition", len(bridge.held) == 15 and torch.equal(final[:, bridge.held], hold[bridge.held].expand(batch, -1)))
    reverse = list(range(80, -1, -1))
    permuted = PlayingTargetBridge([names[j] for j in reverse], main_names, hold[reverse], native_lo[reverse], native_hi[reverse], sources)
    perm_final, _, _ = permuted.compose(actions, torch.zeros(batch, 66), previous[:, reverse], torch.zeros(66))
    same_final, _, _ = bridge.compose(actions, torch.zeros(batch, 66), previous, torch.zeros(66))
    check("native_name_permutation_invariant", torch.equal(perm_final[:, reverse], same_final))
    reverse_source = list(range(29, -1, -1))
    reordered = copy.deepcopy(sources)
    for c in reordered.values():
        c["names"] = [c["names"][j] for j in reverse_source]
        c["lower"] = c["lower"][reverse_source]
        c["upper"] = c["upper"][reverse_source]
    source_order_bridge = PlayingTargetBridge(names, main_names, hold, native_lo, native_hi, reordered)
    source_order_final, _, _ = source_order_bridge.compose(
        {t: a[:, reverse_source] for t, a in actions.items()},
        torch.zeros(batch, 66), previous, torch.zeros(66))
    check("source_name_order_with_matching_actions_invariant", torch.equal(source_order_final, same_final))
    mid_previous = hold[None].clone()
    for c in bridge.sources.values():
        mid_previous[:, c["idx"]] = c["mid"]
    zeros = {t: torch.zeros(1, 30) for t in sources}
    delta = torch.zeros(1, 66, requires_grad=True)
    outputs, _, _ = bridge.compose(zeros, delta, mid_previous, torch.ones(66))
    outputs[:, bridge.main].sum().backward()
    check("all66_residual_gradients_one_EMA_no_held_authority", torch.allclose(delta.grad, torch.full_like(delta, 1 - bridge.alpha)))
    saturated, histories, flags = bridge.compose(zeros, torch.full((1, 66), 100.), mid_previous, torch.full((66,), 100.))
    check("saturation_within_intersection_and_reported", bool(flags[:, bridge.main].any()) and bool((saturated >= bridge.lower).all()) and bool((saturated <= bridge.upper).all()))
    history_error = 0.
    for task, c in bridge.sources.items():
        decoded = c["mid"] + c["scale"] * histories[task] * c["half"]
        history_error = max(history_error, float((decoded - saturated[:, c["idx"]]).abs().max()))
        assert bool((histories[task].abs() <= 1 + 1e-6).all())
    check("history_encodes_final_clipped_float32_target", history_error < 2e-6)
    rejected = []
    def reject(label, call):
        try:
            call()
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(label + " was accepted")
    reject("actual_baseline_outside_source_profile", lambda: bridge.compose(zeros, torch.zeros(1, 66), hold[None], torch.zeros(66)))
    reject("residual_over_cap", lambda: bridge.compose(zeros, torch.ones(1, 66), mid_previous, torch.zeros(66)))
    reject("nonfinite_residual", lambda: bridge.compose(zeros, torch.full((1, 66), float("nan")), mid_previous, torch.ones(66)))
    reject("wrong_residual_width", lambda: bridge.compose(zeros, torch.zeros(1, 33), mid_previous, torch.ones(66)))
    reject("action_outside_normalized_range", lambda: bridge.compose(dict(zeros, fret=torch.full((1, 30), 1.1)), torch.zeros(1, 66), mid_previous, torch.zeros(66)))
    reject("changed_held_target", lambda: bridge.compose(zeros, torch.zeros(1, 66), mid_previous + torch.nn.functional.one_hot(torch.tensor(bridge.held[0]), 81).float()[None] * .001, torch.zeros(66)))
    reject("duplicate_native_names", lambda: PlayingTargetBridge([names[0]] * 81, main_names, hold, native_lo, native_hi, sources))
    bad = copy.deepcopy(sources); bad["strike"]["alpha"] = .25
    reject("different_source_EMA", lambda: PlayingTargetBridge(names, main_names, hold, native_lo, native_hi, bad))
    bad_names = copy.deepcopy(sources); bad_names["strike"]["names"] = sources["fret"]["names"]
    reject("overlapping_source_ownership", lambda: PlayingTargetBridge(names, main_names, hold, native_lo, native_hi, bad_names))
    check("nine_invalid_contracts_rejected_without_physics", len(rejected) == 9)
    after = {p: sha(p) for p in before}
    check("all_inputs_SHA_unchanged", before == after)
    result = dict(checks=checks, input_sha256_before=before, input_sha256_after=after,
                  sources=rows, bridge_source_labels=["fret47000", "strike10000"],
                  actual_baseline_profile_mismatches=violations, native_names=names, main_names=main_names,
                  actual_initial_q_profile_mismatches=initial_violations,
                  source_mapping={t: dict(names=c["names"], native_indices=c["idx"], mid_rad=c["mid"].tolist(), half_rad=c["half"].tolist(), scale=c["scale"]) for t, c in bridge.sources.items()},
                  alpha=bridge.alpha, held_native_indices=bridge.held,
                  torch_version=str(torch.__version__),
                  original_Base_AST_max_target_difference_rad=max_error, final_history_decode_max_error_rad=history_error,
                  rejected_cases=rejected, native_initializations=0, physics_steps=0, actor_inference_calls=0, training_updates=0,
                  scope="CPU target/history sub-contract and saved evaluation evidence; not full observation/postprocessing/qualified free-guitar playback; actual hold rejected, no native adoption")
    (P / "contract.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(checks=checks, mismatches=violations, original_AST_max_error_rad=max_error), indent=2))


if __name__ == "__main__":
    main()
