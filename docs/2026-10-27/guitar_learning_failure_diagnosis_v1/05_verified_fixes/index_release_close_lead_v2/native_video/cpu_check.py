"""Stdlib fixture: verify capture ordering and immutable V2 source aliases."""
import ast
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

here = Path(__file__).resolve().parent
module = runpy.run_path(str(here/'render.py'), run_name='video_cpu_fixture')
v2, base = module['v2'], module['base']
events = []


class Tensor:
    def clone(self): return self
    def __sub__(self, value): return 0.
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self
    def copy(self): return [9]*9


class Pool:
    def step(self, action):
        events.append('native')
        return None, [Tensor()], None, None, None, []


class Capture:
    samples = []
    def record(self, *args):
        events.append('capture')
        self.samples.append({})


tree = ast.parse((here/'render.py').read_text())
execute = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'execute')
cls = next(n for n in execute.body if isinstance(n, ast.ClassDef))
scope = dict(shared=SimpleNamespace(Pool=Pool), np=SimpleNamespace(asarray=lambda v: v), __name__='fixture')
exec(compile(ast.Module(body=[cls], type_ignores=[]), str(here/'render.py'), 'exec'), scope)
pool = scope['CapturedPool'].__new__(scope['CapturedPool'])
pool.capture = Capture()
pool.environment = SimpleNamespace(episode_reward_terms={str(i): [Tensor()] for i in range(9)})
assert pool.step(None)[0] is None
assert events == ['native', 'capture'] and pool.capture.samples[0]['reward'] == [9]*9


class BrokenCapture(Capture):
    samples = []
    def record(self, *args):
        super().record(*args)
        raise BrokenPipeError('fixture encoder pipe')


pool.capture = BrokenCapture()
try:
    pool.step(None)
except BrokenPipeError as error:
    assert str(error) == 'fixture encoder pipe'
else:
    raise AssertionError('Capture pipe error was swallowed')
assert set(pool.capture.samples[0]) == {'reward', 'reward_components9'}
old = base.HERE, base.SCHEMA, base.support
base.support = lambda: SimpleNamespace(Pool=Pool, convert=None, compact_episode=None)
try:
    sentinel = base.support
    try:
        with v2.execution_scope():
            raise RuntimeError('fixture')
    except RuntimeError:
        pass
    assert base.HERE == old[0] and base.SCHEMA == old[1] and base.support is sentinel
finally:
    base.HERE, base.SCHEMA, base.support = old
assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
print('PASS: native step before capture, nine rewards, aliases restored, stdlib only; native runs=0')
