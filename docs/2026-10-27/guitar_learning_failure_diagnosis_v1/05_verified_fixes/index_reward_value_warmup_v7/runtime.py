"""V7 changes reward-value initialization only; V6 physics/actor/cost are retained."""
import copy
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_cost_prior_zero_v6'
spec = importlib.util.spec_from_file_location('warmup_v7_v6_runtime',SOURCE/'runtime.py')
v6 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v6
spec.loader.exec_module(v6)
base,v2,ADAPTER,shared = v6.base,v6.v2,v6.ADAPTER,v6.shared
SCHEMA = 'diagnostic.reward_value_warmup.v7'
COST_PRIOR = v6.COST_PRIOR
WARMUP = dict(schema=SCHEMA,steps=1000,batch_size=512,gamma=.99,train_envs=[0,95],
    holdout_envs=[96,127],target='realized354tickMC_actualterminal_no_bootstrap',
    parameters=['value_encoder','reward_critic'],temporary_optimizer='Adam_existing_value_lr_and_grad_cap',
    dataset='V6fit_stochastic12buffers_only',actor_fit_steps=1000)


def attach(contract):
    result = v6.attach(contract)
    result['diagnostics']['reward_value_warmup'] = copy.deepcopy(WARMUP)
    return result


def settings():
    result = v6.settings()
    result['simple_start']['initialization'] = 'fresh V7 identical V6 actorfit1000; reward value MC warmup1000; PPO300'
    return result


class GoalPolicy(v6.GoalPolicy):
    schema = SCHEMA+'.goal_policy'
    def __init__(self,*,contract,size='large'):
        if contract.get('diagnostics',{}).get('reward_value_warmup') != WARMUP:
            raise ValueError('Own V7 reward-value warmup contract required')
        super().__init__(contract=contract,size=size)


class GoalPool(v6.GoalPool):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        try:
            self.contract = attach(self.contract)
            self.environment.contract['diagnostics']['reward_value_warmup'] = copy.deepcopy(WARMUP)
        except BaseException:
            self.close()
            raise

Environment,sigma4 = v6.Environment,v6.sigma4
