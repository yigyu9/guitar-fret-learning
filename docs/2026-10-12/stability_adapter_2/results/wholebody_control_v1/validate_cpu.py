"""CPU validation and immutable input audit, not a native physics trial."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
out = PHASE/'cpu_v1'
out.mkdir(exist_ok=False)
asset = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'
xml = ET.parse(asset).getroot()
meshdir = asset.parent/xml.find('compiler').get('meshdir')
inputs = {asset, Path(__file__).resolve(), ROOT/'stability_adapter_2/__init__.py',
          ROOT/'stability_adapter_2/music_pipeline_v2/control.py',
          ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.json',
          ROOT/'docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/final_verification.json',
          ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json'}
inputs.update((ROOT/'stability_adapter_2/music_pipeline_v3').glob('*.py'))
inputs.update((meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda p, value: p.write_text(json.dumps(value, indent=2)+'\n')
before = {str(p): sha(p) for p in sorted(inputs)}
write(out/'inputs_before.json', before)
for p in inputs:
    if p.suffix == '.py': ast.parse(p.read_text(), filename=str(p))
command = [sys.executable, '-m', 'unittest', '-v', 'stability_adapter_2.music_pipeline_v3.test_control']
with (out/'tests.log').open('w') as stream:
    run = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                         stdout=stream, stderr=subprocess.STDOUT)
after = {str(p): sha(p) for p in sorted(inputs)}
v2 = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/final_verification.json').read_text())['input_union_sha256']
old = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json').read_text())['input_sha256']
changed = lambda mapping: [p for p, digest in mapping.items() if not Path(p).is_file() or sha(Path(p)) != digest]
joints = xml.findall('.//worldbody//joint')
zero = [j.get('name') for j in joints if len(set(map(float, j.get('range').split()))) == 1]
result = dict(scope='synthetic CPU targets/PD commands and original XML topology; no native dynamics or measured torques',
              command=command, python=sys.version, returncode=run.returncode,
              inputs_after=after, changed_inputs=changed(before),
              previous_pipeline_inputs=len(v2), previous_pipeline_changed=changed(v2),
              historical_native_inputs=len(old), historical_native_changed=changed(old),
              asset_joint_channels=len(joints), zero_range_names=zero,
              nonzero_range_joint_channels=len(joints)-len(zero),
              mesh_declarations_pinned=len(xml.findall('./asset/mesh')), native_runs=0)
write(out/'result.json', result)
print((out/'tests.log').read_text())
print(json.dumps({k: result[k] for k in ('returncode','changed_inputs','previous_pipeline_changed',
    'historical_native_changed','asset_joint_channels','nonzero_range_joint_channels','mesh_declarations_pinned')}))
sys.exit(run.returncode or bool(result['changed_inputs']) or bool(result['previous_pipeline_changed']) or bool(result['historical_native_changed']))
