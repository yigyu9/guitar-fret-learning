"""Native two-worker independence and five-second progression, without graphics."""
import argparse,hashlib,json,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    from .dual_music_scene_v1 import DualMusicScene
    from .parallel_cpu_env_v1 import ParallelCPUEnvironment
    from .run_deadline_training_v9 import input_closure
    import numpy as np
    closure=input_closure();pool=ParallelCPUEnvironment(2,a.out/'workers');failure=None
    try:
        obs=pool.reset();assert np.array_equal(obs[0],obs[1]);abi=pool.abi()
        initial_states=pool.snapshots();assert initial_states[0]['native_state']==initial_states[1]['native_state']
        assert all(r['creation_calls'][0]['forwarded_graphics_device_id']==-1 and not r['render_lookup_counts'] for r in pool.metadata['parallel_collection']['graphics_resource_policy_by_worker'])
        actions=np.zeros((2,81),dtype=np.float32);actions[1,abi['groups'].index('arm')]=.2
        start=time.monotonic()
        for step in range(300):
            obs,reward,terminated,truncated,info=pool.step(actions)
            assert not terminated.any() and not truncated.any()
            assert np.isfinite(obs).all() and np.isfinite(reward).all()
            if step%60==0:print('native_parallel_control_step',step+1,flush=True)
        assert not np.array_equal(obs[0],obs[1])
        final_states=pool.snapshots()
        q=np.array([[r['pos'] for r in value['native_state']['human_dof_states']] for value in final_states])
        assert np.max(np.abs(q[0]-q[1]))>0
        assert all(not r['forbidden_calls'] and r['physics_steps']==1200 and r['strap_force_calls']==13*1200 for r in final_states)
        record={'completed':True,'workers':2,'control_steps_per_worker':300,'physics_steps_per_worker':1200,
                'simulation_seconds_per_worker':5.,'wall_seconds':time.monotonic()-start,
                'equal_initial_observations':True,'different_final_observations_under_distinct_actions':True,
                'initial_native_states_exact':True,'initial_states':initial_states,'final_states':final_states,
                'maximum_actual_q_difference_rad':float(np.max(np.abs(q[0]-q[1]))),
                'maximum_final_observation_difference':float(np.max(np.abs(obs[0]-obs[1]))),
                'metadata':pool.metadata,'last_info':pool.last_info,'input_sha256':closure,
                'inputs_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in closure.items()),
                'scope':'two graphics-free independent scenes; full checkpoint video is a separate smoke evaluation'}
        assert record['inputs_unchanged']
        with (a.out/'report.json').open('x') as f:json.dump(record,f,indent=2,allow_nan=False)
    finally:pool.close()
if __name__=='__main__':main()
