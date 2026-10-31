"""Release the declared same-initial elbow diagnostic only after its stationary gate."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 summary=P/'result_summary_v1.json';static=P/'diagnostic_candidate_v1/config_static.json';s=read(summary)['cases']['static_cradle'];assert s['temporary_stationary_motion_entry_gate'] and s['elbow_command_amplitude_deg']==0;config=read(static);candidate=Path(config['initial_candidate']);assert sha(candidate)==config['initial_candidate_sha256'];inputs={str(p):sha(p)for p in [Path(__file__).resolve(),R/'stability_adapter_2/AXILLA_ELBOW_ISOLATION_PLAN_V3.md',summary,static,candidate,P/'analysis_v3/static_cradle/verification.json',P/'contact_region_v1.json']};out=P/'motion_candidate_v1';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
 save(out/'config_motion.json',{**config,'elbow_motion_amplitude_rad':float(np.deg2rad(2)),'stationary_gate_summary':str(summary),'stationary_gate_summary_sha256':sha(summary)})
 save(out/'gate_release.json',{'input_sha256':inputs,'stationary_gate_passed':True,'stationary_body_centre_change_mm':s['final_body_bbox_centre_change_mm'],'stationary_rotation_change_deg':s['final_rotation_change_deg'],'candidate_unchanged_exact':True,'change_only':'elbow scalar R_Elbow_y finite PD target sinusoid2deg, .5Hz, 2.5..4.5s','scope':'single diagnostic, not repeatability or musical skill success'});assert all(sha(Path(p))==h for p,h in inputs.items())
if __name__=='__main__':main()
