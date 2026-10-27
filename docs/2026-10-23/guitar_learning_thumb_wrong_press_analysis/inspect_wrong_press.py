from pathlib import Path
import json,numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET
base=Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/evaluations')
result=[]
for label,folder in [(0,'initial'),(500,'update_0500'),(1000,'update_1000'),(1500,'update_1500'),(2000,'final')]:
 p=base/f'evaluation_fixed_{folder}_1024'
 targets=json.loads((p/'targets.json').read_text());dur=np.array([t['end_s']-t['onset_s'] for t in targets]); fingers=np.array([t['finger'] for t in targets])
 groups={k:[] for k in ['all','safe']}
 for line in (p/'first_episodes.jsonl').open():
  d=json.loads(line); groups['all'].append(d)
  if d['left_curriculum']['full_safe']:groups['safe'].append(d)
 row={'updates':label,'groups':{}}
 for key,eps in groups.items():
  vals={k:np.array([e['left_note_ledger']['values'][k] for e in eps]) for k in ['wrong','clean','missing','left','higher_time','lower_time','assignment_time','exposure_time']}
  audible=np.array([[max(min(t['end_s'],e['task_time_s'])-t['onset_s'],0) for t in targets] for e in eps])
  wrong=vals['wrong'];left=vals['left'].astype(bool)
  # Trapezoid wrong/missing integration and both-endpoint clean can leave at most half physics tick per candidate transition.
  assert (wrong>=-1e-9).all() and (wrong<=audible+1e-7).all()
  g={'episodes':len(eps),'wrong_episodes':int((wrong.sum(-1)>1e-9).sum()),'wrong_note_events':int((wrong>1e-9).sum()),'wrong_target_seconds':float(wrong.sum()),'observed_audible_target_seconds':float(audible.sum()),'wrong_audible_fraction':float(wrong.sum()/audible.sum()),'mean_wrong_s_per_episode':float(wrong.sum()/len(eps)),'success_notes':int(left.sum()),'success_notes_with_any_wrong':int((left & (wrong>1e-9)).sum()),'wrong_s_median_per_episode':float(np.median(wrong.sum(-1))),'wrong_s_p95_per_episode':float(np.quantile(wrong.sum(-1),.95)),'reward_wrong_mean':float(np.mean([e['reward_components']['song_wrong_press'] for e in eps])),'cause_seconds_prep_to_end':{k:float(vals[k].sum()) for k in ['higher_time','lower_time','assignment_time']},'by_target_finger':{str(f):{'wrong_s':float(wrong[:,fingers==f].sum()),'audible_s':float(audible[:,fingers==f].sum()),'wrong_events':int((wrong[:,fingers==f]>1e-9).sum())} for f in range(1,5)}}
  row['groups'][key]=g
 result.append(row)
print(json.dumps(result,indent=2))
Path('/tmp/v8_wrong_counts.json').write_text(json.dumps(result,indent=2)+'\n')
xmlpath=Path('guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml').resolve();root=ET.parse(xmlpath).getroot();folder=xmlpath.parent/root.find('compiler').get('meshdir','.')
meshes={m.get('name'):m for m in root.findall('./asset/mesh')}
for geom in root.findall('./worldbody/body/geom'):
 if geom.get('mesh') not in ('guitar_neck1','guitar_neck2'):continue
 m=meshes[geom.get('mesh')];v=np.array([[float(x) for x in line.split()[1:4]] for line in (folder/m.get('file')).read_text().splitlines() if line.startswith('v ')]);v*=np.fromstring(m.get('scale','1 1 1'),sep=' ')
 q=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ');v=Rotation.from_quat(np.r_[q[1:],q[:1]]).apply(v)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
 h=ConvexHull(v); rear=h.equations[:,2]<-.5
 print('HULL',m.get('name'),v.shape,len(h.simplices),'bounds',v.min(0),v.max(0),'rear facets',rear.sum(),'planes',np.unique(np.round(h.equations[rear],7),axis=0))
