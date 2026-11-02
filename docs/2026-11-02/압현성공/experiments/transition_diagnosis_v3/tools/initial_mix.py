"""I 조건: A/B 정렬 초기 분포만 바꾸는 독립 실험.

B_hover의 CPU FK snapshot을 만들고, 별도 GPU 초기화 검증을 통과한 후보만
학습에 사용한다. 전환 중 상태를 쓰지 않으며 평가에서는 A 초기화만 사용한다.
"""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

BASE=Path(__file__).resolve().parents[1]
ROOT=next(p for p in BASE.parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
SCHEMA='guitar_learning.transition_initial_mix.v1'


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def runtime():
    spec=importlib.util.spec_from_file_location('diagnosis_runtime_for_initial_mix',Path(__file__).with_name('runtime.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def prepare(out):
    """위치·회전과105개 DOF를 동일한 B각으로 만든다. native 성공은 주장하지 않는다."""
    import numpy as np
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    r=runtime();r.initial_configuration()
    source=ROOT/'docs/2026-11-02/압현성공/experiments/target_transition_v2/geometry/reference_v3/reference_candidates.json'
    reference=json.loads(source.read_text());candidate=reference['candidates']['B_hover']
    if not candidate['cpu_candidate_valid']:raise ValueError('CPU B 후보 미통과')
    catalog_path=BASE/'geometry/initial_catalog.json';catalog=json.loads(catalog_path.read_text())
    a=next(row for row in catalog['goals'] if row['song']==r.INITIAL_SONG)
    state=copy.deepcopy(a['state']);q=np.asarray(candidate['q105']);names=catalog['joint_names']
    contract=load_gpu_prepared_reset_contract('left');bodies=contract['initial']['human_body_names']
    if names!=contract['initial']['joint_names']:raise ValueError('native105 순서 불일치')
    active=np.asarray(reference['native_indices']);inactive=np.ones(105,dtype=bool);inactive[active]=False
    if not np.allclose(q[inactive],np.asarray(a['q105'])[inactive],atol=1e-7,rtol=0):
        raise ValueError('B 후보에서 팔12·중지4 이외 관절 변경')
    fk=full_fk(SimpleNamespace(names=names,human_bodies=bodies,q_ref=np.asarray(a['q105'])),state)
    poses=fk(q)
    for name,row in zip(bodies,state['human_body_states']):
        position,rotation=poses[name]
        row['pose']['p']=dict(zip('xyz',position.tolist()))
        row['pose']['r']=dict(zip('xyzw',rotation.as_quat().tolist()))
        row['vel']={key:dict.fromkeys('xyz',0.) for key in ('linear','angular')}
    state['human_dof_states']=[dict(pos=float(value),vel=0.) for value in q]
    value=dict(schema=SCHEMA,role='B_hover',fret=7,string_index=2,finger=2,
        q105=q.tolist(),hold_target105=candidate['hold_target105'],state=state,
        cpu_fk_snapshot=True,native_verified=False,
        source_reference=str(source),source_reference_sha256=r.natural.digest(source),
        initial_catalog_sha256=r.natural.digest(catalog_path),
        active_physical_inputs=json.loads((BASE/'geometry/initial_provenance.json').read_text())['active_physical_inputs'],
        fk_scope='A calibrated native105 FK; B_hover arm12+middle4 only; guitar/chair unchanged; zero human velocity',
        note='CPU snapshot only; independent native reset validation required before training')
    if Path(out).exists():raise FileExistsError(out)
    write(out,value);return value


def verify_candidate(candidate):
    r=runtime();value=json.loads(Path(candidate).read_text())
    if value.get('schema')!=SCHEMA or not value.get('cpu_fk_snapshot'):raise ValueError('I CPU snapshot 필요')
    if r.natural.digest(BASE/'geometry/initial_catalog.json')!=value['initial_catalog_sha256']:
        raise ValueError('A catalog 변경')
    if r.natural.digest(value['source_reference'])!=value['source_reference_sha256']:raise ValueError('B 원본 변경')
    for name,expected in value['active_physical_inputs'].items():
        if r.natural.digest(ROOT/name)!=expected:raise ValueError('B 초기 기하 입력 변경: '+name)
    return value


def verify_native(candidate,proof):
    """별도 검증이 동일 후보·물리 입력에 대해 성공했는지 확인한다."""
    r=runtime();value=verify_candidate(candidate);record=json.loads(Path(proof).read_text())
    expected=dict(candidate_sha256=r.natural.digest(candidate),initial_catalog_sha256=value['initial_catalog_sha256'],
        active_physical_inputs=value['active_physical_inputs'])
    if record.get('schema')!='guitar_learning.transition_initial_mix_native.v1':raise ValueError('B native reset 검증 필요')
    for name,target in expected.items():
        if record.get(name)!=target:raise ValueError('B native 검증 입력 불일치: '+name)
    if (not record.get('completed') or not record.get('finite') or record.get('episodes',0)<32 or
        record.get('hold_duration_s',0)<2. or record.get('physical_failures',1)!=0 or
        record.get('wrist_failures',1)!=0 or record.get('max_readback_position_error_m',1)>.001 or
        record.get('max_readback_rotation_error_rad',1)>.01 or
        record.get('max_readback_dof_error_rad',1)>.001 or record.get('minimum_initial_pad_height_m',-1)<.004):
        raise ValueError('B native reset 안정성/간격 기준 미충족')
    return value


@contextmanager
def mixed_runtime(settings):
    import torch
    r=runtime();mix=settings['initial_mix'];candidate=Path(mix['candidate']);proof=Path(mix['native_proof'])
    if mix.get('schema')!=SCHEMA or mix.get('training_B_fraction')!=.5 or mix.get('evaluation_B_fraction')!=0.:raise ValueError('고정50:50 학습/A평가 계약 필요')
    b=verify_native(candidate,proof)
    if r.natural.digest(candidate)!=mix['candidate_sha256'] or r.natural.digest(proof)!=mix['native_proof_sha256']:
        raise ValueError('초기 분포 입력 봉인 변경')
    from guitar_learning.gpu.scene import GpuScene,_body_row
    from guitar_learning.training import finger_skill_runner as runner
    class MixedScene(r.TransitionScene):
        mix_enabled=True
        def reset(self,indices):
            if not self._configured:return super().reset(indices)
            ids=torch.as_tensor(indices,dtype=torch.long,device=self.device).flatten()
            # 같은 물리 시점이어도 학습↔평가 모드가 바뀐 행은 새 분포로 초기화한다.
            # 행별로 기록하여 부분 reset 후 나머지 행의 B 상태도 빠짐없이 해제한다.
            rows=ids.cpu().tolist();modes=getattr(self,'_mix_reset_modes',{})
            same_mode=all(modes.get(index) is self.mix_enabled for index in rows)
            if not same_mode:self._last_reset_physics_step=None
            if self._last_reset_physics_step==self.physics_steps and bool(self._reset_mask[ids].all()):
                return self.snapshot()
            if not hasattr(self,'initial_is_B'):self.initial_is_B=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
            choices=torch.rand(len(ids)).tolist()  # official checkpoint의 CPU RNG 복원 경로를 사용한다.
            dofs=[]
            for index,choice in zip(ids.cpu().tolist(),choices):
                use_b=self.mix_enabled and choice<.5;self.initial_is_B[index]=use_b
                goal=b if use_b else self.goal;state=goal['state']
                dofs.append(torch.tensor([[row['pos'],row['vel']] for row in state['human_dof_states']],device=self.device))
                self._natural_press_bodies[index]=torch.tensor([_body_row(row) for kind in ('human','guitar','chair')
                    for row in state[kind+'_body_states']],device=self.device)
                self.initial_hold[index]=torch.tensor(goal['hold_target105'],device=self.device)
                self.initial_is_v9[index]=False
            original=self._prepared_dofs;self._prepared_dofs=torch.stack(dofs)
            try:
                GpuScene.reset(self,ids);self.target[ids]=self.initial_hold[ids]
                self._mix_reset_modes={**modes,**{index:self.mix_enabled for index in rows}}
                return self.snapshot()
            finally:self._prepared_dofs=original
    original_scene=r.TransitionScene;original_pool=r.TransitionPool
    class MixedPool(original_pool):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for contract in (self.contract,self.environment.contract):contract['initial_mix']=copy.deepcopy(mix)
            original_episode=self.environment._episode
            def episode(index,failed):
                result=original_episode(index,failed)
                result['initial_mix']=dict(schema=SCHEMA,started_from_B=bool(self.scene.initial_is_B[index]),
                    training_B_fraction=.5,evaluation_B_fraction=0.,evaluation=bool(self.environment.evaluation))
                return result
            self.environment._episode=episode
        def reset(self,indices=None):
            self.scene.mix_enabled=not self.environment.evaluation
            return super().reset(indices)
    r.TransitionScene=MixedScene;r.TransitionPool=MixedPool
    try:
        with r.transition_runtime(settings):
            original_pins=runner._pins
            def pins(current,out,extra=()):
                return original_pins(current,out,list(extra)+[Path(__file__).resolve(),candidate,proof])
            runner._pins=pins
            try:yield
            finally:runner._pins=original_pins
    finally:r.TransitionScene=original_scene;r.TransitionPool=original_pool


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','train','evaluate','render'))
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--candidate',type=Path)
    parser.add_argument('--native-proof',type=Path);parser.add_argument('--checkpoint',type=Path);parser.add_argument('--resume',type=Path)
    parser.add_argument('--updates',type=int,default=100);parser.add_argument('--seed',type=int)
    parser.add_argument('--horizon',type=int,choices=(32,128));parser.add_argument('--num-envs',type=int)
    parser.add_argument('--action-mode',choices=('mean','sampled'),default='mean')
    parser.add_argument('--std-scale',type=float,choices=(0.,.25,.5,1.),default=1.)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    if args.operation=='prepare':prepare(args.out);return
    if args.updates<1:parser.error('양수 updates 필요')
    if args.operation=='train' and args.checkpoint:parser.error('train은 resume만 허용')
    if args.operation!='train' and (not args.checkpoint or args.resume):parser.error('평가/영상은 checkpoint 필요')
    if args.operation=='evaluate' and args.num_envs not in (None,32,128):parser.error('평가는32/128환경')
    import isaacgym
    import torch
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    r=runtime();source=args.resume if args.operation=='train' else args.checkpoint
    before=None
    if source:
        source=source.resolve();before=r.natural.digest(source)
        payload=torch.load(source,map_location='cpu',weights_only=False);runner._validate_pins(payload['metadata'])
        settings=localize(payload['metadata']['settings'])
        if 'initial_mix' not in settings:raise ValueError('I 전용 모델 필요')
        for key,value in (('seed',args.seed),('horizon',args.horizon),('num_envs',args.num_envs if args.operation=='train' else None)):
            if value is not None and value!=settings[key]:raise ValueError('strict resume 설정 변경 불가: '+key)
        if args.candidate and args.candidate.resolve()!=Path(settings['initial_mix']['candidate']).resolve():raise ValueError('저장 후보 변경 불가')
        if args.native_proof and args.native_proof.resolve()!=Path(settings['initial_mix']['native_proof']).resolve():raise ValueError('저장 native 검증 변경 불가')
    else:
        if args.operation!='train' or not args.candidate or not args.native_proof:parser.error('candidate/native-proof 필요')
        verify_native(args.candidate,args.native_proof)
        settings=r.build_settings(updates=args.updates,seed=args.seed if args.seed is not None else 7,
            horizon=args.horizon or 32,num_envs=args.num_envs or 64)
        settings['initial_mix']=dict(schema=SCHEMA,training_B_fraction=.5,evaluation_B_fraction=0.,
            candidate=str(args.candidate.resolve()),candidate_sha256=r.natural.digest(args.candidate),
            native_proof=str(args.native_proof.resolve()),native_proof_sha256=r.natural.digest(args.native_proof))
    with mixed_runtime(settings):
        if args.operation=='train':
            settings['updates']=args.updates;result=runner.run(settings,SimpleNamespace(out=args.out.resolve(),resume=source))
        elif args.operation=='evaluate':
            original=runner._DeterministicPolicy
            class EvaluationPolicy(original):
                def act(self,*inputs):return r.evaluation_action(self.policy,inputs,args.action_mode,args.std_scale)
            runner._DeterministicPolicy=EvaluationPolicy
            try:result=runner.evaluate_checkpoint(source,args.out.resolve(),num_envs=args.num_envs or 32,scope='full_song',max_episodes=args.num_envs or 32)
            finally:runner._DeterministicPolicy=original
            write(args.out/'action_mode.json',dict(action_mode=args.action_mode,std_scale=args.std_scale,
                evaluation_seed=settings['seed'],first_episodes=args.num_envs or 32,initial_B_fraction=0.))
        else:
            if args.action_mode!='mean' or args.std_scale!=1.:parser.error('영상은 기본 mean 실행만 지원')
            from guitar_learning.tool.demonstration.render_finger_skill import render
            result=render(source,args.out.resolve(),num_envs=args.num_envs or 4,scope='full_song')
    report=result[0] if isinstance(result,tuple) else result
    if before is not None and r.natural.digest(source)!=before:raise ValueError('실행 중 체크포인트 변경')
    if not report.get('completed') or report.get('failure'):raise RuntimeError('I 조건 실행 미완료; report 확인')

if __name__=='__main__':main()
