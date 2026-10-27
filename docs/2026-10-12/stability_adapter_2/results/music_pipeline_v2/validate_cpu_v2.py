"""Preserve before/after inputs and CPU-only test results in a new directory."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
out.mkdir(exist_ok=False)
inputs = set((ROOT/'stability_adapter_2/music_pipeline_v2').glob('*.py'))
inputs.add(Path(__file__).resolve())
for relative in ('stability_adapter_2/__init__.py', 'stability_adapter_2/fresh_music_v1/events.py',
                 'tab2body/env/__init__.py', 'tab2body/env/strike_goal_compiler.py', 'tab2body/full/events.py',
                 'stability_adapter_2/chest_upperarm_pose_test_v1/initial.json',
                 'docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/config_v1/body9_effort_reference.json',
                 'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json'):
    inputs.add(ROOT/relative)
for song in ('05_BN2-131-B_solo', '00_SS1-68-E_comp'):
    inputs.update(p for p in (ROOT/'data/song_bundles'/song).rglob('*') if p.is_file())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): sha(p) for p in sorted(inputs)}
(out/'inputs_before.json').write_text(json.dumps(before, indent=2)+'\n')
syntax = []
for p in sorted(inputs):
    if p.suffix == '.py':
        ast.parse(p.read_text(), filename=str(p)); syntax.append(str(p))
command = [sys.executable, '-m', 'unittest', '-v'] + [
    'stability_adapter_2.music_pipeline_v2.test_'+name for name in ('control_v2', 'music', 'policy', 'ppo', 'integration_v2')]
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
with (out/'tests.log').open('w') as stream:
    completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
after = {str(p): sha(p) for p in sorted(inputs)}
old = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json').read_text())['input_sha256']
old_changed = [p for p, digest in old.items() if not Path(p).is_file() or sha(Path(p)) != digest]
result = dict(scope='CPU unit and integration tests; synthetic physics/reward fixtures; no native simulation or music training',
              command=command, python=sys.version, returncode=completed.returncode,
              syntax_checked=syntax, input_count=len(before), inputs_after=after,
              changed_inputs=[p for p in before if before[p] != after[p]],
              historical_native_input_count=len(old), historical_native_inputs_changed=old_changed)
(out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print((out/'tests.log').read_text())
print(json.dumps({k: result[k] for k in ('returncode','input_count','changed_inputs','historical_native_input_count','historical_native_inputs_changed')}))
sys.exit(completed.returncode or bool(result['changed_inputs']) or bool(old_changed))
