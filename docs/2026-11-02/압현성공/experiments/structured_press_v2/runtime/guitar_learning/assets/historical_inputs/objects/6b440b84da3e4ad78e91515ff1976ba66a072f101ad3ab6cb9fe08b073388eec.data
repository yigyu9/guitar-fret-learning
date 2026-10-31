"""Audit the new OM colliders at the saved, unchanged prior initial posture."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,ROOT
from .realistic_guitar_geometry_v1 import source_scene,source_audit


def main():
    result=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'
    reference=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/initial_values.json'
    asset=ROOT/'stability_adapter_2/assets/om_body_geometry_v2/guitar_asset.xml'
    paths=[Path(__file__).resolve(),reference,asset,asset.with_name('manifest.json')]
    inputs={str(p):sha(p) for p in paths}
    saved=read(reference);state=saved['native_initial_state'];names=saved['joint_names'];bodies=saved['human_body_names']
    _,parents=calibrated_upper_fk(names,bodies,state,np.asarray(saved['q_ref_rad']))
    scene=source_scene(state,bodies,asset);audit=source_audit(scene,parents)
    assert all(sha(p)==h for p,h in inputs.items())
    save(result/'initial_source_audit_v2.json',{'input_sha256':inputs,'audit':audit,'native_runs':0,'initial_pose_changes':0})
    print('source_clear',audit['source_clear'],'overlaps',len(audit['human_guitar_overlap']))


if __name__=='__main__':main()
