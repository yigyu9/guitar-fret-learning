"""Meaningful CPU fixtures exercise rejection gates; never run simulation."""
import copy
import importlib.util
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('settlement_analysis',HERE/'analyze.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def rejected(fn):
    try:
        fn()
    except (ValueError,FileNotFoundError):
        return True
    raise AssertionError('invalid fixture accepted')


assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
base=a.read(a.V5/'runs/fit_deterministic/evaluation.json')['episodes'][0]
a.audit_episode(base)
checks={}
ep=copy.deepcopy(base);del ep['success_settlement']
checks['reject_missing_V5_training_ledger']=rejected(lambda:a.summarize([ep],require_settlement=True))
checks['V4_missing_ledger_explicitly_allowed']=a.summarize([ep],require_settlement=False)['attempts']==1
ev=copy.deepcopy(a.read(a.V5/'runs/fit_deterministic/evaluation.json'))
ev['episodes'][127]['env_id']=126
checks['reject_duplicate_and_missing_env']=rejected(lambda:a.audit_evaluation_attempts(ev))
ev['episodes'][127]['env_id']=128
checks['reject_out_of_range_env']=rejected(lambda:a.audit_evaluation_attempts(ev))
for field,value in [('settlement_paid',.5),('settlement_entitled_raw',.5),('settlement_pending_raw',.1),('settlement_time_s',3.2703),('settlement_removed_raw',0)]:
    ep=copy.deepcopy(base);ep['success_settlement'][field]=value
    checks['reject_'+field]=rejected(lambda:a.audit_episode(ep))
ep=copy.deepcopy(base);ep['reward']+=.01
checks['reject_reward_sum']=rejected(lambda:a.audit_episode(ep))
checks['reject_wrong_mode']=rejected(lambda:a.evaluation(a.V5,(0,True,a.V5/'runs/fit_stochastic',a.V5/'runs/fit/fit.pt')))
checks['reject_missing_report']=rejected(lambda:a.read(HERE/'missing_report_fixture.json'))
checks['actual_initial_deterministic']=a.evaluation(a.V5,a.cases(a.V5)[0])['attempts']==128
checks['actual_initial_stochastic']=a.evaluation(a.V5,a.cases(a.V5)[1])['attempts']==128
checks['actual_v4_completed_training']=a.training(a.V4)[0]['transitions']==1228800
result={'python':__import__('sys').version,'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'checks':checks,'all_checks_passed':all(checks.values()),'GPU_runs':0,'NN_runs':0}
(HERE/'cpu_fixture_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
