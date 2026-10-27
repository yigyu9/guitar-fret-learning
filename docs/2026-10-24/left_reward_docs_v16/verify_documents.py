"""Check this documentation revision without importing training/native code."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
DOCS = ROOT/'docs/2026-10-26/왼손보상구조'
RUN = ROOT/'docs/2026-10-23/guitar_learning_long_training_v16'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    manifest_path = RUN/'training_source_manifest.json'
    pins = json.loads(manifest_path.read_text())['source']
    active = {str(p.resolve()) for p in (ROOT/'guitar_learning').rglob('*.py')
              if 'archive' not in p.relative_to(ROOT/'guitar_learning').parts}
    assert len(pins) == 451 and set(pins) == active
    for path, digest in pins.items():
        assert sha(Path(path)) == digest, path
        ast.parse(Path(path).read_text(), filename=path)
    backup_path = PHASE/'backup_manifest.json'
    backups = json.loads(backup_path.read_text())['files_sha256']
    for name, digest in backups.items():
        assert sha(PHASE/'before'/name) == digest, name
    assert len(backups) == 16
    inputs = json.loads((RUN/'train2000/inputs_before.json').read_text())
    assert '왼손보상구조' not in json.dumps(inputs, ensure_ascii=False)
    snapshot = json.loads((PHASE/'training_status_snapshot.json').read_text())
    observed = snapshot['pipeline_status.json']
    assert not observed['completed'] and observed['stage'] == 'waiting_for_training'
    assert snapshot['preflight_verification.json']['completed']
    for stage, updates, transitions in [('smoke_1024', 12, 393216),
                                        ('resume_1024', 13, 32768)]:
        report = json.loads((RUN/stage/'report.json').read_text())
        assert report['completed'] and report['lifecycle_verified']
        assert report['optimizer_updates'] == updates and report['transitions'] == transitions
        assert not any(report[key] for key in ('failure', 'cleanup_errors', 'changed_inputs',
                                              'missing_import_pins'))
    # These source anchors locate the implementation reviewed in the prose;
    # they do not substitute for the sealed implementation's numerical tests.
    anchors = {
        'guitar_learning/gpu/environment.py': [
            'guitar_learning.gpu_tensor_song_reward.v16',
            'guitar_learning.surface_fretting.v7',
            'guitar_learning.left_surface_events.v4',
            'guitar_learning.gpu_action_change.v2',
            'excess = (action_change.abs()-.05).clamp_min(0)',
            'self.terms[\'song_finger_standby\'] += posture[\'rate\']/240.',
            'deficit = (1-self.note[\'best_clean_streak\']/self.required).clamp(0, 1)'],
        'guitar_learning/gpu/wrist_region.py': [
            'along_half_width_m=.06', 'below_lower_edge_m=[.01, .08]',
            'behind_board_m=[.02, .11]'],
        'guitar_learning/gpu/fingertip_pad.py': ['guitar_learning.gpu_finger_tracking_rate.v7'],
        'guitar_learning/gpu/finger_reward.py': ['guitar_learning.gpu_finger_preparation_rate.v1'],
    }
    locations = {}
    for name, fragments in anchors.items():
        lines = (ROOT/name).read_text().splitlines()
        locations[name] = {}
        for fragment in fragments:
            matches = [i+1 for i, line in enumerate(lines) if fragment in line]
            assert matches, (name, fragment)
            locations[name][fragment] = matches
    links = []
    for path in sorted(DOCS.glob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            local = re.sub(r':\d+$', '', target.split('#')[0])
            resolved = Path(local)
            if not resolved.is_absolute():
                resolved = path.parent/resolved
            assert resolved.exists(), (str(path), target)
            links.append(dict(document=path.name, target=target))
    evidence = [manifest_path, PHASE/'training_status_snapshot.json', backup_path,
                RUN/'preflight_verification.json', RUN/'smoke_1024/report.json',
                RUN/'resume_1024/report.json',
                ROOT/'docs/2026-10-23/guitar_learning_action_change_v1/delivery_manifest.json']
    audit = dict(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        checked_date_kst='2026-10-24', reward_schema='guitar_learning.gpu_tensor_song_reward.v16',
        scope='Documentation only; static source and preserved execution evidence readback',
        source_manifest=str(manifest_path), source_paths_sha256=pins,
        active_python_files_verified=len(pins), source_changed=False,
        source_anchor_lines=locations, evidence_sha256={str(p): sha(p) for p in evidence},
        training_status_snapshot=str(PHASE/'training_status_snapshot.json'),
        gpu_or_training_executed_by_this_documentation_task=False)
    write(DOCS/'source_audit.json', audit)
    review = json.loads((PHASE/'independent_review.json').read_text()) if (PHASE/'independent_review.json').exists() else None
    if review:
        assert review['verdict'] == 'PASS' and not review['unresolved_findings']
        prose_names = {p.name for p in DOCS.glob('*.md') if p.name != 'independent_review.md'}
        assert len(prose_names) == 12 and set(review['reviewed_prose_sha256']) == prose_names
        for name, digest in review['reviewed_prose_sha256'].items():
            assert sha(DOCS/name) == digest, name
    else:
        write(PHASE/'pre_review_source_audit.json', audit)
    result = dict(completed=True, phase='final' if review else 'pre_final_review',
        checked_date_kst='2026-10-24', scope=audit['scope'], reward_schema=audit['reward_schema'],
        active_python_unchanged=len(pins), source_manifest_match=True, ast_parse_count=len(pins),
        preserved_original_files=len(backups), backup_sha_match=True,
        local_links_checked=len(links), missing_links=[], training_inputs_overlap=False,
        training_status='in progress at the preserved observation time; not final results',
        new_gpu_native_training_executed=False, implementation_tests_rerun=False,
        review_pending=not bool(review), independent_review=review,
        source_audit_path=str(DOCS/'source_audit.json' if review else PHASE/'pre_review_source_audit.json'),
        source_audit_sha256=sha(DOCS/'source_audit.json'))
    if review:
        result['files_sha256'] = {p.name: sha(p) for p in sorted(DOCS.iterdir())
                                 if p.is_file() and p.name != 'verification.json'}
        write(DOCS/'verification.json', result)
    else:
        write(DOCS/'verification_pre_review.json', result)
    print(json.dumps({k: result[k] for k in ('phase', 'active_python_unchanged',
        'preserved_original_files', 'local_links_checked', 'review_pending')}))


if __name__ == '__main__':
    main()
