"""Two closed-loop B300 evaluations; only candidate-positive DIP target increments differ."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import random
import subprocess
import sys

HERE=Path(__file__).resolve().parent
BPATH=HERE.parent/'low_effort_index_zero_cost_init_v1'
spec=importlib.util.spec_from_file_location('dip_guard_B_producer',BPATH/'probe.py')
B=importlib.util.module_from_spec(spec);sys.modules[spec.name]=B;spec.loader.exec_module(B)
grid,cap=B.grid,B.cap
MODES=('passthrough','candidate_dip_no_positive_increment')
REVIEW=BPATH/'analysis/results_v1/review.json'
REVIEW_SHA='49995b26e859c2cd4e4fafa0ffdafd8ef61c8af54e331fe0b0ff9b38e8a78e78'


def actual_gate():
    _,paths=B.gate('evaluate');assert grid.sha(REVIEW)==REVIEW_SHA
    paths.update(B.base.reviewed(REVIEW));paths.add(B.checkpoint(300))
    return paths|{BPATH/'probe.py',Path(__file__).resolve(),HERE/'PLAN.md'}


def gate(require_review=True):
    paths=actual_gate();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def target_filter(controller,original,action,snapshot,first,candidate,wrong,failed,dip,ai,guard):
    import torch
    old=controller.target[:,dip].clone();raw=original(action,snapshot)
    if raw.data_ptr()!=controller.target.data_ptr():raise ValueError('Target return must alias controller memory')
    before=raw.clone();proposed=raw[:,dip].clone()
    finite=torch.isfinite(before).all(-1) & torch.isfinite(old)
    for key in ('q','qd','body_state','contact_force'):finite &= torch.isfinite(snapshot[key]).flatten(1).all(-1)
    valid=first & candidate & ~wrong & ~failed & ~snapshot['reset_body_snapshot'] & finite
    blocked=valid & (proposed>old) & guard
    controller.target[:,dip]=torch.where(blocked,old,proposed)
    final=raw[:,dip].clone();difference=(raw-before).abs();difference[:,dip]=0
    other=difference.amax(-1)
    low=torch.maximum(controller.lower[dip],controller.action_low[ai])
    high=torch.minimum(controller.upper[dip],controller.action_high[ai])
    rate=controller.rate[dip]/60
    excess=torch.maximum(torch.maximum(low-final,final-high),torch.maximum((final-old).abs()-rate,torch.zeros_like(old)))
    memory=(raw[:,dip]-controller.target[:,dip]).abs()
    check=first & finite
    tolerance=8*torch.finfo(raw.dtype).eps*torch.maximum(old.abs(),proposed.abs()).clamp_min(1)
    if not bool(((other[check]==0)&(memory[check]==0)&(excess[check]<=tolerance[check])).all()):raise ValueError('DIP target memory/other104/native-rate mismatch')
    if not bool((final[~blocked]==proposed[~blocked]).all()):raise ValueError('Unblocked target changed')
    return raw,dict(first_attempt=first.clone(),candidate=candidate.clone(),wrong=wrong.clone(),eligible=valid,blocked=blocked,
        reset=snapshot['reset_body_snapshot'].clone(),prior_failure=failed.clone(),finite=finite,old_target_rad=old,raw_target_rad=proposed,final_target_rad=final,
        other104_error_rad=other,memory_error_rad=memory,box_rate_excess_rad=excess,numerical_tolerance_rad=tolerance)


def fingerprints(policy,trainer):
    import numpy as np
    import torch
    h=hashlib.sha256()
    for k,v in sorted(policy.state_dict().items()):h.update(k.encode());h.update(v.detach().cpu().contiguous().numpy().tobytes())
    rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().numpy(),[v.cpu().numpy() for v in torch.cuda.get_rng_state_all()] if torch.cuda.is_initialized() else [])
    return dict(model_sha256=h.hexdigest(),RNG_sha256=hashlib.sha256(pickle.dumps(rng)).hexdigest(),updates=trainer.updates,cost_weight=trainer.cost_weight)


@contextmanager
def observer_scope(runner,mode,audit):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    old=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer)
    trainers=[]
    class Pool(old[0]):
        def __init__(self,config,out):
            super().__init__(config,out)
            try:
                assert self.num_envs==128 and self.spec['finger']==1 and self.spec['mode']=='incremental'
                self.first=torch.ones(128,dtype=torch.bool,device=self.scene.device);self.pending=None
                self.dip=self.scene.names.index('LH:index3');ai=self.controller.active.tolist().index(self.dip);self.dip_action=ai
                assert self.spec['learned_action_names'][-1]=='LH:index3' and self.spec['learned_action_indices'][-1]==ai and self.controller.rate[self.dip]==4
                self.obs_index=self.contract['observation']['fields'].index('target_error.LH:index3')
                self.native_targets=self.controller.targets;self.controller.targets=self.targets
                audit['pool']=self;audit['dip_native_index']=self.dip;audit['max_ticks']=self.spec['view']['duration_ticks']
            except BaseException:
                try:self.close()
                except BaseException as error:audit.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
                raise
        def targets(self,action,snapshot):
            env=self.environment;j=env.selected_index
            raw,self.pending=target_filter(self.controller,self.native_targets,action,snapshot,self.first,env.candidate[:,j],env.wrong[:,j],
                env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure,self.dip,self.dip_action,mode==MODES[1])
            self.pending['start_clock']=env.clock.clone();return raw
        def step(self,action):
            if len(audit['rows'])>=audit['max_ticks']:raise ValueError('First-attempt tick budget exceeded')
            self.pending=None
            try:result=super().step(action)
            except BaseException:
                if self.pending is not None:
                    try:audit['aborted_control']={k:v.detach().cpu().numpy() for k,v in self.pending.items()}
                    except BaseException as error:audit.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
                raise
            row=self.pending
            if row is None:raise RuntimeError('Missing per-control DIP record')
            row['clock']=self.environment.clock.clone();row['post_failure']=(self.environment.failure.any(-1)|self.environment.wrist_failure|self.environment.wrist_severe_failure).clone()
            row['submit_error_rad']=(self.scene.target[:,self.dip]-row['final_target_rad']).abs()
            expected=((self.scene.target[:,self.dip]-self.scene.q[:,self.dip])/self.environment.scales[self.obs_index]).clamp(-10,10)
            row['observation_error']=(result[0]['state'][:,self.obs_index]-expected).abs()
            valid=row['first_attempt'] & row['finite']
            if not bool(((row['submit_error_rad'][valid]==0)&(row['observation_error'][valid]==0)).all()):raise ValueError('Scene/observation differs from filtered target')
            audit['rows'].append({k:np.where(row['first_attempt'].cpu().numpy(),v.detach().cpu().numpy(),np.zeros_like(v.detach().cpu().numpy())) for k,v in row.items()})
            for episode in result[-1]:
                audit.setdefault('completed_envs',set()).add(episode['env_id']);self.first[episode['env_id']]=False
            return result
    def trainer(*args,**kwargs):
        value=old[3](*args,**kwargs);trainers.append(value);return value
    def evaluate(pool,policy,spec,args,out):
        before=fingerprints(policy,trainers[0]);primary=None
        try:return old[2](pool,policy,spec,args,out)
        except BaseException as error:primary=error;raise
        finally:
            try:
                after=fingerprints(policy,trainers[0]);audit['policy_before']=before;audit['policy_after']=after
                if before!=after:raise ValueError('Frozen policy/RNG/updates changed')
            except BaseException as error:
                if primary is None:raise
                audit.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
    runner.ShortPool=runtime.ShortPool=Pool;runner._evaluate=evaluate;runner.DecisionPPOTrainer=trainer
    try:yield runner
    finally:
        runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer=old
        audit['observer_aliases_restored']=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer)==old


def launch(mode):
    assert mode in MODES
    out=HERE/'runs'/mode;cap.reject_existing(out);seal,paths=gate();observed={};audit=dict(rows=[]);failure=None;cleanup=[]
    old=(B.base.output,B.base.checkpoint)
    try:
        import isaacgym  # Entire gate and output rejection precede numerical/native imports.
        with B.execution_scope('evaluate',seal,paths,observed):
            original=B.base.effort_scope
            @contextmanager
            def scope(evidence,state):
                with original(evidence,state) as runner:
                    with observer_scope(runner,mode,audit):yield runner
            B.base.effort_scope=scope;B.base.output=lambda *args,**kwargs:out;B.base.checkpoint=lambda update:B.checkpoint(update)
            try:B.base.launch('evaluate',None,300)
            finally:B.base.effort_scope=original
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        B.base.output,B.base.checkpoint=old
        cleanup.extend(audit.get('cleanup_errors',[]))
        state=observed.get('state',{});restored=(B.base.output,B.base.checkpoint)==old
        if out.is_dir():
            if 'identity' in state:cap.owned(out,state['identity'])
            try:
                import numpy as np
                if audit.get('aborted_control'):
                    with (out/'dip_aborted_control.npz').open('xb') as f:np.savez_compressed(f,**audit['aborted_control'])
                if audit['rows']:
                    with (out/'dip_control60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in audit['rows']]) for k in audit['rows'][0]})
            except BaseException as error:cleanup.append(dict(type=type(error).__name__,message=str(error)))
            checks=dict(all128_first_attempts_finished=len(audit.get('completed_envs',set()))==128,outer_aliases_restored=restored,observer_aliases_restored=audit.get('observer_aliases_restored',False),
                B_initialization_aliases_restored=state.get('initialization_aliases_restored',False),B_contract_tagged=state.get('initialization_contract_tagged',False),
                frozen_policy=audit.get('policy_before')==audit.get('policy_after') and 'policy_before' in audit)
            grid.write(out/'execution_override.json',dict(mode=mode,scope='Frozen B300 plus closed-loop target override; not unmodified policy performance or fixed-tape effect',
                enabled=mode==MODES[1],only='current candidate positive DIP increment held; negative/zero and other104 unchanged' if mode==MODES[1] else 'disabled; original targets unchanged',model_checkpoint=str(B.checkpoint(300)),fresh=False,first_attempt_only=True,physics_hz=240,control_hz=60))
            grid.write(out/'dip_guard_report.json',dict(completed=failure is None and not cleanup and all(checks.values()),failure=failure,cleanup_errors=cleanup,checks=checks,
                mode=mode,assigned_first_attempts=128,completed_first_attempts=len(audit.get('completed_envs',set())),control_rows=len(audit['rows']),trace_scope='All128 first-attempt scalar DIP control60; includes failed endpoint; retries masked. Full body detail remains env0 only.',
                policy_before=audit.get('policy_before'),policy_after=audit.get('policy_after')))
            if failure is None and (cleanup or not all(checks.values())):raise RuntimeError('DIP observer audit failed; original outputs retained')


def commands():return {m:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',m] for m in MODES}


def prepare():
    assert not any(m in sys.modules for m in ('torch','numpy','isaacgym'));paths=actual_gate()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    tests=B.module('dip_guard_cpu_checks',HERE/'cpu_checks.py');verification=tests.check(sys.modules[__name__])
    config=grid.read(BPATH/'cpu_inputs/settings.json');inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('settings.json',config),('commands.json',commands()),('execution_override.json',dict(modes=MODES,changed_native_joint='LH:index3',first_attempts_per_condition=128,closed_loop=True))):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',verification)
    paths.update(inputs.glob('*.json'));paths.update((HERE/'cpu_checks.py',HERE/'README.md',HERE/'cpu_verification.json'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,jobs=2,pins=len(seal['input_pins']))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for n in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=MODES);args=parser.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare:prepare()
    elif args.self_test:print(json.dumps(B.module('dip_guard_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif args.dry_plan:print(json.dumps(commands(),indent=2))
    elif args.gate_check:
        assert not any(m in sys.modules for m in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate(require_review=True)
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('Pending execution admitted')
        else:gate(require_review=True)
        assert not any(m in sys.modules for m in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,model_deserialized=False,pending_execution_rejected=True,GPU_executed=False)))
    else:launch(args.execute)
