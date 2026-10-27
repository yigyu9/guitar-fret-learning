from __future__ import annotations
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from PIL import Image

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4')
INPUT = BASE / 'counterexamples.json'
OUTPUT = BASE / 'audit_signals.png'
MANIFEST = BASE / 'producer_manifest.json'
FINAL_PRODUCER = BASE / 'generate_audit_signals.py'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def hashes(paths: dict[str, Path]) -> dict[str, str]:
    return {key: sha256(path) for key, path in paths.items()}


def main() -> None:
    raw = INPUT.read_bytes()
    before_input = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    declared = data['input_sha256']
    source_paths = {key: Path(path) for path, key in ((p, p) for p in declared)}
    before_sources = hashes(source_paths)
    mismatches = {k: (declared[k], before_sources[k]) for k in declared if declared[k] != before_sources[k]}
    if mismatches:
        raise RuntimeError(f'frozen source hashes differ from counterexamples.json: {mismatches}')

    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(22, 9.1), dpi=120)
    fig.patch.set_facecolor('#f5f7fb')
    for ax in axes:
        ax.set_facecolor('white')
        ax.grid(True, axis='y', color='#dbe3eb', linewidth=.8)
        ax.spines[['top', 'right']].set_visible(False)

    # Panel 1: exact 60-frame traces and source CPU tracker fields.
    ax = axes[0]
    dropout = data['dropout']
    traces = [row['trace'] for row in dropout]
    ax.imshow(traces, aspect='auto', interpolation='nearest', origin='upper',
              cmap=ListedColormap(['#d66b5e', '#65a486']), vmin=0, vmax=1,
              extent=(0, 60, 1.5, -0.5))
    ax.set_yticks([0, 1], ['6개 분산 dropout', '6개 연속 dropout'], fontsize=10)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60])
    ax.set_xlim(0, 60)
    ax.set_xlabel('eligible frame index (60 frames)', fontsize=10)
    ax.set_title('같은 hold 비율, 다른 끊김 모양', fontsize=15, fontweight='bold', color='#18324b', pad=13)
    ax.set_ylabel('합성 press 성공 trace', fontsize=10)
    ax.grid(False)
    ax.text(.03, -.23,
            '두 조건 모두 54/60, U=.90, 마지막 O=1, E=1 가정\n'
            '조건부 F + 0.10U - 0.05E = 2.04 (동일)\n'
            'CPU tracker: longest dropout 1 → pass, 6 → fail (cutoff 3)',
            transform=ax.transAxes, va='top', fontsize=9, color='#455b6b',
            bbox=dict(boxstyle='round,pad=.45', fc='white', ec='#c5d0db', alpha=.96))
    ax.text(.03, .98, '정상 frame', transform=ax.transAxes, va='top', fontsize=8, color='#397454')
    ax.text(.24, .98, 'dropout', transform=ax.transAxes, va='top', fontsize=8, color='#a3483e')

    # Panel 2: values are copied from pure-position samples; rotation is zero.
    ax = axes[1]
    cap = data['guitar_cap']
    x = [r['pure_position_outside_mm'] for r in cap]
    craw = [r['C_raw'] for r in cap]
    cg = [r['C_g'] for r in cap]
    ax.plot(x, craw, 'o-', color='#c06a35', lw=2.7, ms=7, label='C_raw · 포화 전')
    ax.plot(x, cg, 's-', color='#347a9f', lw=2.7, ms=6, label='C_g · 학습용 cap')
    ax.axhline(1, color='#8795a1', lw=1, ls=':')
    ax.axvline(30, color='#8795a1', lw=1.2, ls='--', label='30 mm부터 cap=1')
    ax.set_title('순수 위치 이탈과 포화', fontsize=15, fontweight='bold', color='#18324b', pad=13)
    ax.set_xlabel('허용범위 바깥 거리 (mm)', fontsize=10)
    ax.set_ylabel('무차원 비용 C_raw / C_g', fontsize=10)
    ax.set_xticks(x, [str(v) for v in x])
    ax.set_ylim(-.15, 4.95)
    ax.legend(loc='upper left', fontsize=9, frameon=True)
    ax.text(.97, .50, '회전 이탈 = 0°', transform=ax.transAxes, ha='right', va='center', fontsize=9,
            color='#526879', bbox=dict(boxstyle='round,pad=.35', fc='white', ec='#c5d0db', alpha=.94))

    # Panel 3: synthetic 60 Hz retention values, log y-axis.
    ax = axes[2]
    discounts = data['discount']
    positions = list(range(len(discounts)))
    gamma_labels = [f"{row['gamma_per_step']:.3g}" for row in discounts]
    w2 = [row['weight_after_2s'] for row in discounts]
    w5 = [row['weight_after_5s'] for row in discounts]
    ax.plot(positions, w2, 'o-', color='#347a9f', lw=2.5, ms=7, label='2초 뒤')
    ax.plot(positions, w5, 's-', color='#9b5b91', lw=2.5, ms=7, label='5초 뒤')
    ax.set_yscale('log')
    ax.set_ylim(1e-8, 1.2)
    ax.set_xticks(positions, gamma_labels)
    ax.set_title('할인 후 잔존 가중치', fontsize=15, fontweight='bold', color='#18324b', pad=13)
    ax.set_xlabel('step당 γ', fontsize=10)
    ax.set_ylabel('잔존 가중치 (log scale)', fontsize=10)
    ax.legend(loc='lower right', fontsize=9, frameon=True)
    half_lives = '반감기 (합성 60 Hz): ' + ' · '.join(
        f"γ={row['gamma_per_step']:.3g}: {row['half_life_seconds']:.3f}s" for row in discounts)
    ax.text(.04, .97, '60 Hz는 합성 환산 가정\nadapter γ 설정/추천을 뜻하지 않음\n' + half_lives,
            transform=ax.transAxes, va='top', fontsize=8.4, color='#526879',
            bbox=dict(boxstyle='round,pad=.4', fc='white', ec='#c5d0db', alpha=.95))
    for i, (v2, v5) in enumerate(zip(w2, w5)):
        ax.annotate(f'{v2:.3g}', (i, v2), xytext=(5, 5), textcoords='offset points', fontsize=7.5, color='#285c79')
        ax.annotate(f'{v5:.3g}', (i, v5), xytext=(5, -11), textcoords='offset points', fontsize=7.5, color='#79446f')

    fig.suptitle('보상 감사 신호 · 계산/계측 비교 · 새 물리 0 / 학습 0',
                 fontsize=21, fontweight='bold', color='#18324b', y=.985)
    fig.text(.5, .94, 'counterexamples.json 기반 · 수치/단위는 각 패널에 표시 · Isaac Gym 렌더가 아님',
             ha='center', fontsize=10.5, color='#526879')
    fig.subplots_adjust(left=.07, right=.985, bottom=.31, top=.86, wspace=.36)
    fig.savefig(OUTPUT, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)

    after_input = sha256(INPUT)
    after_sources = hashes(source_paths)
    if before_input != after_input or before_sources != after_sources:
        raise RuntimeError('an input changed while rendering; output must not be treated as verified')
    with Image.open(OUTPUT) as image:
        width, height = image.size
    manifest = {
        'scope': 'figure production only; input JSON and declared source hashes checked before/after render',
        'counterexamples_sha256_before': before_input,
        'counterexamples_sha256_after': after_input,
        'declared_source_sha256': declared,
        'source_sha256_before': before_sources,
        'source_sha256_after': after_sources,
        'all_inputs_unchanged': True,
        'producer_path': str(FINAL_PRODUCER),
        'producer_sha256': sha256(FINAL_PRODUCER),
        'outputs': {
            'README.md': sha256(BASE / 'README.md'),
            'audit_signals.png': sha256(OUTPUT),
            'audit_signals_png_dimensions': [width, height],
        },
        'source_tracker_cases': [
            {'trace': row['name'], 'U': row['U'], 'longest_dropout_frames': row['source_metrics']['sustain_max_dropout_frames'],
             'interruptions': row['source_metrics']['sustain_interruption_count'],
             'event_success_rate': row['source_metrics']['sustain_event_success_rate']}
            for row in dropout
        ],
        'native_runs': data['native_runs'],
        'training_updates': data['training_updates'],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
