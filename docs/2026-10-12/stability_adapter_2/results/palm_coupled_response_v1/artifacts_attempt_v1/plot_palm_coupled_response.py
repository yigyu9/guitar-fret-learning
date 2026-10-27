"""Plot saved coupled hand/guitar response trials; performs no simulation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1'
RUNS = ['baseline'] + [f'axis_{i:02d}' for i in range(12)] + ['heldout']
ANALYSIS = PHASE / 'analysis.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [ANALYSIS, Path(__file__).resolve()]
    paths.extend(PHASE / run / f'{name}.json' for run in RUNS
                 for name in ('report', 'trace', 'tasks', 'contacts'))
    paths = [p.resolve() for p in paths]
    if len(set(paths)) != len(paths) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('missing or duplicate declared inputs')
    return paths


def read_and_validate():
    analysis = json.loads(ANALYSIS.read_text())
    checks = analysis.get('checks', {})
    if len(checks) != 6 or not all(checks.values()):
        raise ValueError('analysis.json must have six passing checks')
    if analysis.get('counts') != {'native_initializations': 14, 'physics_steps': 336}:
        raise ValueError('unexpected phase counts')
    summary = {row['label']: row for row in analysis['summary']}
    if set(summary) != set(RUNS):
        raise ValueError('unexpected run labels in analysis')
    raw = {}
    for run in RUNS:
        base = PHASE / run
        report, trace, tasks, contacts = [json.loads((base / f'{name}.json').read_text())
                                          for name in ('report', 'trace', 'tasks', 'contacts')]
        if report.get('failure') or report.get('native_initializations') != 1 or report.get('physics_steps') != 24:
            raise ValueError(f'{run}: incomplete report')
        if not report.get('checks') or not all(report['checks'].values()):
            raise ValueError(f'{run}: report checks failed')
        if len(trace) != 25 or len(tasks) != 25 or len(contacts) != 24:
            raise ValueError(f'{run}: expected 25 states/tasks and 24 contact records')
        times = [float(row['time_s']) for row in trace]
        if any(not math.isfinite(t) or abs(t - i / 240.0) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{run}: invalid trace timestamps')
        task_mm = math.sqrt(sum(float(v) ** 2 for v in tasks[-1][:3])) * 1000
        task_deg = math.sqrt(sum(float(v) ** 2 for v in tasks[-1][3:6])) / .08 * 180 / math.pi
        max_g_pos = max(float(row['position_error_m']) * 1000 for row in trace)
        max_g_rot = max(float(row['rotation_error_deg']) for row in trace)
        positive_steps, positive_rows = [], 0
        for contact_record in contacts:
            vals = [float(c['lambda']) for c in contact_record['contacts']
                    if {c.get('body0_name'), c.get('body1_name')} == {'guitar/guitar', 'human/LH:palm'}]
            count = sum(value > 0 for value in vals)
            if count:
                positive_steps.append(int(contact_record['physics_step']))
                positive_rows += count
        row = summary[run]
        expected = (row['end_point_error_mm'], row['end_normal_angle_deg'],
                    row['max_guitar_position_error_mm'], row['max_guitar_rotation_error_deg'])
        actual = (task_mm, task_deg, max_g_pos, max_g_rot)
        if any(abs(float(x) - float(y)) > 1e-6 for x, y in zip(expected, actual)):
            raise ValueError(f'{run}: raw task/trace does not match analysis summary')
        if positive_steps != row['positive_raw_palm_lambda_steps'] or positive_rows != row['positive_raw_palm_lambda_rows']:
            raise ValueError(f'{run}: raw palm lambda does not match summary')
        raw[run] = {'report': report, 'trace': trace, 'tasks': tasks,
                    'summary': row, 'positive_steps': positive_steps,
                    'positive_rows': positive_rows}

    baseline = raw['baseline']['report']
    joint_names = baseline['human_joint_names']
    arm_indices = baseline['arm_indices']
    if len(arm_indices) != 12 or len(joint_names) != 81:
        raise ValueError('unexpected 12-axis arm mapping')
    names = [joint_names[index] for index in arm_indices]
    base_bias = [float(x) for x in baseline['bias_rad']]
    if len(base_bias) != 12:
        raise ValueError('baseline bias must contain 12 values')
    for i in range(12):
        report = raw[f'axis_{i:02d}']['report']
        if report['arm_indices'] != arm_indices or report['human_joint_names'] != joint_names:
            raise ValueError('arm mapping differs between runs')
        bias = [float(x) for x in report['bias_rad']]
        for j in range(12):
            expected = .005 if i == j else 0.0
            if abs((bias[j] - base_bias[j]) - expected) > 1e-6:
                raise ValueError(f'axis_{i:02d}: target delta is not a single +0.005-rad probe')
    heldout_bias = [float(x) for x in raw['heldout']['report']['bias_rad']]
    if any(abs((heldout_bias[i] - base_bias[i]) - .001) > 1e-6 for i in range(12)):
        raise ValueError('heldout is not the expected all-axis +0.001-rad probe')

    heldout = analysis['heldout']
    diff = [float(p) - float(a) for p, a in zip(heldout['predicted_terminal'], heldout['actual_terminal'])]
    derived = {
        'hand_position_mm': math.sqrt(sum(x*x for x in diff[0:3])) * 1000,
        'hand_normal_rotation_vector_deg': math.sqrt(sum(x*x for x in diff[3:6])) / .08 * 180 / math.pi,
        'guitar_position_mm': math.sqrt(sum(x*x for x in diff[6:9])) * 1000,
        'guitar_rotation_vector_deg': math.sqrt(sum(x*x for x in diff[9:12])) * 180 / math.pi,
    }
    for key, value in derived.items():
        if abs(value - float(heldout['terminal_prediction_difference'][key])) > 1e-9:
            raise ValueError(f'heldout prediction difference mismatch: {key}')
    return analysis, raw, names, derived


def make_plot(out_path, raw, names, heldout_diff):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    labels = ['α=.45\n기준'] + names + ['heldout\n+.001×12']
    keys = ['baseline'] + [f'axis_{i:02d}' for i in range(12)] + ['heldout']
    colors = ['#555555'] + ['#3977a8'] * 12 + ['#d27a27']
    fields = [('end_point_error_mm', '손바닥 끝점 오차 (mm)', '손바닥'),
              ('max_guitar_position_error_mm', '기타 최대 위치 오차 (mm)', '기타 위치'),
              ('max_guitar_rotation_error_deg', '기타 최대 회전 오차 (°)', '기타 회전')]
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    xs = list(range(len(keys)))
    for ax, (field, title, label) in zip((axes[0, 0], axes[0, 1], axes[1, 0]), fields):
        values = [float(raw[key]['summary'][field]) for key in keys]
        ax.scatter(xs, values, c=colors, s=35, zorder=3)
        lo, hi = min(values), max(values)
        pad = max((hi - lo) * .15, .01)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_title(title + ' · 관측 범위 확대')
        ax.set_ylabel(label + (' error (mm)' if field != 'max_guitar_rotation_error_deg' else ' error (°)'))
        ax.set_xticks(xs, labels, rotation=58, ha='right', fontsize=7)
        ax.grid(True, axis='y', alpha=.25)
    ax = axes[1, 1]
    ax.axis('off')
    rows = [
        ('손바닥 위치', heldout_diff['hand_position_mm'], 'mm'),
        ('손 법선 회전벡터', heldout_diff['hand_normal_rotation_vector_deg'], '°'),
        ('기타 위치', heldout_diff['guitar_position_mm'], 'mm'),
        ('기타 회전벡터', heldout_diff['guitar_rotation_vector_deg'], '°'),
    ]
    ax.set_title('Heldout: 예측−실제 terminal 차이')
    ax.text(.04, .83, '각 출력 block norm (단위별 별도 표기)', fontsize=10, transform=ax.transAxes)
    for i, (name, value, unit) in enumerate(rows):
        ax.text(.08, .68 - .13*i, f'{name}: {value:.6f} {unit}', fontsize=11, transform=ax.transAxes)
    ax.text(.04, .08, '비교 오차 관측값이며 합격 기준이나 검증 통과 판정이 아님.',
            fontsize=9, transform=ax.transAxes, wrap=True)
    fig.suptitle('저장된 12축 coupled-response 요약 · native 0.1 s · 상수 PD 목표', y=.995)
    fig.tight_layout(rect=(0, 0, 1, .97))
    fig.savefig(out_path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / 'palm_coupled_response.png'
    manifest = out_dir / 'plot_manifest.json'
    if image.exists() or manifest.exists():
        raise FileExistsError('output exists; choose a fresh output directory')
    inputs = explicit_inputs()
    before = {str(path): sha256(path) for path in inputs}
    _, raw, names, heldout_diff = read_and_validate()
    make_plot(image, raw, names, heldout_diff)
    after = {str(path): sha256(path) for path in inputs}
    if before != after:
        image.unlink(missing_ok=True)
        raise RuntimeError('input SHA changed during plotting')
    payload = {'input_sha256': before, 'producer_sha256': sha256(__file__),
               'output_sha256': {str(image): sha256(image)}}
    manifest.write_text(json.dumps(payload, indent=2) + '\n')
    print(image)
    print(manifest)


if __name__ == '__main__':
    main()
