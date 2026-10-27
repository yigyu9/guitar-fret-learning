"""Plot saved palm-contact-boundary trials; this script performs no simulation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1'
PREVIOUS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1'
RUNS = {
    'α=.25 · quarter reference': PREVIOUS / 'validation/corrected_quarter',
    'α=.30': PHASE / 'alpha_30',
    'α=.35': PHASE / 'alpha_35',
    'α=.40': PHASE / 'alpha_40',
    'α=.45': PHASE / 'alpha_45',
    'α=.50 · half reference': PREVIOUS / 'validation/corrected_half',
}
ANALYSIS = PHASE / 'analysis.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [ANALYSIS, Path(__file__).resolve()]
    paths.extend(directory / name for directory in RUNS.values()
                 for name in ('trace.json', 'contacts.json'))
    paths = [p.resolve() for p in paths]
    if len(set(paths)) != len(paths) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('missing or duplicate declared plot inputs')
    return paths


def read_data():
    analysis = json.loads(ANALYSIS.read_text())
    checks = analysis.get('checks')
    if not isinstance(checks, dict) or len(checks) != 6 or not all(checks.values()):
        raise ValueError('analysis.json must contain six passing structural checks')
    if analysis.get('counts') != {'native_initializations': 4, 'physics_steps': 96}:
        raise ValueError('unexpected current-phase counts')
    summary = {row['label']: row for row in analysis['summary']}
    alpha_for = {'corrected_quarter': .25, 'alpha_30': .30, 'alpha_35': .35,
                 'alpha_40': .40, 'alpha_45': .45, 'corrected_half': .50}
    result = {}
    for label, directory in RUNS.items():
        run_name = directory.name
        row = summary.get(run_name)
        if not row or abs(row['alpha'] - alpha_for[run_name]) > 1e-12:
            raise ValueError(f'analysis summary mismatch: {run_name}')
        if Path(row['run_path']).resolve() != directory.resolve():
            raise ValueError(f'analysis path mismatch: {run_name}')
        curve = analysis['curves'][str(alpha_for[run_name])]
        trace = json.loads((directory / 'trace.json').read_text())
        contacts = json.loads((directory / 'contacts.json').read_text())
        if len(trace) != 25 or len(contacts) != 24:
            raise ValueError(f'{run_name}: expected 25 trace rows and 24 contacts records')
        times = [float(item['time_s']) for item in trace]
        if any(not math.isfinite(t) or abs(t - i / 240) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{run_name}: invalid trace time coverage')
        vector = curve['guitar_error_W_m_rad']
        native_drift = curve['guitar_native_start_drift_W_m_rad']
        if len(vector) != 25 or len(native_drift) != 25 or len(curve['source_normal_gap_mm']) != 25 or len(curve['step_max_raw_palm_lambda']) != 24:
            raise ValueError(f'{run_name}: invalid analyzed curve coverage')
        p_mm, q_deg, trace_p_mm, trace_q_deg, start_p_mm, start_q_deg = [], [], [], [], [], []
        source_gap, lambdas = [], []
        for i, (sample, err, drift) in enumerate(zip(trace, vector, native_drift)):
            if len(err) != 6 or not all(math.isfinite(float(x)) for x in err):
                raise ValueError(f'{run_name}: invalid world guitar error vector')
            p = math.sqrt(sum(float(x) ** 2 for x in err[:3])) * 1000
            q = math.sqrt(sum(float(x) ** 2 for x in err[3:])) * 180 / math.pi
            if len(drift) != 6 or not all(math.isfinite(float(x)) for x in drift):
                raise ValueError(f'{run_name}: invalid native-start drift vector')
            sp = math.sqrt(sum(float(x) ** 2 for x in drift[:3])) * 1000
            sq = math.sqrt(sum(float(x) ** 2 for x in drift[3:])) * 180 / math.pi
            rp = float(sample['position_error_m']) * 1000
            rq = float(sample['rotation_error_deg'])
            if not all(math.isfinite(x) for x in (p, q, rp, rq)):
                raise ValueError(f'{run_name}: nonfinite guitar metric')
            if abs(p - rp) > 1e-5 or abs(q - rq) > 1e-5:
                raise ValueError(f'{run_name}: analysis vector and trace norm differ')
            p_mm.append(p); q_deg.append(q); trace_p_mm.append(rp); trace_q_deg.append(rq)
            start_p_mm.append(sp); start_q_deg.append(sq)
            source_gap.append(float(curve['source_normal_gap_mm'][i]))
            if i:
                raw_rows = contacts[i - 1]['contacts']
                palm = [float(c['lambda']) for c in raw_rows
                        if c.get('body0_name') == 'guitar/guitar' and c.get('body1_name') == 'human/LH:palm']
                value = max(palm, default=0.0)
                if abs(value - float(curve['step_max_raw_palm_lambda'][i - 1])) > 1e-6:
                    raise ValueError(f'{run_name}: raw palm lambda mismatch at physics step {i}')
                lambdas.append(value)
        result[label] = {
            'time': times, 'p_mm': p_mm, 'q_deg': q_deg,
            'trace_p_mm': trace_p_mm, 'trace_q_deg': trace_q_deg,
            'start_p_mm': start_p_mm, 'start_q_deg': start_q_deg,
            'gap_mm': source_gap, 'lambda': lambdas, 'summary': row,
        }
    return analysis, result


def make_plot(out_path, data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    colors = ['#555555', '#3977a8', '#55a868', '#e08b28', '#b64f4f', '#8156a8']
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    panels = [('p_mm', '기타 위치 오차 (mm; 설정 초기 목표 기준)'),
              ('q_deg', '기타 회전 오차 (°; 설정 초기 목표 기준)'),
              ('gap_mm', 'Source normal gap (mm)'),
              ('lambda', 'Raw palm λ (원시 단위; N 환산 아님)')]
    for ax, (field, title) in zip(axes.flat, panels):
        for (label, series), color in zip(data.items(), colors):
            time = series['time'][1:] if field == 'lambda' else series['time']
            ax.plot(time, series[field], color=color, marker='o', ms=2.1,
                    lw=1.5, label=label)
            if field == 'p_mm':
                ax.plot(series['time'], series['start_p_mm'], color=color, lw=1.0,
                        ls='--', alpha=.72)
            elif field == 'q_deg':
                ax.plot(series['time'], series['start_q_deg'], color=color, lw=1.0,
                        ls='--', alpha=.72)
        ax.set_title(title)
        ax.set_xlim(0, .1)
        ax.set_xlabel('저장 시각 (s)')
        ax.grid(True, alpha=.25)
        ax.legend(fontsize=7, ncol=2)
    axes[0, 0].text(.02, .97, '실선: 설정 목표 기준 · 점선: native t=0 기준',
                    transform=axes[0, 0].transAxes, va='top', fontsize=8,
                    bbox={'facecolor': 'white', 'alpha': .8, 'edgecolor': 'none'})
    axes[0, 1].text(.02, .97, '실선: 설정 목표 기준 · 점선: native t=0 기준',
                    transform=axes[0, 1].transAxes, va='top', fontsize=8,
                    bbox={'facecolor': 'white', 'alpha': .8, 'edgecolor': 'none'})
    axes[1, 1].set_ylim(bottom=0)
    fig.suptitle('저장 native response · 고정 상수 palm 목표 보정 · 0.1 s', y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / 'palm_contact_boundary.png'
    manifest = out_dir / 'plot_manifest.json'
    if image.exists() or manifest.exists():
        raise FileExistsError('output already exists; choose a fresh directory')
    inputs = explicit_inputs()
    before = {str(p): sha256(p) for p in inputs}
    _, data = read_data()
    make_plot(image, data)
    after = {str(p): sha256(p) for p in inputs}
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
