"""Audit actual native readback and summarize three saved transfer diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation as R

from .validate_team_pose_envelope import BODY_CENTER_G, ROOT, read, save, sha

CASES = ('current_control', 'reported_reference', 'reported_center')
LABELS = ('현재 수평 배치', '보고 기준 재구성', '보고 중앙 후보 재구성')
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json'


def pose(row):
    p=row['pose']; return np.array([p['p'][a] for a in 'xyz']),R.from_quat([p['r'][a] for a in 'xyzw'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',type=Path,required=True);args=parser.parse_args()
    phase=args.phase.resolve();out=phase/'analysis';out.mkdir(exist_ok=False)
    paths=[Path(__file__).resolve(),Path(__file__).with_name('validate_team_pose_envelope.py'),BASE,FONT]
    paths += [p for case in CASES for p in (phase/'native'/case).rglob('*') if p.is_file()]
    hashes={str(p):sha(p) for p in paths};save(out/'inputs_before.json',hashes)
    from matplotlib.font_manager import FontProperties, fontManager
    fontManager.addfont(str(FONT));plt.rcParams['font.family']=FontProperties(fname=str(FONT)).get_name()
    plt.rcParams['axes.unicode_minus']=False
    base=read(BASE);expected_pelvis=base['native_initial_state']['human_body_states'][base['human_body_names'].index('Pelvis')]
    summaries=[];runs=[];audits={};preserved={}
    for case in CASES:
        path=phase/'native'/case;initial=read(path/'initial_values.json');report=read(path/'report.json');attempt=read(path/'attempt.json');trace=read(path/'trace.json')
        for p,h in attempt['input_sha256'].items():
            assert sha(p)==h,p;preserved[p]=h
        state=initial['actual_initial_state'];q=np.array([d['pos'] for d in state['human_dof_states']]);limits=initial['PD']
        pelvis=state['human_body_states'][initial['body_names'].index('Pelvis')];pp,pr=pose(pelvis);gp,gr=pose(state['guitar_body_states'][0])
        basis=pr.apply([[-1,0,0],[0,-1,0],[0,0,1]])
        rfu=(gp+gr.apply(BODY_CENTER_G)-pp) @ basis.T
        qerr=float(np.max(abs(q-attempt['candidate']['joint_angles_rad'])))
        checks={'actual_q_candidate_match':qerr<2e-7,
            'actual_q_in_native_limits':bool(np.all(q>=[r['lower'] for r in limits]) and np.all(q<=[r['upper'] for r in limits])),
            'actual_pelvis_exact_BASE':pelvis==expected_pelvis,
            'actual_body_center_matches_record':bool(np.allclose(rfu,initial['body_center_rfu_m'],rtol=0,atol=1e-12)),
            'native_1200_steps_151_samples':report['physics_steps']==1200 and len(trace)==151,
            'runner_checks_pass':all(report['checks'].values()),'runner_no_failure':report['failure'] is None}
        assert all(checks.values()),(case,checks)
        audits[case]={'checks':checks,'actual_q_max_error_rad':qerr,'actual_body_center_rfu_m':rfu.tolist()}
        t=np.array([r['time_s'] for r in trace]);positions=np.array([r['position_W_m'] for r in trace]);rotations=R.from_quat([r['quaternion_xyzw'] for r in trace]);i2=int(np.argmin(abs(t-2)))
        late=t>=2;last=trace[-1];earliest_ground=None;left_steps=0
        for line in (path/'contacts.jsonl').read_text().splitlines():
            row=json.loads(line);cs=row['contacts']
            if any('ground' in (c['body0_name'],c['body1_name']) for c in cs) and earliest_ground is None:earliest_ground=row['step']/240
            if any(any(c[k].startswith('human/LH:') for k in ('body0_name','body1_name')) for c in cs):left_steps+=1
        summaries.append({'case':case,'initial_body_center_rfu_cm':(rfu*100).tolist(),
            'initial_neck_elevation_deg':initial['neck_elevation_deg'],
            'initial_source_intersection_count':report['source_intersection_count'],
            'max_position_change_mm':report['max_position_change_m']*1000,'max_rotation_change_deg':report['max_rotation_change_deg'],
            'final_position_change_mm':last['position_change_m']*1000,'final_rotation_change_deg':last['rotation_change_deg'],
            'late_max_position_change_from_2s_mm':float(np.linalg.norm(positions[late]-positions[i2],axis=1).max()*1000),
            'late_max_rotation_change_from_2s_deg':float(np.degrees((rotations[late]*rotations[i2].inv()).magnitude()).max()),
            'first_ground_contact_s':earliest_ground,'left_hand_contact_steps_of_1200':left_steps,
            'simulation_s':t[-1],'frames':len(trace),'source_initial_clear_only':True})
        runs.append((path,trace))
    save(out/'native_readback_audit.json',audits);save(out/'frozen_runner_inputs.json',preserved)
    save(out/'summary.json',{'cases':summaries,'native_initializations':3,'physics_steps':3600,
        'original_team_reproduction':False,'full_envelope_verified':False,'policy_or_learning_updates':0,
        'conclusion':'Current human joint pose supports the horizontal control much better; reported reconstructed poses lose support. This is not a disproof of the original team visual judgments.'})
    fig,axes=plt.subplots(3,2,figsize=(16,13))
    for i,((path,trace),label) in enumerate(zip(runs,LABELS)):
        for j,frame in enumerate(('00000','00150')):
            axes[i,j].imshow(plt.imread(path/'images/frames/whole_body'/f'{frame}.png'));axes[i,j].axis('off')
            axes[i,j].set_title(f'{label} — {0 if j==0 else 5}초',fontsize=15,pad=8)
    fig.suptitle('같은 휴머노이드 초기각·무스트랩·기존 팔 PI | 실제 Isaac Gym 카메라',fontsize=19,y=.995)
    fig.text(.5,.012,'보고 기준/중앙은 명시한 좌표 가정으로 재구성. 팀원 원본 시험 재현 아님. 고정 카메라에서 낙하한 기타 일부는 화면 밖으로 이동.',ha='center',fontsize=12)
    fig.tight_layout(rect=[0,.035,1,.975]);fig.savefig(out/'native_comparison.png',dpi=140);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(13,8),sharex=True)
    for (_,trace),label,color in zip(runs,LABELS,('#2166ac','#d6604d','#7b3294')):
        t=[r['time_s'] for r in trace]
        axes[0].plot(t,[r['position_change_m']*100 for r in trace],label=label,color=color)
        axes[1].plot(t,[r['rotation_change_deg'] for r in trace],label=label,color=color)
    for ax in axes:ax.grid(alpha=.25);ax.axvline(2,color='grey',linestyle=':',label=None)
    axes[0].set_ylabel('초기 actor-root 대비 이동 (cm)');axes[1].set_ylabel('초기 대비 최단 회전 차이 (°)');axes[1].set_xlabel('시뮬레이션 시간 (초)')
    axes[0].legend(loc='upper left');fig.suptitle('5초 자유 기타 변화 — 원자료151표본씩, 상태 고정·손 부착 없음',fontsize=16)
    fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(out/'pose_changes.png',dpi=150);plt.close(fig)
    after={p:sha(p) for p in hashes};assert after==hashes
    save(out/'inputs_after.json',after);print(json.dumps(summaries,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
