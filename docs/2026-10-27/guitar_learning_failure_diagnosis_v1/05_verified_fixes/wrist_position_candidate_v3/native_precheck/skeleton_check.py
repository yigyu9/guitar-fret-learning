"""Dry-plan/output-guard only; no active runtime, CPU final audit or native import."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import run_precheck as run


def main():
    old = run.reused()
    previous = run.load(run.PREVIOUS/'run_regression.py', 'candidate_v3_skeleton_previous')
    plan = run.jobs()
    assert len(plan) == 8 and len({j['out'] for j in plan}) == 8
    assert [j['name'] for j in plan] == [f+'_'+c for f in ('index','middle') for c in ('initial','reference','zero','random')]
    for jobs, source, prior_path in ((plan[:4],old.jobs()[:4],run.OLD/'runs'),(plan[4:],previous.jobs()[:4],run.PREVIOUS/'runs')):
        for actual, prior in zip(jobs,source):
            restored = copy.deepcopy(actual)
            restored['out'] = restored['out'].replace(str(run.HERE/'runs'),str(prior_path))
            restored['args'] = [v.replace(str(run.HERE/'runs'),str(prior_path)) for v in restored['args']]
            assert restored == prior
            assert restored['args'][restored['args'].index('-m')+1] == old.MODULE
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'out';path.mkdir();sentinel=path/'keep';sentinel.write_bytes(b'keep')
        link = Path(temp)/'dangling';link.symlink_to(Path(temp)/'missing')
        for existing in (path,link):
            try:run.reject_existing(existing)
            except FileExistsError:pass
            else:raise AssertionError('Existing output accepted')
        assert sentinel.read_bytes()==b'keep' and list(path.iterdir())==[sentinel]
    for p in run.HERE.glob('*.py'):ast.parse(p.read_text(),feature_version=(3,8))
    import sys
    assert 'isaacgym' not in sys.modules and 'torch' not in sys.modules
    baseline=old.original()
    baseline.write(run.HERE/'dry_run.json',dict(jobs=plan,GPU_executed=False,old_checkpoints_used=False))
    baseline.write(run.HERE/'skeleton_verification.json',dict(CPU_only=True,GPU_executed=False,native_executed=False,
        active_runtime_imported=False,jobs8_exact_original_except_run_paths=True,standard_module_CLI=True,
        index_row1_middle_row8_paths_unchanged=True,own_fresh_initial_only=True,
        existing_output_and_dangling_symlink_rejected=True,existing_output_unchanged=True,python38_syntax=True,
        final_CPU_or_seal_or_review_executed=False))
    print('Eight standard-CLI stages; skeleton/output guards passed; no active runtime/native import')


if __name__=='__main__':main()
