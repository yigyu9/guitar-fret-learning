"""Single-defect rejection and exact recovery boundary/cleanup regressions."""
import copy
from contextlib import redirect_stderr
import io
from pathlib import Path
import tempfile
from unittest.mock import patch


def check(probe):
    audit=probe.module('goal_fit_post_error_audit',probe.HERE/'audit.py');result=audit.run(probe)
    parent=probe.grid.read(probe.source.HERE/'02_launcher.json');log=(probe.source.HERE/'02_fit.log').read_text();names=[p.name for p in probe.source.output('fit').iterdir()]
    badparents=[]
    for change in (dict(completed=True),dict(returncode=0),dict(children=[]),dict(children=parent['children']+[dict(job='evaluate',returncode=0)])):
        badparents.append(dict(parent,**change))
    child=copy.deepcopy(parent);child['children'][0]['returncode']=0;badparents.append(child)
    child=copy.deepcopy(parent);child['children'][0]['argv'][-1]='evaluate';badparents.append(child)
    cases=[(p,log,names) for p in badparents]+[(parent,log.replace("name 'sys'","name 'other'"),names),(parent,log+'\nTraceback (most recent call last):\n',names),
        (parent,log,names+['inputs_after.json']),(parent,log,names[:-1])]
    for args in cases:
        try:probe.single_defect(*args)
        except AssertionError:pass
        else:raise AssertionError('Different failure/artifacts accepted')
    original=(probe.source.gate,probe.source.output)
    for fail in (False,True):
        try:
            with probe.scope({},set()):
                assert probe.source.gate('evaluate')==({},set()) and probe.source.output('fit')/'initial.pt'==probe.CHECKPOINT
                assert probe.source.output('evaluate')==probe.HERE/'runs/evaluate'
                for forbidden in ('fit','reference'):
                    try:probe.source.gate(forbidden)
                    except ValueError:pass
                    else:raise AssertionError('Recovery retraining allowed')
                if fail:raise RuntimeError('primary scope')
        except RuntimeError as error:assert fail and str(error)=='primary scope'
        assert (probe.source.gate,probe.source.output)==original
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);out=root/'evaluate';out.mkdir();(out/'keep').write_text('unchanged')
        with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',side_effect=AssertionError('must not gate')) as gate:
            try:probe.launch()
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            gate.assert_not_called()
        assert (out/'keep').read_text()=='unchanged'
        link=root/'symlink';link.symlink_to(root/'missing')
        with patch.object(probe,'output',return_value=link),patch.object(probe,'gate',side_effect=AssertionError('must not gate')) as gate:
            try:probe.launch()
            except FileExistsError:pass
            else:raise AssertionError('Broken symlink admitted')
            gate.assert_not_called()
        stderr=io.StringIO()
        def fail(stage):
            out=probe.source.output(stage);out.mkdir(parents=True);raise ValueError('original evaluator primary')
        def write(*args):raise OSError('secondary recovery report')
        with patch.object(probe,'HERE',root/'fresh'),patch.object(probe,'gate',return_value=({},set())),patch.object(probe.source,'launch',side_effect=fail),patch.object(probe.grid,'write',side_effect=write),redirect_stderr(stderr):
            try:probe.launch()
            except ValueError as error:assert str(error)=='original evaluator primary'
            else:raise AssertionError('Original evaluation error lost')
        assert 'secondary recovery report' in stderr.getvalue() and (probe.source.gate,probe.source.output)==original
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    codec=probe.source.support();_,_,_,contract,_=codec.dataset(probe.source);torch.manual_seed(7)
    policy=codec.policy_type(probe.source)(contract=contract,size='large',fresh=True);initial={n:v.clone() for n,v in policy.state_dict().items()}
    trainer=DecisionPPOTrainer(policy,PPOConfig(**probe.source.parent.settings()['ppo']));payload=torch.load(probe.CHECKPOINT,map_location='cpu',weights_only=False)
    for kind in ('cost','critic','std','PPO_update','optimizer','identity'):
        bad=copy.deepcopy(payload)
        if kind in ('cost','critic','std'):
            name={'cost':'cost_critic.bias','critic':'reward_critic.bias','std':'finger_log_std'}[kind];bad['model'][name]+=1
        elif kind=='PPO_update':bad['updates']=1
        elif kind=='optimizer':bad['actor_optimizer']['state']={0:{}}
        else:bad['identity']['architecture']['schema']='wrong'
        try:audit.saved_state(bad,trainer,initial,probe.source.source.source.support())
        except AssertionError:pass
        else:raise AssertionError('Hidden failed fit check admitted: '+kind)
    static={p.name:audit.unresolved(p) for p in probe.HERE.glob('*.py')};assert set(static)=={'probe.py','audit.py','cpu_checks.py'} and not any(static.values())
    assert audit.unresolved(probe.source.HERE/'codec.py')==['sys'] and set(probe.commands())=={'evaluate','checkpoint','PPO_updates','supervised_steps'}
    checks=dict(CPU_only=True,GPU_executed=False,original_failed_parent_and_missing_reports_preserved=True,single_known_failure_negative_cases=len(cases),evaluate_only_scope_and_original_checkpoint=True,
        original_goal_metadata_bytes_identity_unchanged=True,CPU_model73_frozen54_changed19_exact=True,hidden_false_check_cases=6,PPO_empty0=True,original_loss1000_finite=True,original_reference_gate_unchanged=True,
        original_CUDA_topology_rejected_CPU_projection_only=True,scope_aliases_restore_on_error=True,output_and_broken_symlink_rejected_before_gate=True,original_primary_secondary_report_error_preserved=True,
        symtable_referenced_globals=static,symtable_scope='Narrow referenced-global versus module assigned/imported/builtins check, not a general linter; original codec sys defect retained')
    return result,checks
