"""Synthetic negative fixtures and immutable initial-data helper check; no live run read."""
import copy
import json
import os
from pathlib import Path
import analyze as a


def rejected(fn):
    try:
        fn()
    except (ValueError,KeyError):
        return True
    raise AssertionError('invalid input admitted')


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    checks={}
    checks['missing_mode_rejected']=rejected(lambda:a.audit_mode({'checkpoint_updates':0},0,False))
    checks['wrong_mode_rejected']=rejected(lambda:a.audit_mode({'checkpoint_updates':0,'stochastic':True},0,False))
    ev={'assigned_quotas':[1]*128,'episodes':[{'env_id':i} for i in range(128)]}
    a.h.audit_evaluation_attempts(ev)
    ev['episodes'][-1]['env_id']=0
    checks['duplicate_env_rejected']=rejected(lambda:a.h.audit_evaluation_attempts(ev))
    ep=a.read(a.V6/'runs/fit_deterministic/evaluation.json')['episodes'][0]
    a.h.audit_episode(ep,require_settlement=True)
    bad=copy.deepcopy(ep);del bad['success_settlement']
    checks['missing_ledger_rejected']=rejected(lambda:a.h.audit_episode(bad,require_settlement=True))
    bad=copy.deepcopy(ep);bad['success_settlement']['settlement_paid']+=.001
    checks['bad_ledger_conservation_rejected']=rejected(lambda:a.h.audit_episode(bad,require_settlement=True))
    checks['reward_sum_rejected']=rejected(lambda:a.h.audit_episode(dict(ep,reward=ep['reward']+1),require_settlement=True))
    z=dict(count=4096,nonfinite_count=0,mean=0.,std=0.,min=0.,max=0.)
    m=dict(update=1,cost_value_loss=0.,cost_value_loss_last=0.,cost_weight=1.,mean_failure_cost=0.,diagnostics=dict(
        valid_decisions=4096,physical_transitions=4096,advantages=dict(cost_weight_used=1.,cost_raw=copy.deepcopy(z)),
        post_update=dict(critics=dict(cost=dict(value=copy.deepcopy(z),target=copy.deepcopy(z),mse=0.))),
        minibatches=dict(value=dict(sample_weighted_mean=dict(cost_loss=0.),max=dict(cost_loss=0.)))))
    assert a.cost_proof([m],0)['zero_cost_signal_proof']
    for key in ['cost_raw','value','target']:
        bad=copy.deepcopy(m)
        dest=bad['diagnostics']['advantages']['cost_raw'] if key=='cost_raw' else bad['diagnostics']['post_update']['critics']['cost'][key]
        dest['max']=1e-20
        checks['nonzero_'+key+'_proof_refused']=not a.cost_proof([bad],0)['zero_cost_signal_proof']
    bad=copy.deepcopy(m);bad['cost_value_loss']=1e-20
    checks['nonzero_cost_loss_proof_refused']=not a.cost_proof([bad],0)['zero_cost_signal_proof']
    bad=copy.deepcopy(m);bad['mean_failure_cost']=.01
    checks['positive_real_cost_does_not_imply_zero']=not a.cost_proof([bad],1)['zero_cost_signal_proof']
    checks['incomplete_zero_sample_rejected']=rejected(lambda:a.zero_summary(dict(z,count=4095)))
    checks['nonfinite_zero_sample_rejected']=rejected(lambda:a.zero_summary(dict(z,nonfinite_count=1)))
    bad=copy.deepcopy(m);bad['cost_weight']=0.
    checks['disabled_cost_weight_rejected']=rejected(lambda:a.cost_proof([bad],0))
    # Completed initial data only; exercise actual frozen helper compatibility and V6 schemas.
    files=set()
    for root in [a.V5,a.V6]:
        for case in a.cases(root)[:2]:
            summary=a.evaluation(root,case,files)
            assert summary['attempts']==128 and summary['note_opportunities']==384
            a.checkpoint(case[3],root,0)
    checks['four_actual_initial_evaluations_pass']=True
    a.initial_evidence(files)
    checks['actual_initial_69_plus_2_rechecked']=True
    assert all(checks.values())
    out=dict(all_checks_passed=True,checks=checks,python_version=__import__('sys').version,new_GPU_runs=0,new_NN_runs=0,
             source_sha256={str(p):a.sha(p) for p in [Path(__file__),Path(a.__file__),a.HELPER]})
    (a.OUT/'cpu_verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))


if __name__=='__main__':main()
