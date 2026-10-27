"""Read imported actor surface properties without advancing physics."""
from pathlib import Path
from .initial_pose_noise_v1 import save,sha
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/material_inspection_v1'

def main():
    from isaacgym import gymapi
    import numpy as np
    assets={'human':ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml','guitar':ROOT/'stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml'}
    files=[Path(__file__).resolve(),ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V14.md',ROOT/'stability_adapter_2/environment.py',ROOT/'stability_adapter_2/self_collision_environment.py',*assets.values()];inputs={str(p):sha(p)for p in files};P.mkdir(exist_ok=False);save(P/'inputs_before.json',inputs)
    gym=gymapi.acquire_gym();params=gymapi.SimParams();params.dt=1/240;params.up_axis=gymapi.UP_AXIS_Z;params.gravity=gymapi.Vec3(0,0,-9.81);params.use_gpu_pipeline=False;params.physx.use_gpu=False
    sim=gym.create_sim(0,-1,gymapi.SIM_PHYSX,params)
    if sim is None:raise RuntimeError('material readback sim failed')
    result={}
    try:
        env=gym.create_env(sim,gymapi.Vec3(-1,-1,-1),gymapi.Vec3(1,1,1),1)
        for name,path in assets.items():
            options=gymapi.AssetOptions();options.fix_base_link=name=='human';options.collapse_fixed_joints=False;asset=gym.load_asset(sim,str(path.parent),path.name,options)
            if asset is None:raise RuntimeError('material readback asset failed')
            actor=gym.create_actor(env,asset,gymapi.Transform(),name,0,0);names=list(gym.get_actor_rigid_body_names(env,actor));ranges=gym.get_actor_rigid_body_shape_indices(env,actor);props=gym.get_actor_rigid_shape_properties(env,actor)
            result[name]={body:[{field:float(getattr(props[j],field))for field in ('friction','rolling_friction','torsion_friction','restitution','contact_offset','rest_offset')}for j in range(span.start,span.start+span.count)]for body,span in zip(names,ranges)}
            assert all(np.isfinite(list(row.values())).all()for rows in result[name].values()for row in rows)
    finally:gym.destroy_sim(sim)
    assert all(sha(p)==h for p,h in inputs.items());save(P/'materials.json',{'actors':result,'physics_steps':0,'surface_setters':0,'input_sha256':inputs,'scope':'native imported actor materials before existing scene filter/contact-offset overrides; those source paths do not override friction; not measured contact coefficient or completed rollout'})
    print({name:{body:rows for body,rows in fields.items()if body in ('L_Hip','R_Hip','Chest','R_Shoulder','G:body')}for name,fields in result.items()})

if __name__=='__main__':main()
