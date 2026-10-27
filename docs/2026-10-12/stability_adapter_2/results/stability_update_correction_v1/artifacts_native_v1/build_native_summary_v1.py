#!/usr/bin/env python3
"""Build visual summaries from completed smoke_on_v1 native artifacts."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from PIL import Image

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1'
OUT = RESULTS / 'artifacts_native_v1'
RUN = RESULTS / 'smoke_on_v1'
RUNTIME = RESULTS / 'runtime_verification_v2.json'
BRIEF = RESULTS / 'next_change_brief_v1.json'
SUPPORT = RESULTS / 'nominal_support_analysis_v2.json'
TRAINING = RUN / 'training.jsonl'
CHECKPOINTS = ['initial_000000', 'update_000001', 'update_000003']
LABELS = ['초기 정책 (0 update)', 'update 1', 'update 3']
FRAME_AT = [(0, '0초'), (60, '2초'), (491, '16.3667초 끝 프레임')]
COLORS = ['#415A77', '#2A9D8F', '#E07A5F']


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def evaluation_dir(checkpoint):
    return RUN / 'evaluations' / checkpoint / 'native/episode_0001'


def frame_path(checkpoint, camera, index):
    return evaluation_dir(checkpoint) / 'media/frames' / camera / f'{index:05d}.png'


def video_path(checkpoint, camera):
    return evaluation_dir(checkpoint) / 'media' / f'{camera}.mp4'


def sha_record(path):
    return {'path': str(path), 'sha256': sha256(path), 'bytes': path.stat().st_size}


def render_frames(camera, output, title):
    fig, axes = plt.subplots(3, 3, figsize=(15, 8.8), constrained_layout=True)
    fig.suptitle(title, fontsize=17, fontweight='bold')
    for row, (checkpoint, label) in enumerate(zip(CHECKPOINTS, LABELS)):
        for col, (frame_id, time_label) in enumerate(FRAME_AT):
            ax = axes[row, col]
            with Image.open(frame_path(checkpoint, camera, frame_id)) as image:
                ax.imshow(image.convert('RGB'))
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(time_label, fontsize=12)
            if col == 0:
                ax.set_ylabel(label, fontsize=11, rotation=90, labelpad=10)
            for spine in ax.spines.values():
                spine.set_visible(False)
    fig.savefig(output, dpi=145, facecolor='white')
    plt.close(fig)


def render_outside(runtime, output):
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    for checkpoint, label, color in zip(CHECKPOINTS, LABELS, COLORS):
        rows = json.loads((evaluation_dir(checkpoint) / 'controls.json').read_text())
        times = np.array([r['physics_step'] / 240.0 for r in rows], dtype=float)
        vectors = np.array([r['position_outside_m'] for r in rows], dtype=float)
        outside_norm = np.linalg.norm(vectors, axis=1)
        pct = runtime['evaluations'][checkpoint]['outside_percent']
        ax.plot(times, outside_norm, color=color, linewidth=1.8,
                label=f'{label} · 범위 밖 {pct:.2f}%')
    ax.set_xlim(0, 16.3667)
    ax.set_xlabel('물리 경과 시간 (초)')
    ax.set_ylabel('위치 허용범위 밖 거리 벡터 크기 (m)')
    ax.set_title('3개 checkpoint native 평가 중 위치 범위 밖 거리')
    ax.grid(alpha=.25)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0, frameon=True)
    fig.subplots_adjust(right=.70, left=.10, bottom=.12, top=.88)
    fig.savefig(output, dpi=170, facecolor='white', bbox_inches='tight')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = json.loads(RUNTIME.read_text())
    brief = json.loads(BRIEF.read_text())
    support = json.loads(SUPPORT.read_text())
    training = [json.loads(line) for line in TRAINING.read_text().splitlines() if line.strip()]

    # Register every file read by this producer, including selected native frames and embedded clips.
    input_paths = [RUNTIME, BRIEF, SUPPORT, TRAINING]
    for checkpoint in CHECKPOINTS:
        folder = evaluation_dir(checkpoint)
        input_paths.extend([folder / 'controls.json', folder / 'report.json', folder / 'initial_values.json'])
        input_paths.extend([video_path(checkpoint, camera) for camera in ('whole_body', 'hands')])
        input_paths.extend([frame_path(checkpoint, camera, frame) for camera in ('whole_body', 'hands') for frame, _ in FRAME_AT])
    input_paths = list(dict.fromkeys(input_paths))
    before = {str(p): sha_record(p) for p in input_paths}

    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus'] = False

    whole_body = OUT / 'native_whole_body_frames_v1.png'
    hands = OUT / 'native_hands_frames_v1.png'
    outside = OUT / 'native_outside_over_time_v1.png'
    render_frames('whole_body', whole_body, '실제 native 전신 프레임: 0초 · 2초 · 16.3667초')
    render_frames('hands', hands, '실제 native 손 프레임: 0초 · 2초 · 16.3667초')
    render_outside(runtime, outside)

    after = {str(p): sha_record(p) for p in input_paths}
    if before != after:
        raise RuntimeError('입력 파일이 그림 생성 중 변경됨; provenance 봉인 실패')
    script = Path(__file__).resolve()
    plots = [whole_body, hands, outside]
    manifest = {
        'purpose': 'smoke_on_v1 P단계 native 결과 시각화; 다른 phase 결과 제외',
        'producer': sha_record(script),
        'inputs_before': list(before.values()),
        'inputs_after': list(after.values()),
        'inputs_unchanged_during_render': True,
        'plots': [sha_record(p) for p in plots],
        'runtime_verification': {'path': str(RUNTIME), 'checks_passed': runtime['checks_passed'],
                                 'checks': runtime['checks']},
        'training_updates': [{'update': row['update'], 'transitions': row['transitions'],
                              'optimizer_steps': row['ppo']['optimizer_steps'],
                              'final_analytic_kl': row['ppo']['final_analytic_kl'],
                              'RMS_updated': row['ppo']['RMS_updated']} for row in training],
        'evaluations': runtime['evaluations'],
        'nominal_support_diagnostic': support,
        'next_change_brief': brief,
        'scope_note': '세 native 평가는 각각 16.3667초/492 frames, 공동 음악 성공 0이며 안정화·학습 품질 성공을 뜻하지 않음.',
    }
    (OUT / 'native_provenance_v1.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'producer_sha256': sha256(script), 'plots': [sha_record(p) for p in plots],
                      'inputs': len(input_paths)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
