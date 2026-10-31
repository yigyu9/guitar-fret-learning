"""Synthetic comparison/plot/lifecycle fixtures; no native, model or checkpoint loads."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('warmup_v7_analysis_fixture',HERE/'analyze.py')
a = importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def check():
    wrapper = a.helper();h = wrapper.h
    assert not any(n in sys.modules for n in ('torch','isaacgym'))
    with tempfile.TemporaryDirectory() as temp:
        missing = Path(temp)/'missing-final-artifact'
        with patch.object(a,'required_files',return_value={missing}):
            ready = a.status()
            assert ready['pending'] and not ready['final_ready']
            missing.write_text('fixture')
            assert a.status()['final_ready']
    assert len(a.cases(a.V6)) == len(a.cases(a.V7)) == 9
    assert [(u,s) for u,s,p,c in a.cases(a.V7)] == [(0,False),(0,True),(50,False),(100,False),(150,False),(200,False),(250,False),(300,False),(300,True)]
    sample = h.read(a.V6/'runs/fit_deterministic/evaluation.json')['episodes'][0]
    episodes = [copy.deepcopy(sample) for _ in range(128)]
    for i,e in enumerate(episodes): e['env_id'] = i
    h.audit_evaluation_attempts(dict(assigned_quotas=[1]*128,episodes=episodes))
    summary = h.summarize(episodes,require_settlement=True)
    assert summary['attempts'] == 128 and summary['note_opportunities'] == 384
    # Invalid denominators and duplicate environments must fail rather than shrink the scope.
    for wrong in (episodes[:-1],episodes[:-1]+[episodes[0]]):
        try: h.audit_evaluation_attempts(dict(assigned_quotas=[1]*128,episodes=wrong))
        except ValueError: pass
        else: raise AssertionError('Bad original denominator accepted')
    wrong = copy.deepcopy(episodes[0]);wrong['reward_components']['action_change'] += 1.
    try: h.audit_episode(wrong,require_settlement=True)
    except ValueError: pass
    else: raise AssertionError('Nine reward sum error accepted')
    metric = h.rows(a.V6/'runs/ppo/metrics.jsonl')[0]
    zero = wrapper.cost_proof([metric],0.)
    assert zero['zero_cost_signal_proof']
    positive = copy.deepcopy(metric);positive['mean_failure_cost'] = 1.
    positive['diagnostics']['advantages']['cost_raw']['std'] = .1
    proof = wrapper.cost_proof([positive],1.)
    assert not proof['all_actual_cost_zero'] and not proof['zero_cost_signal_proof']
    assert a.finite_tree(metric) and not a.finite_tree(dict(value=float('nan')))
    invalid_training = copy.deepcopy(summary)
    invalid_training['per_note'][0]['clean_mean'] = float('nan')
    try: a.require(a.finite_tree(invalid_training),'Nonfinite training episode summary')
    except ValueError: pass
    else: raise AssertionError('NaN training note summary accepted')
    invalid_training = copy.deepcopy(summary);invalid_training['cost_sum'] = float('nan')
    try: a.require(a.finite_tree(invalid_training),'Nonfinite training episode summary')
    except ValueError: pass
    else: raise AssertionError('NaN training cost summary accepted')
    report = h.read(a.V6/'runs/fit_deterministic/learning_report.json')
    a.validate_report(report,a.V6,0,h)
    wrong = copy.deepcopy(report);wrong['schema'] = a.SCHEMAS[a.V7]
    try: a.validate_report(wrong,a.V6,0,h)
    except ValueError: pass
    else: raise AssertionError('Wrong schema accepted')
    # Plot only synthetic copies, never a final or partial actual-results claim.
    result = {}
    for version in ('V6','V7'):
        evaluations = []
        for update,stochastic,p,c in a.cases(a.V6):
            e = copy.deepcopy(summary);e.update(update=update,stochastic=stochastic)
            evaluations.append(e)
        metrics = []
        for update in range(1,301):
            m = copy.deepcopy(metric);m['update'] = update;metrics.append(m)
        result[version] = dict(evaluations=evaluations,metrics=metrics,
            training=dict(total_transitions=300*4096,completed_episode_steps=300*4096-17,open_transitions=17,
                          cost_sum=0.,cost_proof=zero),KL=dict(retries=0,actual_actor_lr_range=[metric['actor_lr'],metric['actor_lr']]))
    result['initial_evidence'] = dict(phases_with_MSE_worsening=dict(train=['9'],holdout=['9']))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp);path = root/'source';path.write_text('original')
        pins = {str(path):a.sha(path)}
        with a.lifecycle(root/'success',pins) as out:
            a.plots(result,out);a.results(result,out);a.write(out/'analysis.json',dict(fixture=True))
        verify = a.read(root/'success/verification.json')
        assert verify['completed'] and len(verify['output_sha256']) == 5
        assert '9' in (root/'success/RESULTS.md').read_text()
        try:
            with a.lifecycle(root/'mutation',pins): path.write_text('changed')
        except RuntimeError: pass
        else: raise AssertionError('Input mutation accepted')
        assert not a.read(root/'mutation/verification.json')['completed']
        path.write_text('original')
        try:
            with a.lifecycle(root/'primary',pins): raise RuntimeError('fixture primary')
        except RuntimeError as error: assert str(error) == 'fixture primary'
        else: raise AssertionError('Primary error lost')
        assert a.read(root/'primary/verification.json')['failure']['message'] == 'fixture primary'
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp);source = root/'input';source.write_text('source')
        pins = {str(source):a.sha(source)}
        original_sha = a.sha
        def fail_output_hash(path):
            if Path(path).name == 'analysis.json': raise OSError('secondary output hash fixture')
            return original_sha(path)
        try:
            with patch.object(a,'sha',side_effect=fail_output_hash):
                with a.lifecycle(root/'output_hash_failure',pins) as out:
                    (out/'analysis.json').write_text('fixture')
                    raise RuntimeError('preserved primary output fixture')
        except RuntimeError as error: assert str(error) == 'preserved primary output fixture'
        else: raise AssertionError('Output hash failure replaced primary exception')
    assert not any(n in sys.modules for n in ('torch','isaacgym'))
    return dict(CPU_only=True,native_runs=0,checkpoint_loads=0,NN_forwards=0,training_steps=0,
        frozen_helper_SHA_exact=True,original128_unique_and384_required=True,nine_reward_conservation=True,
        positive_cost_signal_not_assumed_zero=True,wrong_schema_rejected=True,nonfinite_metrics_rejected=True,
        all18_case_schedule=True,synthetic_three_plots_and_Korean_report=True,
        primary_failure_and_input_mutation_verification=True,output_hash_secondary_preserves_primary=True,NaN_training_note_and_cost_rejected=True,missing_artifacts_pending_and_complete_presence_ready=True)

if __name__ == '__main__':
    result = check();a.write(HERE/'cpu_verification.json',result);print(json.dumps(result))
