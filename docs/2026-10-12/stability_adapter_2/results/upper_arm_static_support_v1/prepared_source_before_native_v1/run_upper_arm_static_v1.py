"""Five-second constant-target native hold: no music actor, policy or learning."""
import argparse
from pathlib import Path
from unittest.mock import patch
from .initial_pose_noise_v1 import read,save,sha,pose

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    from .dual_music_scene_v1 import DualMusicScene
    from . import dual_music_scene_v1 as dual
    from .deadline_native_v4 import _strap_scene_class,REST_LENGTH
    from .environment_contract_v1 import EnvironmentContract
    from .run_joint_hold import native_state
    from .strap_trial_recording import StrapTrialRecording
    from .upper_arm_static_geometry_v1 import calibrated_upper_fk,source_audit
    from .build_fixed_lower_asset import LOWER_BODIES
    from .native_contacts import body_names,read_contacts
    import numpy as np
    from scipy.spatial.transform import Rotation
    from .trial_settings import source_hashes
    closure=source_hashes();
    for path in Path(__file__).resolve().parent.glob('*.py'):closure[str(path)]=sha(path)
    cfg=read(a.config);closure[str(a.config)]=sha(a.config);closure[cfg['initial_candidate']]=sha(cfg['initial_candidate'])
    original=EnvironmentContract();closure.update(original.inputs)
    for path in Path(__file__).with_name('assets').glob('*'):
        if path.is_file():closure[str(path)]=sha(path)
    save(a.out/'attempt.json',{'input_sha256':closure,'music_actors':0,'policy_calls':0,'checkpoint_loads':0,'initial_noise':False,'duration_physics_s':5,'strap_enabled':True,'strap_rest_length_m':REST_LENGTH,'target_rule':'initial q_ref constant without preload'})
    scene=None;recorder=None;failure=None;rows=[];contacts=[]
    try:
        with patch.object(dual,'EnvironmentContract',lambda:EnvironmentContract(a.config)):
            scene=_strap_scene_class(True,True)(5.)
        initial=native_state(scene);names=scene.human_bodies;fixed=[names.index(n) for n in ('Pelvis',)+LOWER_BODIES];qref=scene.contract.q_ref;desired=qref.copy()
        fk,parents=calibrated_upper_fk(scene.names,names,initial,qref);audit=source_audit(initial,names,parents)
        if not audit['source_clear']:raise RuntimeError('actual native initial source overlap')
        before=read(original.config['native_reference'])['native_initial_state']
        if any(initial['human_body_states'][i]!=before['human_body_states'][i] for i in fixed):raise RuntimeError('fixed root/lower initial differs')
        gp0,gr0=pose(initial['guitar_body_states'][0]);chest0=pose(initial['human_body_states'][names.index('Chest')])[1]
        expected=scene.contract.candidate['predicted_human_poses'];errors={n:{'position_error_m':float(np.linalg.norm(p-np.array(expected[n]['p']))),'orientation_error_deg':float(np.rad2deg((Rotation.from_quat(expected[n]['q']).inv()*r).magnitude()))} for n,(p,r) in fk(qref).items()}
        if max(v['position_error_m'] for v in errors.values())>1e-5 or max(v['orientation_error_deg'] for v in errors.values())>.01:raise RuntimeError('candidate FK differs from actual native initialization')
        save(a.out/'initial_values.json',{'native_initial_state':initial,'joint_names':scene.names,'human_body_names':names,'q_ref_rad':qref.tolist(),'fixed_target_rad':desired.tolist(),'target_rule':'exact initial q_ref held; no preload correction','PD_properties':{k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names},'source_audit':audit,'native_FK_error':errors,'strap_initial':scene.strap_initial,'initial_state_write_calls':scene.initial_state_write_calls})
        recorder=StrapTrialRecording(scene,a.out/'media');recorder.capture();mapping=body_names(scene.gym,scene.env)
        def sample():
            state=native_state(scene);q=np.array([r['pos'] for r in state['human_dof_states']]);v=np.array([r['vel'] for r in state['human_dof_states']]);gp,gr=pose(state['guitar_body_states'][0]);chest=pose(state['human_body_states'][names.index('Chest')])[1]
            if not np.isfinite(np.r_[q,v,gp,gr.as_quat()]).all() or abs(v).max()>50:raise RuntimeError('nonfinite/unsafe state')
            if any(state['human_body_states'][i]!=initial['human_body_states'][i] for i in fixed) or scene.forbidden_calls:raise RuntimeError('fixed body or forbidden API')
            rows.append({'physics_step':scene.steps,'time_s':scene.steps/240,'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'position_change_m':float(np.linalg.norm(gp-gp0)),'rotation_change_deg':float(np.rad2deg((gr0.inv()*gr).magnitude())),'Chest_change_deg':float(np.rad2deg((chest0.inv()*chest).magnitude())),'q_rad':q.tolist(),'qdot_rad_s':v.tolist(),'submitted_target_rad':scene.target.tolist()})
        sample()
        for tick in range(300):
            contacts.append({'before_control':tick,'physics_step':scene.steps,'contacts':read_contacts(scene.gym,scene.env,mapping)})
            action=(desired-scene.contract.mid)/scene.contract.half;scene.step(np.clip(action,-1,1));sample()
            if scene.steps%recorder.interval==0:recorder.capture()
        videos=recorder.encode()
        save(a.out/'report.json',{'completed':True,'physics_steps':scene.steps,'controls':300,'physics_seconds':scene.steps/240,'music_actors':0,'policy_calls':0,'checkpoint_loads':0,'forbidden_calls':scene.forbidden_calls,'strap_force_calls':scene.gym.allowed_calls,'initial_state_write_calls':scene.initial_state_write_calls,'rows':rows,'videos':videos,'source_audit':audit,'scope':'constant PD target static-hold diagnostic; contact raw lambda not Newton force'})
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error)}
        if recorder is not None:recorder.encode()
        save(a.out/'failure.json',failure);raise
    finally:
        save(a.out/'trace.json',rows);save(a.out/'contacts.json',contacts)
        if scene is not None:scene.close()
    if any(sha(path)!=h for path,h in closure.items()):raise AssertionError('consumed input changed')
    save(a.out/'inputs_verified.json',{'unchanged':True,'input_count':len(closure)})
if __name__=='__main__':main()
