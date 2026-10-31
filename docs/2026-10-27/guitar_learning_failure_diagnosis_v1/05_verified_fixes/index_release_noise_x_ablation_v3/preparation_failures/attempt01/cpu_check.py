"""CPU arithmetic and alias tests; no native environment construction."""
import ast
import copy
import inspect
import sys
import probe


def check():
    import torch
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1)
    run, digest = probe.transformed_run()
    original = ast.parse(inspect.getsource(probe.base.run))
    assignment = next(n for n in ast.walk(original) if isinstance(n, ast.Assign)
        and ast.unparse(n) == 'raw[:, ids] = (before.atanh() + noise).tanh()')
    transformed = copy.deepcopy(assignment)
    next(n for n in ast.walk(transformed) if isinstance(n, ast.BinOp) and ast.unparse(n) == 'before.atanh() + noise').right.id = 'applied_noise'
    original_code = compile(ast.Module(body=[assignment], type_ignores=[]), 'original', 'exec')
    transformed_code = compile(ast.fix_missing_locations(ast.Module(body=[transformed], type_ignores=[])), 'transformed', 'exec')
    torch.manual_seed(7)
    ids = [17,18,19,20]
    changed = 0
    for _ in range(354):
        raw = torch.linspace(-.8,.8,128*39).reshape(128,39)
        before = raw[:, ids].clone()
        noise = torch.distributions.Normal(torch.zeros(128,4), torch.ones(128,4)*.1).sample()
        rng = torch.get_rng_state().clone()
        reference = dict(raw=raw.clone(), ids=ids, before=before, noise=noise)
        exec(original_code, reference)
        no_mask = dict(raw=raw.clone(), ids=ids, before=before, applied_noise=noise.clone())
        exec(transformed_code, no_mask)
        assert torch.equal(reference['raw'], no_mask['raw'])
        applied = noise.clone(); applied[:,0] = 0.
        masked = dict(raw=raw.clone(), ids=ids, before=before, applied_noise=applied)
        exec(transformed_code, masked)
        others = [i for i in range(39) if i != 17]
        assert torch.equal(masked['raw'][:,others], reference['raw'][:,others])
        assert torch.equal(applied[:,1:], noise[:,1:]) and bool((applied[:,0] == 0).all())
        changed += int((masked['raw'][:,17] != reference['raw'][:,17]).sum())
        assert torch.equal(rng, torch.get_rng_state())
    assert changed > 0
    old = probe.base.HERE, probe.base.SCHEMA, probe.base.support, probe.base.run
    shared = probe.base.support()
    sentinel = RuntimeError('CPU alias fixture')
    try:
        with probe.execution_scope():
            assert probe.base.HERE == probe.HERE and probe.base.run is not old[3]
            raise sentinel
    except RuntimeError as error:
        assert error is sentinel
    assert (probe.base.HERE, probe.base.SCHEMA, probe.base.support, probe.base.run) == old
    assert shared is probe.base.support()
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True, native_runs=0, controls_tested=354, draw_shape=[128,4],
        full39_zero_mask_bitexact=True, only_action17_changes=True, other3_draws_bitexact=True,
        mask_preserves_RNG=True, aliases_restored_after_error=True, guarded_AST_edits=3,
        original_run_source_sha256=digest)


if __name__ == '__main__':
    import json
    print(json.dumps(check(), indent=2))
