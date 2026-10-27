"""Read-only analysis of the one3s short-preparation connection probe."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from guitar_learning.geometry_v1 import frame

BASE = Path(__file__).resolve().parent
NATIVE = BASE / 'native_v1'
paths = [Path(__file__).resolve(), Path(frame.__code__.co_filename).resolve(), NATIVE / 'report.json', NATIVE / 'prepared.json', NATIVE / 'final.json', NATIVE / 'initial_values.json', NATIVE / 'measurements240.json.gz']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in paths}
(BASE / 'analysis_inputs_before.json').write_text(json.dumps(pins, indent=2) + '\n')
report = json.loads((NATIVE / 'report.json').read_text())
assert report['completed'] and report['inputs_unchanged']
assert not report['missing_import_pins'] and not report['original_source_parity_errors']
with gzip.open(NATIVE / 'measurements240.json.gz', 'rt') as stream:
    rows = json.load(stream)['rows']
assert len(rows) == 241 and [r['native']['physics_step'] for r in rows] == list(range(480, 721))
assert all(r['native_contacts']['physics_step'] == r['native']['physics_step'] for r in rows)
initial = json.loads((NATIVE / 'initial_values.json').read_text())['native_state']
start_p, start_r = frame(initial['guitar_body_states'][0])
ready_p, ready_r = frame(rows[0]['native']['guitar_body_states'][0])
translations, rotations, support = [], [], []
for row in rows:
    p, r = frame(row['native']['guitar_body_states'][0])
    translations.append(float(np.linalg.norm(p - ready_p)))
    rotations.append(float((ready_r.inv() * r).magnitude()))
    bodies = set()
    for contact in row['native_contacts']['contacts']:
        if contact['lambda'] <= 0:
            continue
        pair = {contact['body0_name'], contact['body1_name']}
        if any(n.startswith('guitar/') for n in pair):
            bodies.update(n for n in pair if n.startswith('human/'))
    support.append(all('human/' + name in bodies for name in ('Chest', 'R_Shoulder', 'R_Hip')))
assert not json.loads((NATIVE / 'final.json').read_text())['forbidden_calls']
result = {
    'completed': True,
    'actual_reset_initial_step': initial['physics_step'],
    'actual_preparation_end_step': rows[0]['native']['physics_step'],
    'actual_final_step': rows[-1]['native']['physics_step'],
    'preparation_seconds': 2,
    'total_new_physics_seconds': 3,
    'post_preparation_samples': len(rows),
    'fretting_candidate_samples': sum(r['fretting_measurement']['fretting_contact_candidate'] for r in rows),
    'last_fretting_progress': rows[-1]['fretting_progress'],
    'triple_support_samples_post_preparation': sum(support),
    'triple_support_fraction_post_preparation': sum(support) / len(rows),
    'max_guitar_translation_from_ready_mm': max(translations) * 1000,
    'max_guitar_rotation_from_ready_deg': float(np.rad2deg(max(rotations))),
    'guitar_translation_initial_to_ready_mm': float(np.linalg.norm(ready_p - start_p) * 1000),
    'guitar_rotation_initial_to_ready_deg': float(np.rad2deg((start_r.inv() * ready_r).magnitude())),
    'reset_description': report['prepared_reset'],
    'import_source_census_passed': True,
    'inputs_unchanged': all(sha(p) == h for p, h in pins.items()),
    'new_training_updates': 0,
    'scope': 'One short reset/handoff connection test; not full V3 validation, learned fretting, string pressure or audio',
}
assert result['actual_reset_initial_step'] == 0 and result['inputs_unchanged']
(BASE / 'native_analysis.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('reset_description', 'last_fretting_progress')}, indent=2))
