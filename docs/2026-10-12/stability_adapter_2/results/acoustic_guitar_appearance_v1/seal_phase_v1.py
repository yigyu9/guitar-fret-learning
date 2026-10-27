"""Seal appearance evidence without modifying consumed sources or prior artifacts."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

R = Path('/home/ajou/yigyu/3')
A = R/'stability_adapter_2'
P = R/'docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1'
B = P.parent/'realistic_guitar_proportions_v1'
V = R/'docs/2026-10-12/video/acoustic_guitar_appearance_v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact(mapping):
    for path, value in mapping.items():
        assert sha(path) == value, path


def save(name, data):
    file = P/name
    assert not file.exists(), str(file)
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


verification = read(P/'verification_v2.json')
assert verification['passed'] and len(verification['checks']) == 25 and all(verification['checks'].values())
exact(verification['input_sha256'])
exact(read(P/'source_before_native_v1.json'))
for version in (1, 2, 3):
    manifest = read(A/f'assets/acoustic_appearance_v{version}/manifest.json')
    assert all(manifest['checks'].values())
    exact(manifest['input_sha256'])
    exact({manifest['asset']:manifest['asset_sha256']})
    exact({entry['path']:entry['sha256'] for entry in manifest['meshes']})

first, last = read(P/'main_append_v1.json'), read(P/'main_completion_append_v1.json')
main_paths = {entry['path'] for entry in first}
for before, after in zip(first, last):
    assert before['path'] == after['path']
    assert sha(before['snapshot']) == before['before_sha256']
    assert sha(after['snapshot']) == before['after_sha256'] == after['before_sha256']
    assert Path(after['snapshot']).read_bytes().startswith(Path(before['snapshot']).read_bytes())
    assert sha(after['path']) == after['after_sha256']
    assert Path(after['path']).read_bytes().startswith(Path(after['snapshot']).read_bytes())
prior = read(B/'artifact_inventory_v1.json')['files']
for entry in prior:
    path = entry['path']
    original = next(e['snapshot'] for e in first if e['path']==path) if path in main_paths else path
    assert sha(original) == entry['sha256'], path
prior_final = read(B/'final_verification_v1.json')
assert prior_final['passed'] and sha(B/'artifact_inventory_v1.json') == prior_final['inventory_sha256']
assert sha(B/'source_final_v1.json') == prior_final['source_final_sha256']

provenance = read(P/'artifacts_v1/provenance.json')
for path, pair in provenance['inputs_sha256_before_after'].items():
    assert sha(path) == pair['before'] == pair['after'], path
exact(provenance['outputs_sha256'])
assert sha(P/'artifacts_v1/make_appearance_artifacts_v1.py') == provenance['producer_sha256']
videos = read(V/'manifest.json')['videos']
assert len(videos)==4
for video in videos:
    assert sha(video['source']) == sha(video['destination']) == video['source_sha256'] == video['copy_sha256']
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-show_entries','stream=nb_frames,r_frame_rate','-of','json',video['destination']]))
    assert probe['streams'][0]['nb_frames']=='151' and probe['streams'][0]['r_frame_rate']=='30/1'
assert read(P/'native_exit_v1.json')['exit_code']==139
assert all(read(P/f'native_exit_v{version}.json')['exit_code']==0 for version in (2,3))
assert not (P/'verification_v1.json').exists()
review = P/'review_final_v1.md'
assert review.is_file() and review.stat().st_size>0
for doc in [P/'README.md', P/'CHANGED_FILES_V1.md', P/'artifacts_v1/README.md', V/'README.md']:
    for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
        assert Path(re.sub(r':\d+$','',target)).exists(), target

sources = set(main_paths) | {str(p) for p in A.glob('build_acoustic_appearance_v*.py')}
sources |= {str(A/'run_acoustic_appearance_trial_v1.py')} | {str(p) for p in A.glob('ACOUSTIC_GUITAR_APPEARANCE_PLAN_V*.md')}
sources |= {str(p) for p in P.glob('*.py')} | {str(review)}
sources |= {str(p) for p in A.glob('assets/acoustic_appearance_v*/*') if p.is_file()}
save('source_final_v1.json',{path:sha(path) for path in sorted(sources)})
files = {p for p in P.rglob('*') if p.is_file()} | {p for p in V.rglob('*') if p.is_file()}
files |= {Path(path) for path in sources}
inventory = [{'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(files)]
save('artifact_inventory_v1.json',{'files':inventory})
save('final_verification_v1.json',{'passed':True,'native_checks':25,
    'prior_preserved_files':len(prior),'videos_checked':4,'inventory_files':len(inventory),
    'review_sha256':sha(review),'source_final_sha256':sha(P/'source_final_v1.json'),
    'inventory_sha256':sha(P/'artifact_inventory_v1.json'),
    'scope':'appearance/native evidence and preservation; not music or stabilization success'})
print(json.dumps({'passed':True,'prior_files':len(prior),'sealed_files':len(inventory)}))
