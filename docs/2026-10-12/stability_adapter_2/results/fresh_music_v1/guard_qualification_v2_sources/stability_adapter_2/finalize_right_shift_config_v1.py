"""Remove inherited historical left-pose claims; canonical preparation values are unchanged."""
from pathlib import Path
from .search_right_shift_initial_v1 import A,P
from .initial_pose_noise_v1 import read,save,sha


def main():
    original=P/'search_v2/right10mm';out=P/'config_v1';out.mkdir(exist_ok=False)
    paths=[Path(__file__).resolve(),A/'RIGHT_SHIFT_INITIAL_PLAN_V2.md',original/'config.json',original/'candidate.json',P/'search_v2/search.json']
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    cfg=read(original/'config.json');old=read(original/'candidate.json');candidate={**old}
    row=old['right_shift_initial']
    candidate['left_neck_near']={'accepted_for_native':True,'station_G_m':row['station_G_m'],'front_z_G_m':row['front_z_G_m'],'face_measurements':row['face_measurements'],'source_audit':row['source_audit'],'scope':'current shifted preparation from canonical candidate joint_angles_rad; no inherited historical joint delta/frozen48/fit counts'}
    assert row['accepted_for_native'] and candidate['joint_angles_rad']==old['joint_angles_rad'] and candidate['predicted_guitar_body_states']==old['predicted_guitar_body_states'] and candidate['predicted_human_poses']==old['predicted_human_poses']
    save(out/'candidate.json',candidate);save(out/'config.json',{**cfg,'initial_candidate':str(out/'candidate.json'),'initial_candidate_sha256':sha(out/'candidate.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'report.json',{'input_sha256':inputs,'canonical_angles_guitar_human_poses_exact_to_source':True,'source_config':str(original/'config.json'),'config':str(out/'config.json'),'scope':'metadata cleanup only, not a new geometry or physics candidate'})


if __name__=='__main__':main()
