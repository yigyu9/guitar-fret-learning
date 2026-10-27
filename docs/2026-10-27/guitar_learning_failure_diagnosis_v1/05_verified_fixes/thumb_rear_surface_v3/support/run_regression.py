"""Current production thumb helper, original 900-control probe, fixed guitar only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def job(out, video):
    return dict(out=str(out), args=[sys.executable, str(Path(__file__).resolve()),
        '--out', str(out)]+(['--video'] if video else []))


def owned(out, identity):
    return identity is not None and out.is_dir() and (out.stat().st_dev, out.stat().st_ino) == identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--dry-plan', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(str(out))
    if args.dry_plan:
        print(json.dumps(dict(jobs=[job(out, args.video)], GPU_executed=False), indent=2))
        return
    sealed = json.loads((HERE/'precommit.json').read_text())['source_pins']
    if any(not Path(p).is_file() or sha(p) != h for p, h in sealed.items()):
        raise ValueError('Production regression precommit source changed')
    import isaacgym  # Preserve the original native-before-Torch import order.
    import numpy as np
    from guitar_learning.gpu import scene as scene_module, thumb_support
    from guitar_learning.gpu.episode_diagnostics import DIAGNOSTIC_CONTRACT
    from guitar_learning.tool.validation import thumb_contact_probe as probe, hand_contact_probe
    original_scene = scene_module.GpuScene
    original_paths = hand_contact_probe.physics_source_paths
    created, identity, failure = [], None, None

    def fixed_scene(*values, **kwargs):
        kwargs['diagnostic_guitar_mode'] = 'fixed'
        scene = original_scene(*values, **kwargs)
        created.append(scene)
        return scene

    def source_paths(root):
        nonlocal identity
        # Called by the unchanged base only AFTER its exclusive output mkdir.
        stat = out.stat()
        identity = (stat.st_dev, stat.st_ino)
        if not owned(out, identity) or (out/'report.json').exists():
            raise RuntimeError('Unexpected base output ownership')
        return original_paths(root) | set(map(Path, sealed))

    scene_module.GpuScene = fixed_scene
    hand_contact_probe.physics_source_paths = source_paths
    previous_argv = sys.argv
    sys.argv = [str(Path(probe.__file__).resolve()), '--out', str(out), '--mode', 'contact',
        '--controls', '900']+(['--video'] if args.video else [])
    try:
        probe.main()
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        sys.argv = previous_argv
        scene_module.GpuScene = original_scene
        hand_contact_probe.physics_source_paths = original_paths
        if owned(out, identity):
            base_path = out/'report.json'
            base = json.loads(base_path.read_text()) if base_path.is_file() else {}
            inputs_path = out/'inputs_before.json'
            base_pins = json.loads(inputs_path.read_text()) if inputs_path.is_file() else {}
            changed = [p for p, h in {**base_pins, **sealed}.items()
                if not Path(p).is_file() or sha(p) != h]
            scene = created[0] if created else None
            diagnostics = scene.diagnostics if scene else {}
            capture = {}
            raw = out/'physics_env0000.npz'
            if raw.is_file():
                with np.load(raw, allow_pickle=False) as a:
                    ids = base['thumb_joint_indices']
                    target = a['target'][:, ids]
                    reference = target[0]
                    controls = target[3::4]
                    capture = dict(physical_endpoints=len(target), controls=len(controls),
                        finite=all(np.isfinite(a[k]).all() for k in a.files if a[k].dtype.kind not in 'US'),
                        clock_exact=bool(np.allclose(a['time_s'], np.arange(1, len(target)+1)/240., atol=1e-10, rtol=0)),
                        max_target_excursion_deg=float(np.rad2deg(np.abs(target-reference).max())),
                        max_control_change_deg=float(np.rad2deg(np.abs(np.diff(np.vstack((reference, controls)), axis=0)).max())))
                    if scene:
                        lower, upper = scene.lower[ids].cpu().numpy(), scene.upper[ids].cpu().numpy()
                        capture['native_target_limit_excess_rad'] = float(np.maximum(np.maximum(lower-target, target-upper), 0).max())
            checks = dict(base_completed=base.get('completed') is True,
                base_no_failure=base.get('failure') is None and not base.get('cleanup_errors'),
                source_pins_unchanged=bool(base_pins) and not changed and all(base_pins.get(p) == h for p, h in sealed.items()),
                scene_closed=diagnostics.get('closed') is True,
                fixed_readback=diagnostics.get('diagnostic_guitar_mode') == 'fixed'
                    and diagnostics.get('diagnostic_guitar_asset', {}).get('requested_fix_base_link') is True,
                gravity_on=diagnostics.get('diagnostic_guitar_asset', {}).get('requested_disable_gravity') is False,
                physical_clock=capture.get('physical_endpoints') == 3600 and capture.get('controls') == 900
                    and capture.get('clock_exact') is True and diagnostics.get('physics_steps') == 3600,
                finite=capture.get('finite') is True,
                request_bounds=capture.get('max_target_excursion_deg', 99) <= 15.0001
                    and capture.get('max_control_change_deg', 99) <= .5001
                    and capture.get('native_target_limit_excess_rad', 99) < 2e-6,
                codec=base.get('codec_max_error_rad', 99) < 2e-6,
                original_contact_protocol=base.get('all_contact_protocol_conditions_passed') is True,
                original_fixed_witness_release=base.get('fixed_witness_release_2mm_passed') is True,
                native_gpu=diagnostics.get('physx_use_gpu') is True
                    and diagnostics.get('use_gpu_pipeline') is True and diagnostics.get('environment_count') == 1,
                video=not args.video or (base.get('frames') == 450 and base.get('video_encoder_exit') == 0),
                current_contract=thumb_support.THUMB_SUPPORT_CONTRACT['schema'] == 'guitar_learning.gpu_thumb_rear_support.v3'
                    and DIAGNOSTIC_CONTRACT['schema'] == 'guitar_learning.gpu_left_episode_diagnostics.v6')
            result = dict(schema='diagnostic.thumb_rear_surface_production_regression.v1',
                completed=failure is None and all(checks.values()), failure=failure, audits=checks,
                protocol_passed=base.get('protocol_passed'),
                all_contact_protocol_conditions_passed=base.get('all_contact_protocol_conditions_passed'),
                scope='One fixed-guitar035 native environment; unchanged production helper and original 15s thumb-only finite probe. Not learned policy performance or contact-pair pressure.',
                base_scope_notice='Original report.json is untouched and retains inherited free-guitar wording; actual fixed mode/readback is recorded here.',
                source_pins=sealed, changed_inputs=changed, helper_contract=thumb_support.THUMB_SUPPORT_CONTRACT,
                diagnostic_contract=DIAGNOSTIC_CONTRACT, raw_audit=capture, scene=diagnostics,
                base_report_sha256=sha(base_path) if base_path.is_file() else None)
            with (out/'production_regression.json').open('x') as stream:
                stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
            if failure is None and not result['completed']:
                raise RuntimeError('Production regression audit failed')


if __name__ == '__main__':
    main()
