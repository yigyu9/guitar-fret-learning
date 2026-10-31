"""Preserve source V3 geometry and correct its legacy elbow/palm target labels."""
from pathlib import Path
import copy
from .initial_pose_noise_v1 import read,save,sha

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';P=R/'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1'

def main():
    source=P/'search_v3/search.json';anchors=[source,Path(__file__).resolve(),A/'RIGHT_ARM_WRAP_FORWARD_PLAN_V4.md',A/'initial_pose_noise_v1.py']
    inputs={str(p):sha(p) for p in anchors};raw=read(source)
    for path,digest in raw['input_sha256'].items():assert sha(path)==digest;inputs[path]=digest
    for selected in raw['selected']:
        config=Path(selected['config']);inputs[str(config)]=sha(config)
        candidate=Path(read(config)['initial_candidate']);inputs[str(candidate)]=sha(candidate)
    out=P/'search_v4';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
    rows=[];selected=[]
    for item in raw['selected']:
        config=read(item['config']);original=read(config['initial_candidate']);candidate=copy.deepcopy(original)
        row=copy.deepcopy(original['right_thigh_waist']);arm=row['arm_forward']
        arm['requested_palm_forward_mm']=arm['requested_elbow_forward_mm'];arm['requested_elbow_forward_mm']=0
        arm['elbow_forward_error_mm']=abs(arm['elbow_forward_mm']);row['metadata_source']=str(source)
        for key in ('right_thigh_waist','right_block_cradle','body_side_lean_axilla'):candidate[key]=copy.deepcopy(row)
        assert candidate['joint_angles_rad']==original['joint_angles_rad'] and candidate['predicted_human_poses']==original['predicted_human_poses']
        assert candidate['predicted_guitar_body_states']==original['predicted_guitar_body_states']
        folder=out/item['label'];folder.mkdir();save(folder/'candidate.json',candidate)
        save(folder/'config.json',{**config,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')})
        rows.append(row);selected.append({'label':item['label'],'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'geometry_solver_proposals':0,
         'geometry_source':str(source),'native_runs':0,'scope':'metadata-only packaging; exact V3 geometry/q/poses/support references; no new source geometry or simulation'})

if __name__=='__main__':main()
