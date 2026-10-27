"""Root-only documentation coverage, links and preservation audit."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda p, data: p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
assert (PHASE/'review.md').exists()
assert not (PHASE/'final_verification.json').exists()
inputs = {}
for name in ('inputs_before.json', 'role_index_inputs_before.json'):
    for path, digest in json.loads((PHASE/name).read_text()).items():
        assert path not in inputs or inputs[path] == digest
        assert sha(Path(path)) == digest, path
        inputs[path] = digest
index = json.loads((PHASE/'joint_role_map.json').read_text())
joints = ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot().findall('.//worldbody//joint')
names = [joint.get('name') for joint in joints]
rows = index['joints']
assert len(rows) == len({r['name'] for r in rows}) == 105
assert [r['name'] for r in rows] == names
for row, joint in zip(rows, joints):
    limits = list(map(float, joint.get('range').split()))
    assert row['source_range_degrees'] == limits
    assert row['zero_range'] == (limits[0] == limits[1])
    assert row['role'] in index['role_definitions']
    if row['zero_range']: assert row['proposed_55_target_owner'] == 'reference'
current = {r['name'] for r in rows if r['current_cpu_target_owner'] == 'policy'}
proposed = {r['name'] for r in rows if r['proposed_55_target_owner'] == 'policy'}
lower_added = {r['name'] for r in rows if r['lower_body'] and not r['zero_range']}
assert len(current) == 39 and len(proposed) == 55 and proposed-current == lower_added
assert len(lower_added) == 16 and current <= proposed
prior = {}
for label, path, key in (
    ('wholebody_cpu', 'wholebody_control_v1', 'inputs_sha256'),
    ('music_cpu', 'music_pipeline_v2', 'input_union_sha256'),
    ('historical_native', 'fresh_music_v1', 'input_sha256')):
    mapping = json.loads((PHASE.parent/path/'final_verification.json').read_text())[key]
    assert all(Path(p).is_file() and sha(Path(p)) == digest for p, digest in mapping.items())
    prior[label] = len(mapping)
documents = [PHASE/'README.md', PHASE/'review.md'] + [ROOT/p for p in (
    'PROJECT_CONTEXT.md', 'stability_adapter_2/README.md', 'stability_adapter_2/PLAN.md',
    'docs/plans/music_model_pipeline_20261015.md', 'docs/FRESH_MUSIC_USER_REVIEW.md',
    'docs/plans/joint_role_documentation_20261015.md')]
checked_links = 0
for document in documents:
    for target in re.findall(r'\]\((/home/ajou/[^)]+)\)', document.read_text()):
        if document.parent == PHASE or '/joint_role_design_v1/' in target:
            assert Path(re.sub(r':\d+$', '', target)).exists(), (document, target)
            checked_links += 1
snapshot = PHASE/'source_final'
snapshot.mkdir(exist_ok=False)
copies = {}
for path, digest in inputs.items():
    destination = snapshot/Path(path).relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    assert sha(destination) == digest
    copies[str(destination.relative_to(PHASE))] = digest
write(PHASE/'final_verification.json', dict(
    scope='documentation and 105-joint role index; runtime code and native experiments unchanged',
    joint_count=105, current_policy_count=39, proposed_policy_count=55, lower_added_count=16,
    zero_range_count=8, proposed_reference_count=50, new_native_runs=0, new_training_runs=0,
    input_sha256=inputs, source_final_sha256=copies, prior_inputs_unchanged=prior,
    checked_local_links=checked_links, document_sha256={str(p): sha(p) for p in documents},
    role_index_sha256=sha(PHASE/'joint_role_map.json'), verification_source_sha256=sha(Path(__file__).resolve())))
files = {str(p.relative_to(PHASE)): dict(sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(PHASE.rglob('*')) if p.is_file()}
write(PHASE/'artifact_inventory.json', dict(scope='phase files excluding this inventory', files=files))
print(json.dumps(dict(joints=105, current_policy=39, proposed_policy=55,
                     checked_local_links=checked_links, prior_inputs_unchanged=prior, phase_files=len(files))))
