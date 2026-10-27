"""Root-owned completion and preservation audit after independent review."""
import hashlib
import json
import re
import shutil
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
RUN=OUT/'run_v1'


def read(p):return json.loads(p.read_text())


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def write(name,d):
    with (OUT/name).open('x') as f:json.dump(d,f,indent=2,ensure_ascii=False,allow_nan=False)


def main():
    assert (OUT/'review.md').is_file()
    report=read(RUN/'report.json');assert report['completed']
    assert read(RUN/'persistent_audit.json')['completed']
    assert read(OUT/'learning_verification.json')['completed'] and read(OUT/'plot_verification.json')['completed']
    assert read(OUT/'plot_verification_v2.json')['completed']
    assert read(OUT/'preparation_verification.json')['completed']
    runtime=read(OUT/'runtime_verification.json')
    assert runtime['analysis_integrity_passed'] and runtime['training_completed_and_persistent_audit_passed']
    learning=read(OUT/'learning_analysis.json');assert learning['partial_collection']['counts_consistent']
    assert learning['checkpoint']['finite'] and all(learning['checkpoint']['restored_fields_identical'].values())
    checks=('changed_inputs','missing_import_pins','original_source_parity_errors','missing_worker_audits',
        'worker_audit_read_errors','guard_violations','physical_flags_errors','worker_failures','cleanup_errors')
    assert not any(report[key] for key in checks)
    pins={}
    for path in (RUN/'inputs_before.json',OUT/'learning_inputs_before.json',OUT/'plot_inputs_before.json',OUT/'plot_inputs_before_v2.json',OUT/'preparation_inputs_before.json'):
        for name,value in read(path).items():
            assert name not in pins or pins[name]==value
            pins[name]=value
    for name,value in read(OUT/'runtime_inputs_before.json')['sha256'].items():
        assert value is not None and (name not in pins or pins[name]==value)
        pins[name]=value
    for row in read(OUT/'source_run_v1/manifest.json'):
        assert sha(Path(row['original_path']))==row['sha256']
        assert sha(Path(row['snapshot_path']))==row['sha256']
    for row in read(OUT/'main_before/manifest.json'):
        assert sha(Path(row['snapshot_path']))==row['sha256']
    for manifest in OUT.glob('analysis_before_*/manifest.json'):
        row=read(manifest);assert sha(Path(row['snapshot_path']))==row['sha256']
    for row in read(OUT/'plot_before_legend_fix/manifest.json'):
        assert sha(Path(row['snapshot_path']))==row['sha256']
    changed=[name for name,value in pins.items() if not Path(name).is_file() or sha(Path(name))!=value]
    assert not changed,changed
    write('inputs_union.json',pins)
    broken=[]
    for target in re.findall(r'\]\((/[^)]+)\)',(OUT/'README.md').read_text()):
        if not Path(target.split('#')[0]).exists():broken.append(target)
    assert not broken,broken
    final=OUT/'source_final';final.mkdir();rows=[]
    files=list(OUT.glob('*.py'))+[OUT/'README.md',ROOT/'docs/plans/guitar_learning_persistent_training_20261018.md',
        ROOT/'stability_adapter_2/PLAN.md',ROOT/'stability_adapter_2/README.md']
    for p in files:
        t=final/p.relative_to(ROOT);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
        rows.append(dict(original_path=str(p),snapshot_path=str(t),sha256=sha(p)))
    with (final/'manifest.json').open('x') as f:json.dump(rows,f,indent=2)
    inventory={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in OUT.rglob('*') if p.is_file()}
    write('artifact_inventory.json',inventory)
    write('final_verification.json',dict(completed=True,training_completed=report['completed'],stopped=report['stopped'],
        updates_in_run=learning['completed_updates'],cumulative_updates=learning['checkpoint']['final_updates'],
        committed_transitions=report['transitions'],persistent_lifecycle_completed=True,
        declared_input_count=len(pins),changed_inputs=changed,broken_links=broken,
        source_final_count=len(rows),artifact_count=len(inventory),review_sha256=sha(OUT/'review.md'),
        scope='Declared native/analysis/plot inputs and snapshots. Inventory excludes itself and this verification. No claim of musical success or leak-free execution beyond observed results.'))


if __name__=='__main__':main()
