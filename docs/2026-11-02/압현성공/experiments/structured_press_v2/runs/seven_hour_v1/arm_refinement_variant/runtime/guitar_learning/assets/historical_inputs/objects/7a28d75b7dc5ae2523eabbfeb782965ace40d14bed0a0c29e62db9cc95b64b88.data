"""One connection probe with prepared-pose reset and2s hand settling; no22s replay."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import json
import traceback
from dataclasses import asdict
from guitar_learning.training.recording import digest, write, project_source_paths, bridge_dependency
from guitar_learning.core.dependency_inputs import parity_errors as source_parity_errors
from guitar_learning.native.paths import resolve_input_path, rebase_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import isaacgym
    import numpy as np
    from guitar_learning.tool.validation.fretting_environment import FrettingEnvironment
    from guitar_learning.core.environment_v4 import PREPARATION_SECONDS, PREPARATION_STEPS
    from guitar_learning.core.fretting_v1 import FretTarget, FretContract
    from guitar_learning.native.lower_body_release_v1.common import pin
    from guitar_learning.native.gym_trial_recording import GymTrialRecording
    # Load the actual control dependency chain before the initial source census.
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.native.front_facing_ready_v1.runtime_v15 import Scene
    from guitar_learning.native.front_facing_ready_v1.runtime_v12 import Controller
    from guitar_learning.native.native_contacts import body_names, read_contacts

    root = Path(__file__).resolve().parents[2]
    config, out = resolve_input_path(args.config), args.out.resolve()
    expected_config = root / 'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json'
    if config != resolve_input_path(expected_config):
        raise ValueError('Only the original035 baseline reset is supported in this probe')
    out.mkdir(parents=True, exist_ok=False)
    cfg = rebase_paths(json.loads(config.read_text()))
    target = FretTarget(1, 5, 'index')
    contract = FretContract(minimum_dwell_s=.05)
    sources = {Path(__file__).resolve(), config}
    sources.update((root / 'guitar_learning/native').rglob('*.py'))
    sources.update(p for p in (root / 'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    sources.update(prepared_reset_v1.prepared_input_paths())
    for value in cfg.values():
        if isinstance(value, str) and value.startswith('/') and Path(value).is_file():
            sources.add(Path(value).resolve())
    candidate = rebase_paths(json.loads(Path(cfg['candidate']).read_text()))
    sources.add(Path(candidate['support_candidate']).resolve())
    original_run = expected_config.parent.parent / 'native_baseline_v14'
    sources.update(original_run / name for name in ('attempt.json', 'support_wrapper.json'))
    pins = pin(config, extra=sources)
    expected = {}
    for name in ('attempt.json', 'support_wrapper.json'):
        manifest = json.loads((original_run / name).read_text())
        for filename, value in manifest['input_sha256'].items():
            canonical = str(Path(filename).resolve())
            if canonical in expected and expected[canonical] != value:
                raise RuntimeError('Conflicting original source SHA: ' + canonical)
            expected[canonical] = value
    original = {p for p in project_source_paths(list(sys.modules.items())) if not bridge_dependency(p)}
    original.update(p for p in pins if Path(p).suffix.lower() in ('.xml', '.obj', '.stl', '.ply', '.dae'))
    original.add(str(config))
    write(out / 'inputs_before.json', pins)
    if source_parity_errors(original, expected):
        raise RuntimeError('Original runtime/model source parity failed')
    write(out / 'attempt.json', dict(target=asdict(target), contract=asdict(contract),
          target_selection='Diagnostic target selected from existing prepared index2 contact; not a song-performance test',
          preparation_seconds=PREPARATION_SECONDS, preparation_mode='prepared_pose_then_short_hand_settle', active_seconds=1, action_half_range_rad=.002, normalized_action=0,
          scope='Post-fetch native contact candidate and hold measurement; no pressure/audio/PPO'))
    recorder = []
    def capture(scene, phase):
        if not recorder:
            initial = dict(native_state=scene.native(), joint_names=scene.names,
                           human_body_names=scene.human_bodies, guitar_body_names=scene.guitar_bodies,
                           native_PD_properties={key: scene.pd_properties[key].tolist() for key in scene.pd_properties.dtype.names},
                           control_K105=scene.control_kp, control_D105=scene.control_kd,
                           target105_rad=scene.target, loaded_assets=scene.loaded_assets,
                           chair_initial_placement=scene.chair_placement, collision_policy=scene.collision_policy,
                           actual_shape_properties=scene.shape_properties,
                           human_properties=scene.human_properties, guitar_properties=scene.guitar_properties,
                           position_indices=scene.position_indices, effort_indices=scene.effort_indices,
                           zero_range_indices=scene.zero_indices, camera_spec=scene.camera_spec,
                           human_root_fixed=scene.human_root_fixed, guitar_root_fixed=scene.guitar_root_fixed,
                           guitar_gravity_disabled=scene.guitar_gravity_disabled)
            write(out / 'initial_values.json', initial)
            recorder.append(GymTrialRecording(scene, out / 'media'))
            recorder[0].fps, recorder[0].interval = 5, 48
        if scene.steps % 48 == 0:
            recorder[0].capture()
    environment = FrettingEnvironment(config, out / 'environment', action_half_range_rad=.002,
                                     fret_target=target, fret_contract=contract,
                                     note_start_step=PREPARATION_STEPS, note_end_step=PREPARATION_STEPS + 240, sample_callback=capture)
    rows, failure, videos, encoding_errors = [], None, {}, []
    reset_description = None
    try:
        initial, metadata = environment.reset()
        reset_description = metadata['prepared_reset']
        write(out / 'prepared.json', dict(sample=initial, metadata=metadata))
        rows.append(initial)
        for _ in range(60):
            _, info = environment.step(np.zeros(39))
            rows.extend(info['physics_samples240'])
        write(out / 'final.json', dict(sample=rows[-1], forbidden_calls=environment.session.scene.forbidden_calls))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        environment.close()
        write(out / 'measurements240.json.gz', dict(rows=rows), compressed=True)
        if recorder:
            try:
                videos = recorder[0].encode()
            except BaseException as error:
                encoding_errors.append(str(error))
        changed = [p for p, h in pins.items() if digest(p) != h]
        imported = project_source_paths(list(sys.modules.items()))
        missing = sorted(imported - set(pins))
        parity_errors = source_parity_errors((p for p in imported if not bridge_dependency(p)), expected)
        completed = failure is None and len(rows) == 241 and not (changed or missing or parity_errors or encoding_errors)
        write(out / 'report.json', dict(completed=completed, failure=failure, encoding_errors=encoding_errors,
              recorded_samples=len(rows), preparation_seconds=PREPARATION_SECONDS, requested_physics_seconds=3, actual_physics_seconds=rows[-1]['native']['physics_step'] / 240. if rows else None, prepared_reset=reset_description, inputs_unchanged=not changed, changed_inputs=changed,
              actual_imported_sources=sorted(imported), missing_import_pins=missing,
              original_source_parity_errors=parity_errors, videos=videos, new_training_updates=0))
        if failure is None and not completed:
            raise RuntimeError('Native probe output/source checks failed; see preserved report')


if __name__ == '__main__':
    main()
