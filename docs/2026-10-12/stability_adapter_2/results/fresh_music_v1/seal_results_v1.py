"""Root audit of completed v4 runs; historical failures retain their own status."""
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    with (BASE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


assert PROJECT == Path('/home/ajou/yigyu/3')
audit = {}
union = {}
for name in ('pilot_b16_v4', 'baseline_b_v4', 'baseline_d_v4', 'eval_b16_v4'):
    run = BASE / name
    attempt, report = read(run / 'attempt.json'), read(run / 'report.json')
    hashes = attempt['input_sha256']
    changed = [p for p, digest in hashes.items() if sha(p) != digest]
    assert not changed and report['completed'] and not report['changed_inputs']
    assert not report['process_counters']['forbidden_calls'] and not report['old_policy_loaded']
    audit[name] = dict(input_count=len(hashes), changed_now=changed, completed=True,
                      report_sha256=sha(run / 'report.json'), forbidden_calls=[])
    for path, digest in hashes.items():
        assert path not in union or union[path] == digest
        union[path] = digest

qualification = read(BASE / 'guard_qualification_v2/report.json')
assert qualification['all_cases_passed'] and qualification['inputs_unchanged']
replay = qualification['results'][0]
assert replay['counters']['controls'] == 153 and replay['prefix_checks']['compared_controls'] == 152
assert replay['prefix_checks']['all_exact'] and replay['physics_step'] == 612
mesh_closure = {}
for name in union:
    if not name.endswith('.xml'):
        continue
    path = Path(name)
    tree = ET.parse(path).getroot()
    compiler = tree.find('compiler')
    directory = path.parent / (compiler.get('meshdir', '') if compiler is not None else '')
    meshes = [str((directory / m.get('file')).resolve()) for m in tree.findall('./asset/mesh') if m.get('file')]
    missing = [p for p in meshes if p not in union]
    assert not missing
    mesh_closure[name] = dict(declared_meshes=len(meshes), missing=missing)

analysis = read(BASE / 'analysis_v1.json')
assert analysis['analysis_inputs_unchanged']
assert all(sha(p) == digest for p, digest in read(BASE / 'analysis_inputs_before.json').items())
source_final = BASE / 'source_final'
source_final.mkdir(exist_ok=False)
copies = {}
paths = [Path(p) for p in union if Path(p).suffix in ('.py', '.sh', '.json', '.md', '.xml') and PROJECT in Path(p).parents]
paths += [BASE / 'summarize_results_v1.py', Path(__file__).resolve()]
for path in paths:
    target = source_final / path.relative_to(PROJECT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    assert sha(path) == sha(target)
    copies[str(target.relative_to(BASE))] = sha(target)
save('final_verification.json', dict(scope='Completed v4 runs and current input closure; historical failures are not overwritten',
    latest_runs_passed=True, runs=audit, qualification_v2_passed=True, mesh_closure=mesh_closure,
    input_sha256=union, source_final_sha256=copies, analysis_sha256=sha(BASE / 'analysis_v1.json'),
    historical_exceptions=['pilot_b16_v2 failed before any update', 'qualificationv1 random amplitude .8 failed',
        'qualificationv1 input changed during execution; original false report preserved; v2 rerun is separate'],
    performance='16 updates completed; first-note hold/release candidate incomplete; negligible evaluation approach improvement',
    remaining_scope=['No string force/sound verification', 'Root and lower body fixed',
                     'No C/D learned performance or generalization claim', 'Visual geometry warnings remain']))
print('Verified and copied', len(copies), 'source/config files; input union', len(union))
