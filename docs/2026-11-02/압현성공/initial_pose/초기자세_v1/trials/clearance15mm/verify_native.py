"""새 에피소드 경계에서 손가락 대기 상태를 한 번 복원하고5초 유지한다."""
import copy
import json
from pathlib import Path
import sys
import numpy as np

OUT=Path(__file__).resolve().parents[1]


def main():
    import isaacgym
    import torch
    from guitar_learning.runtime import prepared_reset_v1 as prepared
    artifact=json.loads((OUT/'initial_pose.json').read_text())
    original=prepared.load_prepared_reset_contract
    contract=original();contract['state']=artifact['state'];contract['target105']=np.asarray(artifact['target105_rad'])
    # 새 진단 프로세스의 초기 로더만 바꾼다. 원파일과 실행 중 상태는 수정하지 않는다.
    prepared.load_prepared_reset_contract=lambda:copy.deepcopy(contract)
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    torch.set_num_threads(1)
    scene=GpuScene(1,'left',out=OUT/'native_scene')
    try:
        controller=BatchedController(scene);sample=scene.snapshot();controller.reset([0],sample)
        samples=[]
        def record():
            samples.append({k:sample[k][0].cpu().numpy().copy() for k in ('q','qd','body_state','contact_force','target')})
        record()
        action=torch.zeros((1,39),device=scene.device)
        for tick in range(300):
            target=controller.targets(action,sample)
            for sub in range(4):
                effort=controller.efforts(sample)
                if not bool(controller.diagnostics['valid'].all()):raise RuntimeError('유한 하체 제어 실패')
                sample=scene.step(target,effort)
                if not all(bool(torch.isfinite(sample[k]).all()) for k in ('q','qd','body_state','contact_force')):raise RuntimeError('비유한 상태')
            record()
        np.savez_compressed(OUT/'native_hold.npz',**{k:np.array([s[k] for s in samples]) for k in samples[0]})
        meta=dict(body_names=scene.body_names,joint_names=scene.names,human_body_names=scene.human_bodies,guitar_body_names=scene.guitar_bodies,physics_steps=scene.physics_steps,reset_calls=scene.reset_calls,hold_s=5.,sample_hz=60,source='actual Isaac Gym GPU PhysX',scope='diagnostic custom reset only; existing physical gains, constraints, gravity, collisions and finite lower support retained')
        (OUT/'native_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
        print('completed',scene.physics_steps,scene.reset_calls,flush=True)
    finally:
        scene.close();prepared.load_prepared_reset_contract=original


if __name__=='__main__':main()
