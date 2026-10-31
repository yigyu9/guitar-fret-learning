"""Add legacy full-upper-arm witness aliases without changing physical initial values."""
from pathlib import Path
from .initial_pose_noise_v1 import read,save,sha
from .diagnose_user_guided_no_left_v1 import A,P


def main():
    out=P/'package_v4';out.mkdir(exist_ok=False)
    paths=[Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_PACKAGE_V4_PLAN.md']+list(A.glob('*.py'))+[p for p in (P/'search_v3').rglob('*') if p.is_file()]
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs);selected=[]
    for label in ('upper50','upper65'):
        old=P/'search_v3'/label;candidate=read(old/'candidate.json');config=read(old/'config.json');row=candidate['right_block_cradle']
        assert row['accepted_for_native'];upper=row['full_upper_arm_witness'];newrow={**row,'proximal_upper_arm45_witness':upper,'proximal_upper_arm65_witness':upper,'legacy_key_note':'30/45/65 aliases of the full rigid upper-arm witness; numeric key is not the selected fraction'}
        new={**candidate,'right_block_cradle':newrow,'body_side_lean_axilla':newrow,'right_thigh_waist':newrow}
        for key in ('joint_angles_rad','position_W_m','quaternion_xyzw','predicted_human_poses','predicted_guitar_body_states'):assert new[key]==candidate[key]
        folder=out/label;folder.mkdir();save(folder/'candidate.json',new);save(folder/'config.json',{**config,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')});selected.append({'label':label,'config':str(folder/'config.json'),'physical_initial_values_exact':True})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'package.json',{'input_sha256':inputs,'selected':selected,'geometry_solver_proposals':0,'scope':'metadata aliases only; search_v3 values exact; prior zero-step constructor failure preserved'})

if __name__=='__main__':main()
