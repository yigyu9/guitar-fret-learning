"""CPU capture regression and separate actual-model projection; no native scene."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace


def check(video):
    import numpy as np
    import torch
    from guitar_learning.tool.demonstration import render_finger_skill as native
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    schema='diagnostic.index_prefix_learning.v1';settings=dict(num_envs=128,song=dict(short_learning=dict(schema=schema)))
    payload=dict(updates=300,metadata=dict(schema=schema,input_pins={'synthetic':'header-only'},settings=settings))
    assert video.header(payload,300,settings,schema)==payload['metadata']
    for bad in (dict(payload,updates=150),dict(payload,metadata=dict(payload['metadata'],schema='guitar_learning.short_finger_learning.v2')),
                dict(payload,metadata=dict(payload['metadata'],input_pins={})),dict(payload,metadata=dict(payload['metadata'],settings=dict(settings,num_envs=4)))):
        try:video.header(bad,300,settings,schema)
        except ValueError:pass
        else:raise AssertionError('Wrong checkpoint header admitted')
    class Pool:
        def __init__(self):
            self.tick=0;self.resets=[];self.guard_rows=[];self.spec=dict(view=dict(duration_ticks=4));self.num_envs=128
            self.contract=dict(observation=dict(fields=['wrist_termination.active']))
            self.observation=dict(state=torch.zeros(128,1));self.environment=SimpleNamespace(action=torch.zeros(128,39),
                _score_time=lambda:torch.full((128,),self.tick/60+2.4497,dtype=torch.float64),candidate=torch.ones(128,67,dtype=torch.bool),
                wrong=torch.zeros(128,67,dtype=torch.bool),surface_distance=torch.ones(128,67)*.001,surface_height=torch.zeros(128,67),
                note=dict(released=torch.zeros(128,67,dtype=torch.bool),release_s=torch.zeros(128,67)))
            self.last_wrist_feedback=dict(active=torch.ones(128,dtype=torch.bool),pose_error_world=torch.zeros(128,6),requested_delta_rad=torch.zeros(128,12),
                requested_arm_rad=torch.zeros(128,12),candidate_arm_rad=torch.zeros(128,12),position_goal_G_m=torch.zeros(128,3),quaternion_goal_G_xyzw=torch.tensor([0.,0.,0.,1.]).expand(128,-1))
            self.scene=SimpleNamespace(sim='synthetic',envs=[0],gym=SimpleNamespace(step_graphics=lambda s:None,render_all_camera_sensors=lambda s:None,
                get_camera_image=lambda *a:np.zeros((720,1280,4),dtype=np.uint8)))
            self.scene.snapshot=lambda:dict(q=torch.zeros(128,105),qd=torch.zeros(128,105),target=torch.ones(128,105)*.2,
                body_state=torch.zeros(128,1,13),contact_force=torch.zeros(128,1,3),physics_step=torch.full((128,),self.tick*4,dtype=torch.long))
        def step(self,a):
            assert a.shape==(128,39) and a.dtype==torch.float32;self.tick+=1
            self.last_policy_action=a.clone();self.last_executed_action=a.clone();self.environment.action=a.clone()
            self.pending=dict(current_goal=torch.full((128,),4));self.guard_rows.append(dict(first_attempt=np.ones(128,bool),current_goal=np.full(128,4)))
            terminated=torch.zeros(128,dtype=torch.bool);episodes=[]
            if self.tick==1:terminated[1]=True;episodes=[dict(env_id=1)]
            if self.tick==4:terminated[0]=True;episodes=[dict(env_id=0,source_indices=[4,7,8])]
            return self.observation,torch.zeros(128),torch.zeros(128),terminated,torch.zeros_like(terminated),episodes
        def reset(self,ids):self.resets.extend(ids.tolist());return self.observation,[]
    class Broken(io.BytesIO):
        def write(self,value):raise BrokenPipeError('CPU encoder fixture')
    policy=SimpleNamespace(act=lambda *args,**kwargs:dict(action=torch.ones(128,39)*.2));gym=SimpleNamespace(IMAGE_COLOR=1)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for broken in (False,True):
            pool=Pool();videos={k:SimpleNamespace(stdin=Broken() if broken and k=='hand' else io.BytesIO()) for k in ('hand','fullbody')}
            capture=native._EnvZeroCapture(pool,gym,np,dict(hand=0,fullbody=1),videos)
            try:video.capture_episode(pool,policy,capture,np,torch,('state',))
            except BrokenPipeError as error:assert broken and str(error)=='CPU encoder fixture'
            else:assert not broken and capture.episode['env_id']==0 and pool.resets==[1]
            count=2 if broken else 4;assert len(capture.samples)==count
            assert all(r['candidate'].shape==(3,) and r['wrong'].shape==(3,) and r['released'].shape==(3,) and r['wrist_candidate_arm_rad'].shape==(12,) for r in capture.samples)
            assert np.array_equal([r['physics_step'] for r in capture.samples],4*np.arange(1,count+1))
            if not broken:assert capture.frame_times_s==[2/60,4/60] and len(videos['hand'].stdin.getvalue())==2*1280*720*3
            out=root/str(broken);out.mkdir();status=video.save_raw(out,capture,pool,np,broken)
            assert status['trace_finite'] and status['clock_contiguous']
            rawpath=out/('partial_poses_env0000.npz' if broken else 'poses_env0000.npz')
            with np.load(rawpath) as raw:
                assert raw['candidate'].shape==(count,3) and raw['q'].shape==(count,105) and raw['guard_current_goal'].shape==(count,)
            digest=video.grid.sha(rawpath)
            try:video.save_raw(out,capture,pool,np,broken)
            except FileExistsError:pass
            else:raise AssertionError('Existing raw overwritten')
            assert video.grid.sha(rawpath)==digest
    # Call the gate alone in a fresh process; never enter native even after final seal.
    code="""import runpy,sys,json
v=runpy.run_path(sys.argv[1],run_name='prefix_video_fresh_gate')
blocked=False
try:v['gate'](300)
except (FileNotFoundError,AssertionError):blocked=True
assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
print(json.dumps({'unreviewed_gate_blocked':blocked,'stdlib_only':True}))
"""
    value=subprocess.run([video.grid.PYTHON,'-B','-c',code,str(video.HERE/'render.py')],capture_output=True,text=True,check=True)
    fresh=json.loads(value.stdout);assert fresh['stdlib_only']
    review=video.producer.HERE/'review.json';assert video.grid.sha(review)=='b71f0da8ea81a391ca32af64a236b02924b082f6443cb8b795d342d4b17e6c3c'
    record=video.grid.read(review);assert record['verdict']=='PASS' and not record['findings']
    assert all(video.grid.sha(p)==h for p,h in record['reviewed_sha256'].items())
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,actual_checkpoint_read=False,selected_updates=None,prepare_seal_created=False,
        own_schema_header_rejects_legacy_count_and_update=True,original_capture_vector3_and_wrist12=True,firstenv0_episode_otherenv_reset=True,
        original_frame_mapping_and_rgb_bytes=True,BrokenPipe_preserves_complete_partial_raw=True,existing_raw_not_overwritten=True,
        fresh_gate_stdlib_only=fresh,producer_preparation_review=dict(path=str(review),sha256=video.grid.sha(review)),
        native_pixels_tested=False,codec_tested=False,strict_native_load_tested=False,
        limits='Synthetic capture scope only; original PrefixPolicy/init/cap proof reused from producer PASS. Actual models are checked separately; native pixels/codec/CUDA restoration remain unverified.')


def actual_models(video,updates):
    video.completed_training()  # Stdlib completion guard precedes numerical/model reads.
    import copy
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.finger_skill_runner import _validate_pins
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1);extra=video.producer.support();settings=video.producer.settings();rows=[]
    for update in updates:
        path=video.producer.checkpoint(update);digest=video.grid.sha(path);payload=torch.load(path,map_location='cpu',weights_only=False)
        metadata=video.header(payload,update,settings,extra.SCHEMA);_validate_pins(metadata)
        contract=payload['identity']['architecture']['contract']
        policy=extra.PrefixPolicy(contract=contract,size=settings['size'],fresh=False);trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        assert trainer._identity()==payload['identity'] and len(payload['model'])==73
        topology_rejected=False
        try:trainer.load(path)
        except ValueError as error:
            assert str(error)=='CUDA RNG topology mismatch' and payload['cuda_rng'] is not None;topology_rejected=True
        else:assert payload['cuda_rng'] is None
        # Own /tmp CPU projection exercises original full identity/optimizer loader.
        # Only unavailable CUDA RNG restoration is excluded; actual file is immutable.
        with tempfile.TemporaryDirectory() as temp:
            projected=Path(temp)/'cpu_projection.pt';torch.save(dict(payload,cuda_rng=None),projected);trainer.load(projected)
        assert trainer.updates==update and all(torch.equal(v,payload['model'][k]) for k,v in policy.state_dict().items())
        for field in ('actor_optimizer','value_optimizer'):
            actual=getattr(trainer,field).state_dict();expected=payload[field]
            assert actual['param_groups']==expected['param_groups'] and set(actual['state'])==set(expected['state'])
            for key,value in expected['state'].items():
                for name,item in value.items():
                    assert torch.equal(actual['state'][key][name],item) if torch.is_tensor(item) else actual['state'][key][name]==item
        try:trainer.load(video.producer.B.checkpoint(300))
        except ValueError as error:assert 'schema/architecture/input/control/config mismatch' in str(error)
        else:raise AssertionError('Wrong single-note model accepted')
        for wrong in ('schema','guard'):
            bad=copy.deepcopy(contract)
            if wrong=='schema':bad['task']['short_learning']['schema']='guitar_learning.short_finger_learning.v2'
            else:bad['action']['target_contract']['diagnostic_candidate_dip_guard']['source_indices']=[4]
            try:extra.PrefixPolicy(contract=bad,size=settings['size'],fresh=False)
            except ValueError:pass
            else:raise AssertionError('Wrong3note schema/guard accepted')
        assert video.grid.sha(path)==digest
        rows.append(dict(update=update,checkpoint=str(path),sha256=digest,settings_source_pins_valid=True,actual_identity_exact=True,model73_strict_exact=True,
            CPU_projection_original_strict_load_and_optimizers=True,actual_CPU_load_rejected_only_unavailable_CUDA_RNG=topology_rejected,
            actual_native_CUDA_RNG_restore_executed=False,freshFalse_all_trained_tensors_preserved=True,wrong_single_schema_guard_rejected=True))
        del trainer,policy,payload
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,models=rows,
        scope='Actual original identity/models/source verified. /tmp CPU projection excludes only CUDA RNG restoration; native render must load original unmodified checkpoint.')
