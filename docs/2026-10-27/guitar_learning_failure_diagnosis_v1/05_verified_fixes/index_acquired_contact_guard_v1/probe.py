"""Frozen prefix300 paired target override; original strict identity remains intact."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
parent=module('acquired_original_prefix',HERE.parent/'low_effort_index_prefix_learning_v1/probe.py')
grid,cap=parent.grid,parent.cap
MODES=('current_goal','acquired_contact')
INDICES=(4,7,8)
REVIEW=parent.HERE/'learning_analysis/results_v1/review.json'
REVIEW_SHA='59295b114d5fbc0f9992d5857ea71e3aa5601e96a46fbcbd60050ce7a0d5b2a6'


def descriptor(mode):
    assert mode in MODES
    return dict(schema='diagnostic.index_acquired_contact_guard.v1',mode=mode,model_identity='unchanged original prefix300; execution override is separate',
        memory='3bits/env: acquire current goal candidate & ~wrong; keep only while candidate & ~wrong; clear unsafe/reset rows; none cannot acquire but can retain',
        control='positive DIP target increment held on original current goal' if mode==MODES[0] else 'positive DIP target increment held on any still-valid acquired contact',
        preserved='negative/zero increment and other104 exact; no N/full4freeze/new force gate; original codec once',
        scope='60Hz precontrol cache, not certified continuous240Hz contact; closed-loop feedback may change subsequent policy/arm actions')


def evidence():
    _,paths=parent.gate('evaluate');assert grid.sha(REVIEW)==REVIEW_SHA
    return paths|parent.base.reviewed(REVIEW)|{Path(__file__).resolve(),HERE/'PLAN.md',parent.checkpoint(300)}


def gate(require_review=True):
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def memory_step(before,candidate,wrong,goal,safe):
    import torch
    current=goal[:,None]==goal.new_tensor(INDICES)[None]
    return safe[:,None] & candidate & ~wrong & (before|current)


def filtered_targets(pool,action,snapshot,mode,original,extra):
    import torch
    env=pool.environment;rows=torch.arange(pool.num_envs,device=pool.scene.device)
    col,present=extra.current_goal(env._score_time(),env.end[list(INDICES)])
    goal=torch.where(present,col.new_tensor(INDICES)[col],-torch.ones_like(col))
    candidates=env.candidate[:,list(INDICES)];wrongs=env.wrong[:,list(INDICES)];failed=env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure
    before=pool.acquired.clone();current_candidate=candidates[rows,col]&present;current_wrong=wrongs[rows,col]&present
    if mode==MODES[0]:
        target=original(pool,action,snapshot);r=pool.pending  # Original current-goal function, unchanged.
    else:
        finite=torch.isfinite(pool.controller.target[:,pool.dip])
        for key in ('q','qd','body_state','contact_force'):finite &= torch.isfinite(snapshot[key]).flatten(1).all(-1)
        provisional=memory_step(before,candidates,wrongs,goal,finite&~failed&~snapshot['reset_body_snapshot'])
        target,r=parent.guard.target_filter(pool.controller,pool.native_targets,action,snapshot,torch.ones_like(present),
            provisional.any(-1),torch.zeros_like(present),failed,pool.dip,pool.ai,True)
        r.update(first_attempt=pool.first.clone(),current_goal=goal.clone(),start_clock=env.clock.clone());pool.pending=r
    safe=r['finite']&~failed&~snapshot['reset_body_snapshot'];after=memory_step(before,candidates,wrongs,goal,safe);pool.acquired.copy_(after)
    if mode==MODES[1]:r['candidate']=after.any(-1)  # Effective memory predicate, explicitly not current-goal candidate.
    baseline_eligible=safe&current_candidate&~current_wrong
    r.update(input_current_candidate=current_candidate.clone(),input_current_wrong=current_wrong.clone(),
        baseline_would_block=baseline_eligible&(r['raw_target_rad']>r['old_target_rad']))
    r['memory_extended_block']=r['blocked']&~r['baseline_would_block']
    for j,index in enumerate(INDICES):
        for label,value in (('selected_candidate',candidates),('selected_wrong',wrongs),('memory_before',before),('memory_after',after),('memory_acquired',after&~before),('memory_lost',before&~after)):
            r[label+'_'+str(index)]=value[:,j].clone()
    return target


@contextmanager
def observer_scope(runner,mode,audit):
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    extra=parent.support();old=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer);trainers=[]
    class Pool(old[0]):
        def __init__(self,config,out):
            super().__init__(config,out)
            try:
                self.acquired=torch.zeros(self.num_envs,3,dtype=torch.bool,device=self.scene.device);audit['pool']=self
            except BaseException:
                try:self.close()
                except BaseException as error:audit.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
                raise
        def reset(self,indices=None):
            result=super().reset(indices)
            if hasattr(self,'acquired'):
                ids=torch.arange(self.num_envs,device=self.scene.device) if indices is None else torch.as_tensor(indices,device=self.scene.device,dtype=torch.long)
                self.acquired[ids]=False
            return result
        def targets(self,action,snapshot):return filtered_targets(self,action,snapshot,mode,old[0].targets,extra)
        def step(self,action):
            result=super().step(action)
            # Parent pending/step invariants are retained. Saved names state the new predicate's scope.
            record=self.guard_rows[-1]
            for key in ('candidate','wrong','eligible','blocked'):record['effective_'+key]=record.pop(key)
            return result
    def trainer(*args,**kwargs):
        value=old[3](*args,**kwargs);trainers.append(value);return value
    def evaluate(pool,policy,spec,args,out):
        before=parent.guard.fingerprints(policy,trainers[0]);audit['policy_before']=before;primary=None
        try:return old[2](pool,policy,spec,args,out)
        except BaseException as error:primary=error;raise
        finally:
            try:
                after=parent.guard.fingerprints(policy,trainers[0]);audit['policy_after']=after
                if after!=before:raise ValueError('Frozen policy/RNG/updates changed')
            except BaseException as error:
                if primary is None:raise
                audit.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
    runner.ShortPool=runtime.ShortPool=Pool;runner._evaluate=evaluate;runner.DecisionPPOTrainer=trainer
    try:yield
    finally:
        runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer=old
        audit['observer_aliases_restored']=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer)==old


def launch(mode):
    assert mode in MODES
    out=HERE/'runs'/mode;cap.reject_existing(out);seal,paths=gate();observed={};audit={};failure=None;completed=False
    old=(parent.base.output,parent.base.checkpoint)
    try:
        import isaacgym  # Existing-output and full stdlib pin/review gates precede native import.
        with parent.execution_scope('evaluate',seal,paths,observed):
            original=parent.base.effort_scope
            @contextmanager
            def scope(evidence,state):
                with original(evidence,state) as runner:
                    with observer_scope(runner,mode,audit):yield runner
            parent.base.output=lambda *args,**kwargs:out;parent.base.checkpoint=lambda update:parent.checkpoint(update);parent.base.effort_scope=scope
            try:parent.base.launch('evaluate',None,300)
            finally:parent.base.effort_scope=original
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        # parent.execution_scope restores its own aliases; restore direct bindings too.
        parent.base.output,parent.base.checkpoint=old
        if out.is_dir():
            state=observed.get('state',{});cleanup=audit.setdefault('cleanup_errors',[]);cleanup.extend(state.get('cleanup_errors',[]))
            try:
                if 'identity' not in state:raise RuntimeError('No exclusively-created output ownership')
                cap.owned(out,state['identity']);pool=audit.get('pool')
                try:
                    if pool is not None and pool.guard_rows:
                        import numpy as np
                        with (out/'acquired_control60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
                    if (out/'evaluation.json').is_file():grid.write(out/'prefix_acceptance.json',parent.acceptance(grid.read(out/'evaluation.json')['episodes']))
                except BaseException as error:cleanup.append(dict(type=type(error).__name__,message=str(error)))
                grid.write(out/'execution_override.json',dict(descriptor(mode),model_checkpoint=str(parent.checkpoint(300)),model_checkpoint_sha256=grid.sha(parent.checkpoint(300)),
                    original_training_contract_preserved=True,scope='Frozen NN plus declared target override; raw policy_performance flag does not certify unmodified policy performance'))
                checks=dict(outer_aliases_restored=(parent.base.output,parent.base.checkpoint)==old,prefix_aliases_restored=observed.get('aliases_restored',False),
                    observer_aliases_restored=audit.get('observer_aliases_restored',False),prefix_task_verified=state.get('prefix_task_verified',False),
                    original_NN_constructor_exact=observed.get('NN_constructors')==1,frozen_model_RNG_updates='policy_before' in audit and audit.get('policy_before')==audit.get('policy_after'))
                grid.write(out/'acquired_guard_report.json',dict(completed=completed and not cleanup and all(checks.values()),failure=failure,cleanup_errors=cleanup,checks=checks,
                    mode=mode,policy_before=audit.get('policy_before'),policy_after=audit.get('policy_after'),
                    field_scope='effective_candidate/eligible/blocked mean mode-specific memory gate, not necessarily original current goal; input_current_* and selected_* retain actual predicates; scalar3bit fields; firstmask;60Hz only',
                    guard_counts_all_episode_controls=pool.guard_counts.cpu().tolist() if pool is not None else None))
                if failure is None and (cleanup or not all(checks.values())):raise RuntimeError('Override audit failed; outputs retained')
            except BaseException as error:
                if failure is None:raise
                print('Secondary acquired cleanup error: '+repr(error),file=sys.stderr)


def commands():return {m:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',m] for m in MODES}


def prepare():
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('acquired_guard_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__])
    inputs=HERE/'cpu_inputs';inputs.mkdir();config=parent.settings()
    for name,value in (('settings.json',config),('commands.json',commands()),('execution_override.json',[descriptor(m) for m in MODES])):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json'));paths.update((HERE/'cpu_checks.py',HERE/'README.md',HERE/'cpu_verification.json'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),scope='CPU preparation only; root-only frozen300 paired evaluations'))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,jobs=2,pins=len(seal['input_pins']))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=MODES);args=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare:prepare()
    elif args.self_test:print(json.dumps(module('acquired_guard_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif args.dry_plan:print(json.dumps(commands(),indent=2))
    elif args.gate_check:
        assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'));s,_=gate(require_review=False)
        if s['independent_review']=='pending':
            try:gate()
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('Pending native execution admitted')
        else:gate()
        assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'));print(json.dumps(dict(stdlib_only=True,pending_native_rejected=True,checkpoint_deserialized=False,GPU_executed=False)))
    else:launch(args.execute)
