#!/usr/bin/env python3
"""Draft P-initial vs Q-v1-initial visual comparison; no outcome certification."""
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
P_RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1'
Q_RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1'
OUT = Q_RESULTS / 'artifacts_v1'
INITIAL_COMPARISON = Q_RESULTS / 'initial_comparison_v1.json'
INITIAL_COMPARISON_PRODUCER = Q_RESULTS / 'analyze_initial_comparison_v1.py'
RUNS = {
    'P initial (0 update)': P_RESULTS / 'smoke_on_v1',
    'Q v1 initial (0 update)': Q_RESULTS / 'smoke_on_v1',
}
CAPTIONS = ['0초 · frame 0', '2초 · frame 60', '16.3667초 · frame 491']
FRAME_IDS = [0, 60, 491]
COLORS = ['#415A77', '#E07A5F']


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ep_dir(run):
    return run / 'evaluations/initial_000000/native/episode_0001'


def frame(run, view, frame_id):
    return ep_dir(run) / f'media/frames/{view}/{frame_id:05d}.png'


def render_frames(view, path, title):
    fig, axes = plt.subplots(2, 3, figsize=(15, 7), constrained_layout=True)
    fig.suptitle(title, fontsize=17, fontweight='bold')
    for row, (label, run) in enumerate(RUNS.items()):
        for col, (frame_id, caption) in enumerate(zip(FRAME_IDS, CAPTIONS)):
            ax=axes[row, col]
            with Image.open(frame(run, view, frame_id)) as im:
                ax.imshow(im.convert('RGB'))
            ax.set_xticks([]); ax.set_yticks([])
            if row == 0: ax.set_title(caption, fontsize=11)
            if col == 0: ax.set_ylabel(label, fontsize=11)
            for spine in ax.spines.values(): spine.set_visible(False)
    fig.savefig(path, dpi=145, facecolor='white')
    plt.close(fig)


def render_outside(path, metrics):
    fig, ax = plt.subplots(figsize=(9.5, 5.3), constrained_layout=False)
    for color,(label,run) in zip(COLORS,RUNS.items()):
        controls=json.loads((ep_dir(run)/'controls.json').read_text())
        t=np.array([r['physics_step']/240.0 for r in controls],dtype=float)
        v=np.array([r['position_outside_m'] for r in controls],dtype=float)
        norm=np.linalg.norm(v,axis=1)
        m=metrics[label]
        ax.plot(t,norm,color=color,lw=2,
                label=f"{label} · 범위 밖 {m['outside_percent']:.2f}% · 최대 {m['max_norm_m']:.3f} m")
    ax.set_xlim(0,16.3667)
    ax.set_xlabel('물리 경과 시간 (초)')
    ax.set_ylabel('위치 허용범위 밖 거리 벡터 크기 (m)')
    ax.set_title('P initial과 Q v1 initial native 위치 범위 이탈')
    ax.grid(alpha=.25)
    ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0)
    fig.subplots_adjust(left=.12,right=.69,bottom=.14,top=.88)
    fig.savefig(path,dpi=170,facecolor='white',bbox_inches='tight')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p_run=RUNS['P initial (0 update)']; q_run=RUNS['Q v1 initial (0 update)']
    p_ep=ep_dir(p_run);q_ep=ep_dir(q_run)
    source_paths=[
        INITIAL_COMPARISON, INITIAL_COMPARISON_PRODUCER,
        P_RESULTS/'runtime_verification_v2.json',
        Q_RESULTS/'smoke_on_v1.exit.json', Q_RESULTS/'smoke_on_v1.log',
        Q_RESULTS/'smoke_on_v1/training.jsonl',
        p_ep/'report.json',p_ep/'controls.json',p_ep/'media/whole_body.mp4',p_ep/'media/hands.mp4',
        q_ep/'report.json',q_ep/'controls.json',q_ep/'media/whole_body.mp4',q_ep/'media/hands.mp4',
    ]
    frame_paths=[frame(run,view,index) for run in RUNS.values()
                 for view in ('whole_body','hands') for index in FRAME_IDS]
    inputs=list(dict.fromkeys(source_paths+frame_paths))
    before=[{'path':str(p),'sha256':sha256(p),'bytes':p.stat().st_size} for p in inputs]

    comparison=json.loads(INITIAL_COMPARISON.read_text())
    p_eval=comparison['evaluations']['before']
    q_eval=comparison['evaluations']['support_guard']
    q_report=json.loads((q_ep/'report.json').read_text())
    metrics={
        'P initial (0 update)': {'outside_percent':p_eval['outside_percent'],
                                  'max_norm_m':p_eval['max_position_outside_norm_m'],
                                  'max_root_displacement_m':p_eval['max_displacement_from_initial_root_m'],
                                  'max_rotation_deg':p_eval['max_SO3_rotation_from_initial_deg'],
                                  'music_success':p_eval['joint_success_events'],
                                  'seconds':p_eval['physics_seconds'],'frames':492},
        'Q v1 initial (0 update)': {'outside_percent':q_eval['outside_percent'],
                                     'max_norm_m':q_eval['max_position_outside_norm_m'],
                                     'max_root_displacement_m':q_eval['max_displacement_from_initial_root_m'],
                                     'max_rotation_deg':q_eval['max_SO3_rotation_from_initial_deg'],
                                     'music_success':q_report['joint_success_events'],
                                     'seconds':q_eval['physics_seconds'],'frames':492},
    }
    font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family']=font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus']=False
    whole=OUT/'qp_initial_whole_body_frames_draft_v1.png'
    hands=OUT/'qp_initial_hands_frames_draft_v1.png'
    outside=OUT/'qp_initial_outside_over_time_draft_v1.png'
    render_frames('whole_body',whole,'P initial · Q v1 initial 전신 native frame 비교')
    render_frames('hands',hands,'P initial · Q v1 initial 손 native frame 비교')
    render_outside(outside,metrics)
    after=[{'path':str(p),'sha256':sha256(p),'bytes':p.stat().st_size} for p in inputs]
    if before!=after: raise RuntimeError('입력 파일이 임시 비교 생성 중 변경됨')
    producer=Path(__file__).resolve()
    prov={
        'purpose':'임시 Q v1 초기 평가와 P 초기 평가 비교; 최종 phase 봉인 아님, Q v2 대기',
        'producer':{'path':str(producer),'sha256':sha256(producer),'bytes':producer.stat().st_size},
        'authoritative_comparison_json':{'path':str(INITIAL_COMPARISON),'sha256':sha256(INITIAL_COMPARISON),'bytes':INITIAL_COMPARISON.stat().st_size},
        'authoritative_comparison_producer':{'path':str(INITIAL_COMPARISON_PRODUCER),'sha256':sha256(INITIAL_COMPARISON_PRODUCER),'bytes':INITIAL_COMPARISON_PRODUCER.stat().st_size},
        'input_hashes_from_root_comparison':comparison.get('input_sha256'),
        'root_comparison_invariants':{'inputs_unchanged':comparison.get('inputs_unchanged'),'native_initial_state_equal':comparison.get('native_initial_state_equal')},
        'inputs_before':before,'inputs_after':after,'inputs_unchanged_during_render':True,
        'outputs':[{'path':str(p),'sha256':sha256(p),'bytes':p.stat().st_size} for p in (whole,hands,outside)],
        'metrics':metrics,
        'training_attempt':{'Q_v1_updates':0,'Q_v1_transitions':0,'exit_code':1,
          'readiness_error':'guarded pilot reset required; finished episode must reset'},
        'interpretation':'P/Q initial single evaluations only; both music success 0; no stability/naturalness certification',
    }
    (OUT/'qp_initial_comparison_provenance_draft_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'inputs':len(inputs),'producer_sha256':prov['producer']['sha256'],
      'outputs':prov['outputs'],'P_metrics':metrics['P initial (0 update)'],
      'Q_metrics':metrics['Q v1 initial (0 update)']},ensure_ascii=False))

if __name__=='__main__': main()
