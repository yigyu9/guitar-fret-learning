"""Record human motor-reference tracking errors and virtual request saturation."""
from pathlib import Path
import json,hashlib,numpy as np
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[Path(__file__).resolve()]+[P/x/'media/axilla_effort_rows.json'for x in ('native_v2/static_neckyaw26','native_v3/follow_neckyaw26')];inputs={str(p):sha(p)for p in files};cases={}
 for p in files[1:]:
  rows=read(p)['rows'];examples=[]
  for i in (0,120,240,480,720,1199):
   r=rows[i];error=np.array(r['desired_motor_point_W_m'])-np.array(r['motor_point_W_m']);examples.append({'time_before_step_s':i/240,'target_minus_human_point_W_mm':(error*1000).tolist(),'error_norm_mm':float(np.linalg.norm(error)*1000),'virtual_request_norm_N':float(np.linalg.norm(r['point_force_request_W_N']))})
  cases[p.parents[1].name]={'examples':examples,'request_at_cap10_samples':int(sum(np.linalg.norm(r['point_force_request_W_N'])>=10-1e-9 for r in rows)),'scope':'human motor reference and requested virtual point force; not measured contact force or established causal diagnosis'}
 assert all(sha(Path(p))==h for p,h in inputs.items())
 with (P/'upper_point_tracking_probe_v2.json').open('x')as f:json.dump({'input_sha256':inputs,'cases':cases},f,ensure_ascii=False,indent=2,allow_nan=False)
 print(json.dumps(cases,indent=2))
if __name__=='__main__':main()
