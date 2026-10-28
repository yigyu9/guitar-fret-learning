"""One fresh B initialization under the unchanged reviewed index128 effort scope."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'low_effort_index_learning_v1'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


base=module('zero_cost_original_index',BASE/'probe.py')
grid,cap=base.grid,base.cap
VARIANTS=grid.DIAG/'04_ablation/time_credit_ablation/corrected_source_v3/support/variants.py'
variants=module('zero_cost_original_variants',VARIANTS)
VARIANT='B_zero_cost_head'
UPDATES=base.UPDATES
REVIEWS={
    BASE/'learning_analysis/results_v1/review.json':'841592ad223cf10cbbb96f9827e76d2a41472009b83536b4eb4dfc284a078a47',
    BASE/'regression_audit/results_v1/review.json':'313265435453ffd0f9c5998be917def65b1aafcefb83b722ad6bb2e98b966a65',
    BASE/'precheck_analysis/results_v1/review.json':'07566ae9cd31fd861216a434558a6b9834166c24cdac32360edb8f74cf2015d0'}


def actual_gate():
    _,paths=base.gate('train')  # Original384 no-NN precheck, original source/cap strict gate.
    for path,digest in REVIEWS.items():
        assert grid.sha(path)==digest
        paths.update(base.reviewed(path))
    launcher=BASE/'02_train_eval_launcher.json';value=grid.read(launcher)
    assert value['completed'] and value['returncode']==0 and len(value['children'])==8
    assert all(child['returncode']==0 for child in value['children'])
    return paths|{launcher,BASE/'probe.py',VARIANTS,BASE/'train/initial.pt'}


def gate(phase='train',require_review=True):
    assert phase in ('train','evaluate','render')
    paths=actual_gate();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        review=grid.read(HERE/'review.json')
        assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def output(phase,control=None,update=0):
    assert control is None
    return HERE/'train' if phase=='train' else HERE/(('evaluation_' if phase=='evaluate' else 'native_video_')+('%06d'%update))


def checkpoint(update):
    return HERE/'train'/('initial.pt' if update==0 else 'final.pt' if update==300 else 'evaluation_%06d.pt'%update)


def tag(contract):
    short=contract['task']['short_learning'];assert 'ablation' not in short
    short['ablation']=copy.deepcopy(variants.descriptor(VARIANT))


def initial_comparison(new_model,old_model):
    import torch
    assert set(new_model)==set(old_model) and len(new_model)==73
    changed=sorted(k for k,v in old_model.items() if not torch.equal(v,new_model[k]))
    assert changed==['cost_critic.bias','cost_critic.weight']
    assert all(not torch.count_nonzero(new_model[k]) for k in changed)
    return dict(state_tensor_count=73,equal_original_state_tensors=71,changed_state_names=changed,cost_parameters_exact_zero=True)


def initialization_scope(original_scope,fresh):
    @contextmanager
    def scope(paths,state):
        from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
        state['initialization_aliases_restored']=False;state['initialization_contract_tagged']=False
        with original_scope(paths,state) as r:
            old=(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy)
            policy=variants.policy_type(VARIANT,fresh=fresh)
            class TaggedPool(old[0]):
                def __init__(self,config,out):
                    super().__init__(config,out)
                    try:
                        tag(self.contract);state['initialization_contract_tagged']=True
                        runner.write(Path(out)/'initialization_declaration.json',dict(descriptor=variants.descriptor(VARIANT),fresh=fresh,
                            scope='Only fresh cost_critic final linear weight/bias zero; evaluation/render never re-zero'))
                    except BaseException:
                        self.close();raise
            runner.ShortPool=runtime.ShortPool=TaggedPool;runner.ShortPolicy=runtime.ShortPolicy=policy
            try:yield r
            finally:
                runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy=old
                state['initialization_aliases_restored']=(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy)==old
    return scope


@contextmanager
def execution_scope(phase,seal,paths,observed):
    old=(base.HERE,base.gate,base.effort_scope)
    wrapped=initialization_scope(old[2],fresh=phase=='train')
    @contextmanager
    def scope(evidence,state):
        observed['state']=state
        with wrapped(evidence,state) as runner:yield runner
    base.HERE=HERE;base.gate=lambda requested:(seal,paths);base.effort_scope=scope
    try:yield
    finally:base.HERE,base.gate,base.effort_scope=old


def launch(phase,update):
    assert phase in ('train','evaluate','render') and update in UPDATES and (phase!='train' or update==0)
    out=output(phase,update=update);cap.reject_existing(out)
    seal,paths=gate(phase);observed={};failure=None;completed=False
    old=(base.HERE,base.gate,base.effort_scope)
    try:
        with execution_scope(phase,seal,paths,observed):base.launch(phase,None,update)
        if phase=='train':
            import torch
            new,prior=checkpoint(0),BASE/'train/initial.pt'
            result=initial_comparison(torch.load(new,map_location='cpu',weights_only=False)['model'],torch.load(prior,map_location='cpu',weights_only=False)['model'])
            grid.write(out/'initial_model_comparison.json',dict(result,new_initial=str(new),new_initial_sha256=grid.sha(new),baseline_initial=str(prior),baseline_initial_sha256=grid.sha(prior),
                scope='Model-only exact comparison; no baseline trainer/actor transfer or relaxed full load'))
        completed=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        state=observed.get('state',{});restored=(base.HERE,base.gate,base.effort_scope)==old
        ok=restored and state.get('initialization_aliases_restored',False) and state.get('initialization_contract_tagged',False)
        if out.is_dir():
            if 'identity' in state:cap.owned(out,state['identity'])
            grid.write(out/'zero_cost_diagnostic.json',dict(completed=completed and ok,failure=failure,base_aliases_restored=restored,
                initialization_aliases_restored=state.get('initialization_aliases_restored',False),initialization_contract_tagged=state.get('initialization_contract_tagged',False),
                variant=VARIANT,fresh_initialization=phase=='train',original_diagnostic_report_preserved=True))
        if failure is None and not ok:raise RuntimeError('Zero-cost initialization scope audit failed; outputs preserved')


def commands():
    common=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']
    return dict(train=common+['train'],evaluate=[common+['evaluate','--update',str(u)] for u in UPDATES],
        render_template=common+['render','--update','CHOOSE_FROM_ACTUAL_FIXED_EVALUATIONS'])


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    paths=actual_gate();assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('zero_cost_cpu_checks',HERE/'cpu_checks.py')
    declaration,verification=checks.check(sys.modules[__name__])
    from guitar_learning.tool.experiments.short_finger_learning import runner
    config=runner.make_settings(base.train_args(HERE/'train'));assert config==grid.read(BASE/'cpu_inputs/settings.json')
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    grid.write(inputs/'settings.json',config);grid.write(inputs/'effort_declaration128.json',declaration)
    grid.write(inputs/'initialization.json',variants.descriptor(VARIANT));grid.write(inputs/'commands.json',commands())
    grid.write(HERE/'cpu_verification.json',verification)
    paths.update(inputs.glob('*.json'));paths.update((Path(__file__).resolve(),HERE/'PLAN.md',HERE/'cpu_checks.py',HERE/'cpu_verification.json',VARIANTS))
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),
        reused_precheck_review=str(base.PRECHECK_REVIEW),scope='B only: fresh cost head2zero; same index128/cap.25; root-only native'))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),jobs=8)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','gate-check','self-test','dry-plan'):group.add_argument('--'+name,action='store_true')
    group.add_argument('--execute',choices=('train','evaluate','render'));parser.add_argument('--update',type=int,choices=UPDATES,default=0)
    args=parser.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare:prepare()
    elif args.gate_check:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:launch('train',0)
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending initialization admitted')
        else:gate(require_review=True)
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym')) and not (HERE/'train').exists()
        print(json.dumps(dict(fresh_process=True,stdlib_gate=True,pending_native_rejected=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False)))
    elif args.self_test:print(json.dumps(module('zero_cost_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__])[1],indent=2))
    elif args.dry_plan:print(json.dumps(commands(),indent=2))
    else:launch(args.execute,args.update)
