"""실제 rl38에서 제어 전 관측 복사와 원본 별칭 복구를 확인한다."""
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

module = runpy.run_path(str(Path(__file__).resolve().with_name('capture.py')), run_name='capture_cpu')
assert not any(name in sys.modules for name in ('isaacgym','torch','numpy'))
import torch
torch.set_num_threads(1)
rng = torch.get_rng_state().clone()
base, v2 = module['base'], module['v2']
values = {'state': torch.arange(4*557).reshape(4,557).float(),
          'events': torch.ones(4,48,24), 'mask': torch.ones(4,48,dtype=torch.bool),
          'priority_events': torch.ones(4,8,24), 'priority_mask': torch.ones(4,8,dtype=torch.bool)}
pool = SimpleNamespace(spec={'learned_action_indices':[17,18,19,20]},
    first=torch.ones(4,dtype=torch.bool), observation=values,
    environment=SimpleNamespace(clock=torch.tensor([0,4,8,12]), _local_time=lambda: torch.arange(4)/60),
    controller=SimpleNamespace(target=torch.ones(4,105)))
raw = torch.linspace(-.5,.5,4*39).reshape(4,39)
shared = SimpleNamespace(bounds=lambda pool: (0,0,0), decode=lambda raw,*args: raw+1)
rows = module['collect_rows'](pool, raw, shared)
assert len(rows) == 4 and [row['clock'] for row in rows] == [0,4,8,12]
assert rows[0]['state'].shape == (557,) and rows[0]['raw_goal_normalized'].shape == (4,)
assert torch.equal(torch.from_numpy(rows[0]['decoded_goal_rad']), raw[0,17:21]+1)
for value in values.values():
    value.zero_()
pool.controller.target.zero_(); raw.zero_()
assert rows[0]['state'][1] == 1 and rows[0]['old_target_rad105'][0] == 1
assert rows[0]['raw_goal_normalized'][0] != 0
assert torch.equal(rng, torch.get_rng_state())
old = base.HERE,base.SCHEMA,base.support
original = base.support
try:
    base.support = lambda: SimpleNamespace(Pool=None,convert=None,compact_episode=None)
    with v2.execution_scope():
        base.HERE = module['HERE']
        base.support().reference_raw = lambda pool: None
        raise RuntimeError('restore fixture')
except RuntimeError as error:
    assert str(error) == 'restore fixture'
finally:
    base.support = original
assert (base.HERE,base.SCHEMA,base.support) == old
assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
print(json.dumps(dict(CPU_only=True, native_runs=0, precontrol_rows=4, state_dim=557,
    detached_copy_survives_mutation=True, label_mapping=True, RNG_unchanged=True,
    scope_restored_after_exception=True, interpreter=sys.executable, python=sys.version.split()[0])))
