"""Fresh right-hand PPO through the unchanged legacy GPU runner."""
from pathlib import Path
from types import SimpleNamespace

from .runtime import admitted, environment_runtime, read, sha, verify_pins, write


def validate_diagnostic(report, manifest):
    quality = (report.get('episode') or {}).get('right_strike_quality', {})
    if (report.get('completed') is not True or report.get('protocol_completed') is not True or
            report.get('mode') != 'diagnostic' or report.get('failure') is not None or
            report.get('no_mid_episode_state_injection') is not True or
            quality.get('success') is not True or quality.get('full_safe') is not True or
            quality.get('prepared_before_hit') is not True or
            quality.get('native_expected_hit_count') != 1 or quality.get('accepted_count') != 1 or
            any(report.get('pins', {}).get(k) != v for k, v in manifest['pins'].items())):
        raise ValueError('Verified full safe prepare/cross/recover diagnostic required before PPO')


def train(manifest_path, out, *, diagnostic_report, updates=100, num_envs=64, horizon=32, size='medium', seed=7):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError('Fresh right strike training output required')
    with admitted(manifest_path) as (manifest, resource):
        diagnostic_report = Path(diagnostic_report).resolve()
        validate_diagnostic(read(diagnostic_report), manifest)
        import isaacgym  # Native import must precede Torch/NumPy.
        from .settings import build_settings
        from guitar_learning.tool.training.legacy_gpu_runner import run
        settings = build_settings(manifest['bundle'], updates=updates, num_envs=num_envs,
                                  horizon=horizon, size=size, seed=seed)
        pins = dict(manifest['pins'])
        pins[str(Path(manifest_path).resolve())] = sha(manifest_path)
        for name in ('report.json', 'poses.npz', 'observations_before_action.npz', 'geometry_fit.json',
                     'actual_arrival.json', 'training_contract.json'):
            path = diagnostic_report.parent/name
            pins[str(path)] = sha(path)
        with environment_runtime():
            result = run(settings, SimpleNamespace(out=out, resume=None))
        if not result.get('completed') or result.get('optimizer_updates') != updates:
            raise RuntimeError('Original PPO training budget/lifecycle did not complete')
        verify_pins(pins)
        checkpoints = {str(out/name): sha(out/name) for name in ('initial.pt', 'final.pt')}
        write(out/'right_strike_lineage.json', dict(schema='guitar_learning.right_strike_lineage.v1',
            completed=True, manifest=str(Path(manifest_path).resolve()),
            manifest_sha256=sha(manifest_path), pins=pins, checkpoints=checkpoints,
            settings=read(out/'settings.json'), settings_sha256=sha(out/'settings.json'),
            resource_before=resource, report_sha256=sha(out/'report.json'),
            scope='Fresh original right6 PPO; prepare/cross/recover is a separate evaluation metric'))
        return result
