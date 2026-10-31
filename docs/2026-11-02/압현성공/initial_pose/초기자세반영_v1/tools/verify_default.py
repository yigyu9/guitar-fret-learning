"""수정한 기본 경로를 그대로 써서 초기복원·목표·5초유지·부분리셋을 검사한다."""
import json
from pathlib import Path
import isaacgym
import torch
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.control import BatchedController
from guitar_learning.runtime.prepared_reset_v1 import LEFT_INITIAL_POSE
OUT=Path(__file__).resolve().parents[1]
torch.set_num_threads(1)
pose=json.loads(LEFT_INITIAL_POSE.read_text())
scene=GpuScene(4,'left',out=OUT/'default_scene')
try:
    control=BatchedController(scene);sample=scene.snapshot();control.reset([0,1,2,3],sample)
    expected=torch.tensor(pose['q105_rad'],device=scene.device,dtype=sample['q'].dtype)
    target=torch.tensor(pose['target105_rad'],device=scene.device,dtype=sample['q'].dtype)
    assert torch.allclose(sample['q'],expected[None],atol=2e-6,rtol=0)
    assert torch.equal(control.reference,target)
    initial_max_error=float((sample['q']-expected).abs().max())
    action=torch.zeros((4,39),device=scene.device)
    for tick in range(300):
        desired=control.targets(action,sample)
        for sub in range(4):
            sample=scene.step(desired,control.efforts(sample))
            assert all(bool(torch.isfinite(sample[k]).all()) for k in ('q','qd','body_state'))
    before=sample['q'].clone();sample=scene.reset([1,3]);control.reset([1,3],sample)
    assert torch.allclose(sample['q'][[1,3]],expected[None],atol=2e-6,rtol=0)
    assert torch.equal(sample['q'][[0,2]],before[[0,2]])
    report=dict(initial_pose=scene.metadata['initial_pose'],num_envs=4,physics_steps=scene.physics_steps,
        initial_max_q_error_rad=initial_max_error,zero_action_reference_verified=True,
        finite_5s=True,partial_reset_verified=True,unselected_rows_preserved=True)
    (OUT/'default_reset_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
finally:scene.close()
