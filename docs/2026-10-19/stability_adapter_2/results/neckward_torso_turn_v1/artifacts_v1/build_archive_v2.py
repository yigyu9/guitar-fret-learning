from pathlib import Path
import hashlib, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1')
A=P/'artifacts_v1'
OUT=A/'torso_posture_old_new_traces_v2.png'
README=A/'README_V2.md'
PROV=A/'provenance_v2.json'
PRODUCER=A/'build_archive_v2.py'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
INPUTS=[A/'README_V1.md', A/'provenance_v1.json', P/'torso_posture_v2.json',
        P/'search_v1/bend2_neckyaw12/candidate.json', FONT]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def stat(p): return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
before={str(p):stat(p) for p in INPUTS}
d=json.loads((P/'torso_posture_v2.json').read_text())
cand=json.loads((P/'search_v1/bend2_neckyaw12/candidate.json').read_text())
assert len(d['cases']['static_cradle']['trace'])==1201
assert len(d['cases']['static_neckyaw12']['trace'])==1201
# chart: two true native measured world-coordinate time traces; legend stays outside axes.
font_manager.fontManager.addfont(str(FONT))
plt.rcParams['font.family']=font_manager.FontProperties(fname=str(FONT)).get_name()
plt.rcParams['axes.unicode_minus']=False
fig,axs=plt.subplots(2,1,figsize=(12,8),sharex=True)
colors={'static_cradle':'#315a9a','static_neckyaw12':'#bd4b36'}
labels={'static_cradle':'이전 기준 · static_cradle','static_neckyaw12':'새 조건 · static_neckyaw12'}
for ax,key,field,title in [(axs[0],None,'chest_to_neck_forward_inclination_deg','Chest–Neck 전방 기울기'),(axs[1],None,'chest_facing_yaw_from_guitar_front_deg','Chest heading')]:
 for case in ['static_cradle','static_neckyaw12']:
  tr=d['cases'][case]['trace']; x=[r['time_s'] for r in tr]; y=[r[field] for r in tr]
  ax.plot(x,y,label=labels[case],color=colors[case],lw=2)
 ax.set_ylabel('각도 (°)'); ax.set_title(title,loc='left',fontsize=13); ax.grid(True,alpha=.25)
 axs[1].set_xlabel('물리 시간 (s)')
axs[1].set_ylabel('각도 (°)')
handles,labels0=axs[0].get_legend_handles_labels()
fig.legend(handles,labels0,loc='upper center',bbox_to_anchor=(.5,.995),ncol=2,frameon=False)
fig.suptitle('실제 native 자세 trace · world 기준 측정',y=.955,fontsize=16)
fig.tight_layout(rect=[0,.02,1,.91])
fig.savefig(OUT,dpi=170,bbox_inches='tight')
plt.close(fig)

readme='''# Neckward torso turn · 보정본 V2\n\n이 문서는 V1을 보존한 채 잘못된 yaw 대상 표현과 측정 좌표 설명을 바로잡습니다. V1의 “guitar yaw 12°”는 잘못된 표기였습니다. source 목표는 몸통(Chest/Torso) world-Z yaw 12°를 neck 방향으로 요청한 것이며, 기타 quaternion은 초기값 그대로 유지됐습니다. 추가 forward bend는 2°이고, body-right 6°는 yaw 적용 전 몸통 world-goal 성분입니다. 이 source 목표값들은 scalar 관절 q가 아닙니다.\n\n![이전 기준과 새 static의 실제 native world 자세 시간 trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/torso_posture_old_new_traces_v2.png)\n\n위 그래프는 `torso_posture_v2.json`의 1201개 시점을 직접 그렸습니다. forward inclination은 native Chest frame의 원래 Chest–Neck 축을 transport해 얻은 world +Y 전방 기준 각도이고, heading은 world +Y에서 −X로 향하는 각도입니다. 따라서 이는 native world 자세 측정이지 scalar q, native frame 축 각도, 또는 source 목표값이 아닙니다. 이전 static과 새 static은 초기 상태가 달라 직접적인 동일 초기조건 비교가 아닙니다. 새 static과 elbow-motion은 초기값과 2.5초까지 exact하게 일치합니다.\n\n실제 final measured values (이전 static → 새 static): forward inclination 53.575657° → 48.347770°; heading 12.643226° → 22.198890° toward neck; total inclination 53.590252° → 48.762687°; side inclination 2.534570° → −10.951170°. 따라서 실제 자세가 “body-right 6°” 목표를 유지했다고 해석하지 않습니다.\n\n## 기존 캡처와 영상\n\nV1에서 검수된 캡처와 요약 그래프는 변경 없이 그대로 연결합니다.\n\n![이전 static 및 새 조건의 whole-body native 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/native_wholebody_old_new_timeline.png)\n\n![새 static의 초기 support view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_static_initial_support_view.png)\n\n![Elbow-motion 측정 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_elbow_motion_response.png)\n\n![이전 static과 새 static 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/old_vs_neckturn_static.mp4)\n\n![새 elbow-motion 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/neck_yaw_motion_whole_body.mp4)\n\nHands 영상은 왼손/넥 방향 카메라라 오른쪽 상완 접촉의 증거가 아닙니다. 세 native 모두 5초/1200 physics step 완료. 상완 접촉은 1169/1200, R_Hip 1193/1200, Head/왼팔/오른쪽 distal arm 0/1200; 선언된 support-region은 0/1200입니다. Source geometry 간격은 PhysX cooked clearance 인증이 아니며 raw lambda는 힘 측정이 아닙니다. 안정성·연주 성공 주장은 하지 않습니다.\n\n[이전 V1 문서(보존)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/README_V1.md) · [trace 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/torso_posture_v2.json) · [복사 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/INDEX_V1.md)\n'''
readme=readme.replace('/stability_adapter_2/docs/2026-10-19/stability_adapter_2/video/','/stability_adapter_2/video/')
README.write_text(readme)
# self-pin producer after creation, before/after verify consumed inputs
before_after={str(p):{'before':before[str(p)],'after':stat(p),'unchanged':before[str(p)]==stat(p)} for p in INPUTS}
assert all(v['unchanged'] for v in before_after.values())
prov={'task':'neckward torso turn V2 documentation and time trace only','physical_or_training_runs':0,'video_copies_or_reencodes':0,
 'correction':'V1 called torso world-Z yaw 12° a guitar yaw; guitar quaternion stayed unchanged. Body-right 6° is a pre-yaw world-goal component, not scalar q. Native posture metrics are measured in world coordinates from transported anatomical axes.',
 'inputs_before_after':before_after,'producer':{'path':str(PRODUCER),'sha256':sha(PRODUCER),'bytes':PRODUCER.stat().st_size},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [OUT,README]},
 'font':{'path':str(FONT),'sha256':sha(FONT)},'trace_points':{'static_cradle':1201,'static_neckyaw12':1201}}
PROV.write_text(json.dumps(prov,indent=2,ensure_ascii=False)+'\n')
