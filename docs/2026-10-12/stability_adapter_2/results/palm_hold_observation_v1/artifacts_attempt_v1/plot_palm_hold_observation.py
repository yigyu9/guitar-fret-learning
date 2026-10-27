"""Plot saved palm-hold coordinate and total-DOF-force observations only."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1'
RUNS = {name: PHASE / name for name in ('baseline', 'full')}
JOINTS = ('L_Shoulder_x', 'L_Elbow_y')
ANALYSIS = PHASE / 'analysis.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [ANALYSIS, Path(__file__).resolve()]
    for directory in RUNS.values():
        paths.extend([
            directory / 'observation.json',
            directory / 'native/report.json',
            directory / 'native/trace.json',
            directory / 'native/controls.json',
        ])
    paths = [path.resolve() for path in paths]
    if len(set(paths)) != len(paths) or any(not path.is_file() for path in paths):
        raise FileNotFoundError('missing or duplicate declared plot inputs')
    return paths


def read_data():
    analysis = json.loads(ANALYSIS.read_text())
    checks = analysis.get('checks')
    if not isinstance(checks, dict) or len(checks) != 5 or not all(checks.values()):
        raise ValueError('analysis.json must contain five passing checks')
    if analysis.get('counts') != {'native_initializations': 2, 'physics_steps': 48}:
        raise ValueError('unexpected observation phase counts')
    curves = analysis.get('curves', {})
    if set(curves) != set(RUNS):
        raise ValueError('unexpected observation curve labels')

    result = {}
    baseline_observation = json.loads((RUNS['baseline'] / 'observation.json').read_text())
    reference_properties = baseline_observation['properties']
    for label, directory in RUNS.items():
        observation = json.loads((directory / 'observation.json').read_text())
        report = json.loads((directory / 'native/report.json').read_text())
        trace = json.loads((directory / 'native/trace.json').read_text())
        controls = json.loads((directory / 'native/controls.json').read_text())
        obs_checks = observation.get('checks', {})
        if not obs_checks or not all(obs_checks.values()):
            raise ValueError(f'{label}: observer checks failed')
        if observation.get('native_initializations') != 1 or observation.get('physics_steps') != 24:
            raise ValueError(f'{label}: unexpected native execution counts')
        if observation.get('t0_force_measurement') is not None:
            raise ValueError(f'{label}: expected t0 force to be unavailable')
        if (report.get('native_initializations') != 1 or report.get('physics_steps') != 24
                or report.get('failure')):
            raise ValueError(f'{label}: incomplete native report')
        if not all(report.get('checks', {}).values()):
            raise ValueError(f'{label}: native report checks failed')
        if observation['properties'] != reference_properties:
            raise ValueError(f'{label}: native properties differ from baseline')
        names = observation['properties']['human_joint_names']
        if names != report['human_joint_names'] or len(names) != 81:
            raise ValueError(f'{label}: native DOF name mapping mismatch')
        type_codes = observation['properties']['native_DOF_type_codes']
        units = observation['properties']['native_DOF_units']
        if len(type_codes) != 81 or len(units) != 81:
            raise ValueError(f'{label}: invalid native DOF type/unit mapping')
        samples = observation.get('samples', [])
        if len(samples) != 24 or len(trace) != 25 or len(controls) != 24:
            raise ValueError(f'{label}: expected 24 force samples, 25 states, 24 controls')
        control_targets = []
        for step, control in enumerate(controls, 1):
            if int(control['physics_step']) != step:
                raise ValueError(f'{label}: control step alignment mismatch')
            control_targets.append(control['final_target_rad'])
        if any(target != control_targets[0] for target in control_targets[1:]):
            raise ValueError(f'{label}: submitted Python target vector changed during hold')

        state_times = [float(row['time_s']) for row in trace]
        if any(not math.isfinite(t) or abs(t - i / 240.0) > 1e-9
               for i, t in enumerate(state_times)):
            raise ValueError(f'{label}: invalid saved-state time coverage')
        force_times, force_vectors = [], []
        for step, sample in enumerate(samples, 1):
            time = float(sample['time_s'])
            if (int(sample['physics_step']) != step or not math.isfinite(time)
                    or abs(time - step / 240.0) > 1e-9):
                raise ValueError(f'{label}: force sample is not aligned to completed step')
            values = sample['native_total_DOF_force']
            if len(values) != 81 or not all(math.isfinite(float(x)) for x in values):
                raise ValueError(f'{label}: invalid native total DOF force vector')
            force_times.append(time)
            force_vectors.append([float(x) for x in values])

        joint_series = {}
        for name in JOINTS:
            index = names.index(name)
            if type_codes[index] != 1 or units[index] != 'Nm':
                raise ValueError(f'{label}/{name}: unexpected native joint type or unit')
            curve = curves[label]['joints'][name]
            errors = [float(x) for x in curve['native_coordinate_error_rad']]
            forces = [float(x) for x in curve['total_DOF_force_Nm']]
            if len(errors) != 25 or len(forces) != 24:
                raise ValueError(f'{label}/{name}: curve sample count mismatch')
            if not all(math.isfinite(x) for x in errors + forces):
                raise ValueError(f'{label}/{name}: nonfinite plotted value')
            if any(abs(value - force_vectors[i][index]) > 1e-7
                   for i, value in enumerate(forces)):
                raise ValueError(f'{label}/{name}: analysis force differs from observer sample')
            joint_series[name] = {
                'coordinate_error_rad': errors,
                'force_Nm': forces,
            }
        result[label] = {
            'state_time_s': state_times,
            'force_time_s': force_times,
            'joints': joint_series,
            'observation': observation,
        }
    return analysis, result


def make_plot(output, data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    colors = {'baseline': '#555555', 'full': '#d27a27'}
    labels = {'baseline': '기준', 'full': '관측 추가'}
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    panels = [
        (axes[0, 0], 'L_Shoulder_x', 'coordinate_error_rad', 'L_Shoulder_x 좌표 오차', '좌표 오차 (rad)', False),
        (axes[0, 1], 'L_Elbow_y', 'coordinate_error_rad', 'L_Elbow_y 좌표 오차', '좌표 오차 (rad)', False),
        (axes[1, 0], 'L_Shoulder_x', 'force_Nm', 'L_Shoulder_x total DOF force', '힘 관측값 (Nm)', True),
        (axes[1, 1], 'L_Elbow_y', 'force_Nm', 'L_Elbow_y total DOF force', '힘 관측값 (Nm)', True),
    ]
    for ax, joint, field, title, ylabel, force in panels:
        for label, series in data.items():
            time = series['force_time_s'] if force else series['state_time_s']
            ax.plot(time, series['joints'][joint][field], marker='o', ms=2.5,
                    lw=1.5, color=colors[label], label=labels[label])
        ax.set_title(title)
        ax.set_xlabel('저장 시각 (s) · force는 완료 step 시점')
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, .1)
        ax.grid(True, alpha=.25)
        ax.legend()
    fig.suptitle('저장 native 관절 좌표와 total-DOF-force 관측 · 0.1 s', y=.99)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(output, dpi=160, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / 'palm_hold_observation.png'
    manifest = out_dir / 'plot_manifest.json'
    if image.exists() or manifest.exists():
        raise FileExistsError('output exists; choose a fresh directory')
    inputs = explicit_inputs()
    before = {str(path): sha256(path) for path in inputs}
    _, data = read_data()
    make_plot(image, data)
    after = {str(path): sha256(path) for path in inputs}
    if before != after:
        image.unlink(missing_ok=True)
        raise RuntimeError('input SHA changed during plotting')
    manifest.write_text(json.dumps({
        'input_sha256': before,
        'producer_sha256': sha256(__file__),
        'output_sha256': {str(image): sha256(image)},
    }, indent=2) + '\n')
    print(image)
    print(manifest)


if __name__ == '__main__':
    main()
