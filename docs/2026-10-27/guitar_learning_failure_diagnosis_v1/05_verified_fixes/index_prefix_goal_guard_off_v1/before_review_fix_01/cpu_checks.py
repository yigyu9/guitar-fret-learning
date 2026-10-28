"""Only guard-off filter delta and reuse/cleanup fixtures; no scene/model writes."""
import ast
from contextlib import contextmanager,redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def check(probe):
    import torch
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    extra=probe.on.parent.support();original=extra.guard.target_filter
    contract=probe.grid.read(probe.on.recovery.output('evaluate')/'training_contract.json')['action']['target_contract']
    dip=contract['joint_names'].index('LH:index3');ai=contract['action_order'].index('LH:index3');N=128
    from types import SimpleNamespace
    low,high=contract['action_lower_rad'][ai],contract['action_upper_rad'][ai]
    base=torch.full((N,105),(low+high)/2);delta=torch.tensor([.02,-.02,0,.03]).repeat(32);first=torch.ones(N,dtype=torch.bool)
    candidate=first.clone();wrong=torch.zeros_like(first);failed=wrong.clone();candidate[4]=False;wrong[5]=True;failed[6]=True
    snapshot=dict(q=torch.zeros(N,105),qd=torch.zeros(N,105),body_state=torch.zeros(N,1,13),contact_force=torch.zeros(N,1,3),reset_body_snapshot=torch.zeros(N,dtype=torch.bool));snapshot['reset_body_snapshot'][7]=True
    def fixture():
        c=SimpleNamespace(target=base.clone(),lower=torch.full((105,),low),upper=torch.full((105,),high),action_low=torch.full((39,),low),action_high=torch.full((39,),high),rate=torch.full((105,),4.))
        def targets(action,snap):
            c.target+=.001;c.target[:,dip]=base[:,dip]+delta;return c.target
        return c,targets
    c,t=fixture();before=base.clone();on_target,on_row=original(c,t,None,snapshot,first,candidate,wrong,failed,dip,ai,True);on_saved=on_target.clone()
    c,t=fixture();off_target,off_row=probe.passthrough(original,c,t,None,snapshot,first,candidate,wrong,failed,dip,ai,True)
    assert off_target.data_ptr()==c.target.data_ptr() and not off_row['blocked'].any() and torch.equal(off_row['would_block'],on_row['blocked'])
    assert torch.equal(off_row['raw_target_rad'],off_row['final_target_rad']) and (off_row['box_rate_excess_rad']<=off_row['numerical_tolerance_rad']).all()
    other=[i for i in range(105) if i!=dip];assert torch.equal(off_target[:,other],on_saved[:,other]);assert torch.equal(off_target[:,dip][delta<=0],on_saved[:,dip][delta<=0])
    assert torch.equal(base,before) and all(k in off_row for k in ('actual_blocked','would_block'))
    # Exercise the same adapter nesting and its real patched filter, including primary exception.
    old=(probe.on.output,probe.on.gate,probe.on.adapter);approved=({},set(),[1]*4);audit={}
    @contextmanager
    def fake_adapter(*a):yield
    with patch.object(probe.on,'adapter',fake_adapter):
        alias=probe.on.adapter
        try:
            with probe.execution_scope('stochastic',audit,approved):
                assert probe.on.output('stochastic')==probe.output('stochastic') and probe.on.gate('stochastic') is approved
                with probe.on.adapter('stochastic',None,{}):
                    c,t=fixture();_,r=extra.guard.target_filter(c,t,None,snapshot,first,candidate,wrong,failed,dip,ai,True);assert not r['blocked'].any() and r['would_block'].any()
                    raise ValueError('original evaluation primary')
        except ValueError as error:assert str(error)=='original evaluation primary'
        else:raise AssertionError('Primary error lost')
        assert probe.on.adapter is alias
    assert (probe.on.output,probe.on.gate,probe.on.adapter)==old and extra.guard.target_filter is original and all(audit.values())
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for kind in ('existing','symlink'):
            out=root/kind
            if kind=='existing':out.mkdir()
            else:out.symlink_to(root/'absent')
            with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as gate:
                try:probe.launch('deterministic')
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
                gate.assert_not_called()
    # Before a completed stdlib gate, launch cannot reach numerical execution_scope.
    with patch.object(probe,'gate',side_effect=ValueError('pending source actual')),patch.object(probe,'execution_scope') as scope:
        try:probe.launch('deterministic')
        except ValueError as error:assert str(error)=='pending source actual'
        else:raise AssertionError('Incomplete gate admitted')
        scope.assert_not_called()
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)/'new';primary=ValueError('original evaluator primary');stderr=io.StringIO()
        def aborted(mode):out.mkdir();raise primary
        with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',return_value=approved),patch.object(probe.on,'launch',side_effect=aborted),patch.object(probe,'finish',side_effect=OSError('report secondary')),redirect_stderr(stderr):
            try:probe.launch('deterministic')
            except ValueError as error:assert error is primary
            else:raise AssertionError('Primary evaluator error lost')
        assert 'report secondary' in stderr.getvalue() and (probe.on.output,probe.on.gate,probe.on.adapter)==old
    static=probe.on.recovery.module('guard_off_static',probe.on.recovery.HERE/'audit.py');unresolved={p.name:static.unresolved(p) for p in probe.HERE.glob('*.py')};assert not any(unresolved.values())
    for p in probe.HERE.glob('*.py'):ast.parse(p.read_text(),feature_version=(3,8))
    return dict(CPU_only=True,GPU_executed=False,original_passthrough_delegate=True,would_block_equals_on_blocked=True,actual_blocked_zero=True,raw_final_target_exact=True,
        other104_exact=True,negative_zero_exact=True,memory_alias_rate_bounds=True,original_primary_aliases_restored=True,secondary_report_preserves_primary=True,output_symlink_before_gate=True,numerical_scope_after_stdlib_gate=True,
        original_std_mode_callback_reused='source2117 reviewed std/mode/fullstrict/callback fixture unchanged; new scope only replaces target_filter delegate with guard=False',
        symtable_referenced_globals=unresolved,scope='Fixed CPU target snapshots/reuse scope only; native128/physical/closed-loop outcomes unverified')
