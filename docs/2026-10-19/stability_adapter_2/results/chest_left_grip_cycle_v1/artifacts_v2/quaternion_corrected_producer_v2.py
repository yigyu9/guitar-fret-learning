from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1'
ART=P/'artifacts_v2';V=ROOT/'docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1'
N=P/'native_v1';M=N/'media';A1=P/'artifacts_v1'
FRAMES=A1/'hands_cycle_four_moments_v1.png'
VIDEOS=[V/f'{name}.mp4' for name in ('whole_body','hands','chest_arm_close')]
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def paths():
 a=read(P/'analysis_v1.json')
 ps={Path(x) for x in a['input_sha256']}
 ps.update([P/'analysis_v1.json',P/'log_scope_notes_v1.json',N/'initial_values.json',M/'physics_endpoint_contacts.json',
            ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/diagnostic_v1/diagnostic.json',
            A1/'README_v2.md',A1/'motion_samples_240Hz_v1.csv',A1/'guitar_motion_240Hz_v1.png',FRAMES,
            A1/'copy_manifest_v1.json',V/'README.md',*VIDEOS])
 return sorted(ps)
def main():
 before=read(ART/'artifact_before_v2.json')
 expected={x['path']:x['sha256'] for x in before['inputs']}
 if before['producer']['sha256']!=sha(ART/'quaternion_corrected_producer_v2.py'):raise SystemExit('producer changed after input pin')
 if {str(p) for p in paths()}!=set(expected):raise SystemExit('pre-pin input set differs')
 if any(sha(p)!=h for p,h in expected.items()):raise SystemExit('pinned input changed before run')
 analysis=read(P/'analysis_v1.json')['measured']; initial=read(N/'initial_values.json')['native_initial_state']; rows=read(M/'physics_endpoint_contacts.json')['rows']
 diagnostic=read(ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/diagnostic_v1/diagnostic.json')
 local_center=np.asarray(diagnostic['guitar_centre_G_m'],dtype=float)
 def pose(state):
  p=state['pose']['p'];q=state['pose']['r']
  return np.array([p['x'],p['y'],p['z']],float),np.array([q['x'],q['y'],q['z'],q['w']],float)
 states=[initial['guitar_body_states'][0]]+[r['guitar_body_states']['guitar'] for r in rows]
 roots=np.array([pose(s)[0] for s in states])
 rawq=np.array([pose(s)[1] for s in states])
 rotations=Rotation.from_quat(rawq)  # SciPy normalizes each native quaternion.
 centres=roots+rotations.apply(local_center)
 rel=rotations[0].inv()*rotations
 times=np.arange(len(states),dtype=float)/240.0
 bb=np.linalg.norm(centres-centres[0],axis=1)*1000.0
 so3=np.rad2deg(rel.magnitude())
 # Re-read generated rows and compare every point against the independently recomputed SciPy series.
 outcsv=ART/'motion_samples_240Hz_v2.csv'
 with outcsv.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['time_s','guitar_BB_center_displacement_from_initial_mm','guitar_SO3_rotation_from_initial_deg'])
  w.writerows(zip(times,bb,so3))
 with outcsv.open(newline='') as f: generated=list(csv.DictReader(f))
 got=np.array([[float(r['time_s']),float(r['guitar_BB_center_displacement_from_initial_mm']),float(r['guitar_SO3_rotation_from_initial_deg'])] for r in generated])
 ref=np.column_stack([times,bb,so3])
 errors=np.abs(got-ref)
 if len(got)!=3841 or errors[:,0].max()>1e-12 or errors[:,1:].max()>1e-10:raise SystemExit(f'pointwise CSV SciPy validation failed: {errors.max(axis=0)}')
 maxbb=float(bb.max());maxso=float(so3.max())
 if abs(maxbb-analysis['maximum_body_from_initial_mm'])>1e-8 or abs(maxso-analysis['maximum_rotation_from_initial_deg'])>1e-8:
  raise SystemExit(f'global maxima disagree with authoritative analysis: {maxbb}, {maxso}')
 # Show complete native trace with phase boundaries; same SciPy-derived values as CSV.
 fp=FontProperties(fname=FONT) if Path(FONT).exists() else None
 fig,axs=plt.subplots(2,1,figsize=(10,6.4),sharex=True)
 axs[0].plot(times,bb,color='#0072B2',lw=1.2);axs[0].set_ylabel('기타 BB 중심 변위 (mm)',fontproperties=fp)
 axs[1].plot(times,so3,color='#D55E00',lw=1.2);axs[1].set_ylabel('SO(3) 회전거리 (deg)',fontproperties=fp);axs[1].set_xlabel('시간 (s)',fontproperties=fp)
 for ax in axs:
  ax.set_xlim(0,16);ax.grid(True,alpha=.25)
  for x in [2,3,4.5,6,7,8.5,10,11.5,13]:ax.axvline(x,color='gray',lw=.55,alpha=.35)
 fig.tight_layout();plot=ART/'guitar_motion_240Hz_v2.png';fig.savefig(plot,dpi=180);plt.close(fig)
 analysis_readme=ART/'README.md'
 analysis_readme.write_text(f'''# 왼손 기타 사이클 — 정규화된 자세 계산

이 요약은 [native cycle 측정](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/analysis_v1.json>)과 실제 native 영상·프레임을 설명한다. 16초, 3,840 physics step 실행은 완료됐고 기타는 자유 동역학이었다. 이전 V1 CSV/그래프는 native quaternion을 단위화하지 않고 회전을 계산해 pointwise 자세값에 오차가 있었다. V2에서는 SciPy `Rotation.from_quat`으로 모든 endpoint quaternion을 정규화한 뒤 `center_W = actor_position_W + rotation.apply(guitar_centre_G)` 및 `SO(3) = (R0.inv() * Ri).magnitude()`로 재계산했다. [새 CSV](./motion_samples_240Hz_v2.csv)의 3,841개 시점을 SciPy 기준과 각각 비교했고 최대 pointwise 오차는 0이다. 최대 BB 중심 변위는 {maxbb:.10f} mm, 최대 SO(3)는 {maxso:.10f}°로 분석기 결과와 일치한다.

비교 그림과 세 native 영상은 바이트가 보존된 기존 산출물을 직접 연결한다: [네 시점 손 프레임](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/hands_cycle_four_moments_v1.png>), [전신 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/whole_body.mp4>), [손 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/hands.mp4>), [가슴·팔 확대 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/chest_arm_close.mp4>).

![SciPy quaternion 정규화로 재계산한 240 Hz 기타 BB 중심 변위와 SO(3)]({plot})

V1 그래프·CSV는 이 quaternion 정규화 오류 범위에서 superseded 처리한다. native 물리 실행, endpoint 원자료, 16초 영상과 접촉분석은 변경되지 않았다. 입력·도구 SHA 및 pointwise 검사 결과는 [V2 manifest](./copy_manifest_v2.json)에 기록했다.
''',encoding='utf-8')
 index=V/'README_v3.md'
 index.write_text(f'''# 왼손 잡기·놓기 사이클 native 영상

16초 native Isaac Gym 실행의 세 영상은 기존 바이트 보존본을 직접 연결한다. 오른손 타현은 꺼져 있다. 수정된 quaternion 정규화 기반 기타 자세 그래프와 전체 240 Hz 표는 [V2 요약]({analysis_readme})에서 확인한다. V1 quaternion 기반 그래프/CSV는 자세 계산 오류 때문에 superseded 됐으며 native 실행과 영상은 영향받지 않았다.

## 전신

![전신 native cycle]({VIDEOS[0]})

## 손

![손 native cycle]({VIDEOS[1]})

## 가슴·팔 확대

![가슴과 팔 native cycle]({VIDEOS[2]})
''',encoding='utf-8')
 # Revalidate all pinned sources after producing the new files.
 after={str(p):sha(p) for p in paths()}
 if any(after[p]!=h for p,h in expected.items()):raise SystemExit('pinned input changed during generation')
 outputs=[outcsv,plot,analysis_readme,index]
 manifest={'schema':'chest_left_grip_cycle_quaternion_corrected_manifest_v2','producer':{'path':str(ART/'quaternion_corrected_producer_v2.py'),'sha256':sha(ART/'quaternion_corrected_producer_v2.py')},'scipy_version':scipy.__version__,'inputs_before':before['inputs'],'inputs_after':[{'path':p,'sha256':h} for p,h in after.items()],'all_inputs_unchanged':True,'pointwise_validation':{'rows':len(got),'reference':'independent SciPy Rotation.from_quat series recomputation from pinned native endpoints','max_abs_error_time_s':float(errors[:,0].max()),'max_abs_error_BB_mm':float(errors[:,1].max()),'max_abs_error_SO3_deg':float(errors[:,2].max()),'passed':True},'analysis_maxima':{'BB_mm':maxbb,'SO3_deg':maxso},'derived_artifacts':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
 (ART/'copy_manifest_v2.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'scipy':scipy.__version__,'rows':len(got),'maxima':[maxbb,maxso],'pointwise_error':errors.max(axis=0).tolist(),'inputs_unchanged':True}))
if __name__=='__main__':main()
