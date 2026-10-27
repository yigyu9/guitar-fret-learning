"""Explicit supported single-note pools; no silent source-event filtering."""
import copy
from dataclasses import asdict
import random
from .music_task import ScoreTask
from .training_environment import TrainingEnvironment
from .dense_environment import DenseTrainingEnvironment


class BalancedTaskSampler:
    def __init__(self,indices,seed,worker_id):
        if (not isinstance(indices,list) or not indices or
                any(type(i) is not int or i < 0 for i in indices) or len(set(indices)) != len(indices)):
            raise ValueError('nonempty unique explicit nonnegative event indices required')
        if type(seed) is not int or type(worker_id) is not int or worker_id < 0:
            raise ValueError('integer seed and nonnegative worker id required')
        self.indices=tuple(indices)
        self.random=random.Random(seed+worker_id)
        self.remaining=[]

    def next_index(self):
        if not self.remaining:
            self.remaining=list(self.indices)
            self.random.shuffle(self.remaining)
        return self.remaining.pop()


class SampledTaskEnvironment:
    """Retask before reset; expose one stable pool contract to the policy."""
    def __init__(self,environment,tasks,sampler):
        self.environment,self.tasks,self.sampler=environment,tasks,sampler
        duration_scale=max(1.,max(task.duration_s for task in tasks.values()))
        self.state_scale_overrides={name:duration_scale for name in
            ('music.remaining_s','music.held_total_s','music.elapsed_s')}
        self.pool_contract=dict(schema='guitar_learning.explicit_single_note_pool.v2',
            selection='seed+worker_id shuffle without replacement each cycle',stage='B',
            state_scale_overrides=self.state_scale_overrides.copy(),
            goal_event_indices=list(sampler.indices),
            candidates=[dict(event_index=i,provenance=copy.deepcopy(t.provenance),
                duration_s=t.duration_s,targets=[asdict(x) for x in t.targets]) for i,t in tasks.items()])

    def __getattr__(self,name):
        return getattr(self.environment,name)

    def reset(self):
        index=self.sampler.next_index()
        self.environment.task=self.tasks[index]
        _,info=self.environment.reset()
        self.episode_task=dict(event_index=index,task=copy.deepcopy(self.environment.contract['task']))
        builder=self.environment.builder
        for name,scale in self.state_scale_overrides.items():
            builder.scales[builder.fields.index(name)]=scale
        builder.spec['scales']=builder.scales.tolist()
        self.environment.contract['observation']=copy.deepcopy(builder.spec)
        self.environment.contract['task']=copy.deepcopy(self.pool_contract)
        self.contract=self.environment.contract
        info['training_contract']=self.contract
        info['episode_task']=copy.deepcopy(self.episode_task)
        return self.environment._observation(),info

    def step(self,action):
        observation,reward,terminated,truncated,info=self.environment.step(action)
        info['episode_task']=copy.deepcopy(self.episode_task)
        if 'episode' in info:
            info['episode']['episode_task']=copy.deepcopy(self.episode_task)
        return observation,reward,terminated,truncated,info

    def close(self):
        self.environment.close()


def build_environment(config,out,*,bundle,stage,start_event_index,phrase_events,
                      tempo_scale,seed,worker_id,music=None,**kwargs):
    music=dict(music or {})
    if set(music)-{'reward_mode','goal_event_indices'}:
        raise ValueError('unknown music configuration')
    mode=music.get('reward_mode','legacy')
    if mode not in ('legacy','dense_v2'):
        raise ValueError('reward_mode must be legacy or dense_v2')
    cls=TrainingEnvironment if mode=='legacy' else DenseTrainingEnvironment
    indices=music.get('goal_event_indices')
    if indices is None:
        task=ScoreTask.from_bundle(bundle,stage=stage,start_event_index=start_event_index,
            phrase_events=phrase_events,tempo_scale=tempo_scale)
        return cls(config,out,task=task,**kwargs)
    if stage != 'B':
        raise ValueError('explicit goal pool currently requires single-note stage B')
    sampler=BalancedTaskSampler(indices,seed,worker_id)
    # Validate every explicitly requested event before creating any simulator.
    tasks={i:ScoreTask.from_bundle(bundle,stage='B',start_event_index=i,
                                 tempo_scale=tempo_scale) for i in indices}
    environment=cls(config,out,task=tasks[indices[0]],**kwargs)
    return SampledTaskEnvironment(environment,tasks,sampler)
