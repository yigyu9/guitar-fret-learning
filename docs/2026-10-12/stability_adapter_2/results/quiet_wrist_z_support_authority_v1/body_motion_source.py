"""Measure actual body9 motion from the completed wrist trials' saved states."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np

R=Path(__file__).resolve().parents[1];B=R/'docs/2026-10-12/stability_adapter_2/results'
P=B/'quiet_wrist_z_support_authority_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output=P/'body_motion.json';copy=P/'body_motion_source.py'
    assert not output.exists() and not copy.exists()
    folders=dict(baseline=B/'initial_middle3_alignment_v1/native',plus=P/'native/plus',minus=P/'native/minus')
    paths={Path(__file__).resolve()}|{f/n for f in folders.values() for n in ['initial_values.json','states.jsonl','controls.jsonl']}
    before={str(p):sha(p) for p in sorted(paths,key=str)}
    result={};checks={}
    for label,folder in folders.items():
        initial=json.loads((folder/'initial_values.json').read_text());names=initial['human_joint_names']
        joints=[body+'_'+axis for body in ['Torso','Spine','Chest'] for axis in 'xyz'];idx=[names.index(n) for n in joints]
        states=[json.loads(s) for s in (folder/'states.jsonl').read_text().splitlines()]
        controls=[json.loads(s) for s in (folder/'controls.jsonl').read_text().splitlines()]
        q=np.array([[v['pos'] for v in s['human_dof_states']] for s in states]);target=np.array([v['final_target_rad'] for v in controls])
        checks[label+'_ordered_finite_states']=len(states)==1201 and [s['physics_step'] for s in states]==list(range(1201)) and bool(np.isfinite(q).all())
        checks[label+'_all_body9_targets_held']=len(controls)==1200 and bool(np.array_equal(target[:,idx],np.tile(q[0,idx],(1200,1))))
        delta=q[:,idx]-q[0,idx];step,joint=np.unravel_index(np.argmax(abs(delta)),delta.shape)
        result[label]=dict(max_actual_body9_change_rad=float(abs(delta).max()),max_joint=joints[joint],max_step=int(step),end_max_change_rad=float(abs(delta[-1]).max()),per_joint_max_change_rad=dict(zip(joints,abs(delta).max(axis=0).tolist())))
    after={p:sha(p) for p in before};checks['inputs_unchanged']=before==after;assert all(checks.values())
    shutil.copy2(Path(__file__).resolve(),copy);assert sha(copy)==sha(Path(__file__).resolve())
    output.write_text(json.dumps(dict(checks=checks,summary=result,input_sha256_before=before,input_sha256_after=after,source_snapshot=str(copy),native_calls=0,physics_steps=0,scope='Actual body9 angular displacement from saved t0; held PD targets do not imply fixed actual torso'),indent=2)+'\n')
    print(json.dumps(dict(checks=len(checks),summary=result)))


if __name__=='__main__':main()
