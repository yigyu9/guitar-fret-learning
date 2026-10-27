"""Plot saved palm-hold PD gain comparison; no simulation is run here."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2'
LABELS = ('scale_1', 'scale_1p5', 'scale_2')
COLORS = {'scale_1': '#444444', 'scale_1p5': '#2878b5', 'scale_2': '#d17c18'}
DISPLAY = {'scale_1': '1× kp/kd', 'scale_1p5': '1.5× kp/kd', 'scale_2': '2× kp/kd'}
ANALYSIS = PHASE / 'analysis.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [ANALYSIS, Path(__file__).resolve()]
    for label in LABELS:
        run = PHASE / label
        paths.extend(run / rel for rel in (
            'PD.json', 'native/report.json', 'native/trace.json', 'native/contacts.json'))
    paths = [p.resolve() for p in paths]
    if len(paths) != len(set(paths)) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('declared input missing or duplicated')
    return paths


def load_data():
    analysis = json.loads(ANALYSIS.read_text())
    checks = analysis.get('checks', {})
    if len(checks) != 6 or not all(checks.values()):
        raise ValueError('analysis.json must have six passing structural checks')
    if analysis.get('counts') != {'native_initializations': 3, 'physics_steps': 72}:
        raise ValueError('unexpected run counts')
    if set(analysis.get('curves', {})) != set(LABELS):
        raise ValueError('unexpected curve labels')
    summaries = {row['label']: row for row in analysis['summary']}
    result = {}
    for label in LABELS:
        run = PHASE / label
        pd = json.loads((run / 'PD.json').read_text())
        report = json.loads((run / 'native/report.json').read_text())
        trace = json.loads((run / 'native/trace.json').read_text())
        contacts = json.loads((run / 'native/contacts.json').read_text())
        for name, obj in (('PD', pd), ('report', report)):
            if not obj.get('checks') or not all(obj['checks'].values()):
                raise ValueError(f'{label}: {name} checks did not pass')
            if obj.get('native_initializations') != 1 or obj.get('physics_steps') != 24:
                raise ValueError(f'{label}: unexpected {name} counts')
        expected_scale = {'scale_1': 1.0, 'scale_1p5': 1.5, 'scale_2': 2.0}[label]
        if pd['trial']['left_arm_PD_scale'] != expected_scale:
            raise ValueError(f'{label}: unexpected left-arm scale')
        if len(report['pd_kp']) != 81 or len(report['pd_kd']) != 81:
            raise ValueError(f'{label}: expected 81 native PD values')
        if len(trace) != 25 or len(contacts) != 24:
            raise ValueError(f'{label}: expected 25 states and 24 contact records')
        curve = analysis['curves'][label]
        times = [float(row['time_s']) for row in trace]
        if len(curve['time_s']) != 25 or any(abs(float(a)-b) > 1e-9 for a, b in zip(curve['time_s'], times)):
            raise ValueError(f'{label}: saved times mismatch')
        fields = (
            ('guitar_position_error_mm', 'position_error_m', 1000.0),
            ('guitar_rotation_error_deg', 'rotation_error_deg', 1.0),
        )
        for curve_key, raw_key, scale in fields:
            raw = [float(row[raw_key]) * scale for row in trace]
            values = [float(x) for x in curve[curve_key]]
            if len(values) != 25 or any(not math.isfinite(x) for x in values):
                raise ValueError(f'{label}: invalid {curve_key}')
            if any(abs(a-b) > 1e-7 for a, b in zip(values, raw)):
                raise ValueError(f'{label}: {curve_key} differs from trace')
        lambdas = []
        for step, record in enumerate(contacts, 1):
            if record.get('physics_step') != step:
                raise ValueError(f'{label}: contact step order mismatch')
            values = [float(c['lambda']) for c in record['contacts']
                      if {c.get('body0_name'), c.get('body1_name')} ==
                      {'guitar/guitar', 'human/LH:palm'}]
            lambdas.append(max(values, default=0.0))
        raw_lambda = [float(x) for x in curve['step_max_raw_palm_lambda']]
        if len(raw_lambda) != 24 or any(abs(a-b) > 1e-7 for a, b in zip(raw_lambda, lambdas)):
            raise ValueError(f'{label}: palm lambda curve differs from raw contacts')
        gap = [float(x) for x in curve['source_normal_gap_mm']]
        if len(gap) != 25 or not all(math.isfinite(x) for x in gap):
            raise ValueError(f'{label}: invalid source gap curve')
        result[label] = {'curve': curve, 'summary': summaries[label], 'time_s': times}
    return result


def draw(path, data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    panels = (
        (axes[0, 0], 'guitar_position_error_mm', 25, '기타 위치 오차', '오차 (mm)'),
        (axes[0, 1], 'guitar_rotation_error_deg', 25, '기타 회전 오차', '오차 (deg)'),
        (axes[1, 0], 'source_normal_gap_mm', 25, 'source 법선 간격', '간격 (mm)'),
        (axes[1, 1], 'step_max_raw_palm_lambda', 24, 'LH:palm 최대 raw lambda', 'raw lambda (N 환산 아님)'),
    )
    for ax, field, count, title, ylabel in panels:
        for label in LABELS:
            series = data[label]
            times = series['time_s'] if count == 25 else series['time_s'][1:]
            ax.plot(times, series['curve'][field], marker='o', ms=2.5, lw=1.5,
                    color=COLORS[label], label=DISPLAY[label])
        ax.set_title(title)
        ax.set_xlabel('저장 시각 (s) · 완료 physics step 시점')
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 0.1)
        ax.grid(True, alpha=.25)
        ax.legend()
    fig.suptitle('왼팔 kp/kd 배율 비교 · 저장된 native 기록 · 0.1초', y=.99)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    image = out_dir / 'palm_hold_pd.png'
    manifest = out_dir / 'plot_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory is not empty; choose a fresh directory')
    inputs = explicit_inputs()
    before = {str(p): sha256(p) for p in inputs}
    data = load_data()
    out_dir.mkdir(parents=True, exist_ok=True)
    draw(image, data)
    after = {str(p): sha256(p) for p in inputs}
    if before != after:
        raise RuntimeError('an input changed while plotting')
    manifest.write_text(json.dumps({
        'input_sha256': before,
        'producer_sha256': sha256(__file__),
        'output_sha256': {str(image): sha256(image)},
    }, indent=2) + '\n')
    print(image)
    print(manifest)


if __name__ == '__main__':
    main()
