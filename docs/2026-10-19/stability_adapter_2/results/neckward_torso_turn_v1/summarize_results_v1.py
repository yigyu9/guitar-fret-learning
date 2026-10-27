"""Collect completed free-guitar diagnostics and actual torso comparisons."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 paths=[Path(__file__).resolve(),P/'analysis_v1/static_neckyaw12/verification.json',P/'analysis_v2/elbow_neckyaw12/verification.json',P/'torso_posture_v2.json',P/'contact_region_v1.json',P/'elbow_comparison_v1.json'];inputs={str(p):sha(p)for p in paths};cases={}
 for p in paths[1:3]:
  v=read(p);assert v['passed'];cases.update(v['cases'])
 post=read(paths[3]);reg=read(paths[4]);comparison=read(paths[5]);assert comparison['small_elbow_influence_diagnostic_passed']
 for n,c in cases.items():
  c['actual_torso_posture']=post['cases'][n];c['actual_region35_contact_samples']=reg['cases'][n]['declared_region_contact_samples'];c['native_contact_fraction_min_max']=([min(x['human_segment_fraction_clipped']for r in reg['cases'][n]['rows']for x in r['contacts']),max(x['human_segment_fraction_clipped']for r in reg['cases'][n]['rows']for x in r['contacts'])]if reg['cases'][n]['upper_arm_any_contact_samples']else None)
 assert all(sha(Path(p))==h for p,h in inputs.items());save(P/'result_summary_v1.json',{'input_sha256':inputs,'cases':cases,'elbow_comparison':comparison,'previous_stable_actual_torso':post['cases']['static_cradle'],'scope':'two completed5s diagnostics; torso yaw/bend targets vs actualanatomicalaxes separate, small-elbow cycle only, no musical or naturalness/repeatability certification'});print(json.dumps({n:{k:c[k]for k in ['final_body_bbox_centre_change_mm','final_rotation_change_deg','elbow_actual_2p5_to_5s_range_deg','endpoints','actual_region35_contact_samples','native_contact_fraction_min_max']}for n,c in cases.items()},indent=2))
if __name__=='__main__':main()
