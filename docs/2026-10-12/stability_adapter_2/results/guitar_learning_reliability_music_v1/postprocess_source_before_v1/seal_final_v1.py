"""Root-only final preservation and delivery seal, after independent review."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path('/home/ajou/yigyu/3')
PHASE=Path(__file__).resolve().parent
def load(path):return json.loads(path.read_text())
def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()
def write(path,payload):
    with path.open('x') as stream:json.dump(payload,stream,indent=2,allow_nan=False);stream.write('\n')

if __name__=='__main__':
    summary=load(PHASE/'native_summary_v1.json');audit=load(PHASE/'preservation_check_v1.json')
    assert audit['completed']
    assert (PHASE/'review.md').is_file()
    analysis_inputs=load(PHASE/'analysis_inputs_before_v1.json')
    assert all(sha(path)==expected for path,expected in analysis_inputs.items())
    code_before={row['original_path']:row['sha256'] for row in load(PHASE/'source_run_v3/manifest.json') if row['original_path'].endswith('.py')}
    assert all(sha(path)==expected for path,expected in code_before.items())
    log=(PHASE/'cpu_tests_pool_v2.log').read_text()
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s\s+OK',log)
    assert match,log[-500:]
    paths=[p for p in (ROOT/'guitar_learning').rglob('*') if p.is_file() and 'archive' not in p.relative_to(ROOT/'guitar_learning').parts and '__pycache__' not in p.parts]
    paths += [ROOT/'guitar_learning/archive/README.md',ROOT/'stability_adapter_2/PLAN.md',ROOT/'stability_adapter_2/README.md',ROOT/'docs/plans/guitar_learning_reliability_music_20261018.md']
    paths += list(PHASE.glob('*.py'))+list(PHASE.glob('*.md'))
    source=PHASE/'source_final';source.mkdir(exist_ok=False);rows=[]
    for path in sorted(set(paths)):
        target=source/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        assert sha(path)==sha(target)
        rows.append(dict(original_path=str(path),snapshot_path=str(target),sha256=sha(path)))
    write(source/'manifest.json',rows)
    links=[]
    documents=[ROOT/'guitar_learning'/name for name in ('README.md','TRAINING.md','PARALLEL_TRAINING.md','archive/README.md')]+list(PHASE.glob('*.md'))+[ROOT/'docs/plans/guitar_learning_reliability_music_20261018.md']
    for document in documents:
        for target in re.findall(r'\]\((/[^)\n]+)\)',document.read_text()):
            path=target.split('#',1)[0]
            path=re.sub(r':\d+$','',path)
            assert Path(path).exists(),(str(document),target)
            links.append(dict(document=str(document),target=target))
    write(PHASE/'link_check_v1.json',dict(completed=True,count=len(links),links=links))
    runs=audit['runs']
    recovery=summary['recovery_model_checks']
    assert all(value is True for key,value in recovery.items() if key.endswith('_equal'))
    pool=summary['pool_native_v2'];assert set(pool['goal_reset_counts'])=={'0','1','2','3','4'}
    assert all(count>=2 for count in pool['goal_reset_counts'].values())
    native_names=list(runs)
    final=dict(completed=True,scope='requested fixes, bounded native integration and recovery; not musical convergence or long-run memory certification',cpu=dict(tests=int(match.group(1)),wall_s=float(match.group(2)),passed=True),native_runs=runs,committed_transitions=sum(summary[n]['committed_transitions'] for n in native_names),logged_transitions=sum(summary[n]['logged_transitions'] for n in native_names),optimizer_updates_in_bounded_runs=sum(summary[n]['updates'] for n in native_names),recovery_checks=recovery,preservation=audit,postprocess_input_files=len(analysis_inputs),postprocess_inputs_unchanged=True,source_final_files=len(rows),source_final_copies_match=True,final_code_matches_last_run_snapshot=True,local_links_checked=len(links),independent_review=dict(path=str(PHASE/'review.md'),sha256=sha(PHASE/'review.md')),new_eight_hour_run_started_in_this_fix_phase=False,remaining=['musical success/convergence','long-run leak-free operation','pad contact/pressure/vibration/acoustic validation','root-free balance/full song'])
    write(PHASE/'final_verification.json',final)
    files=[p for p in PHASE.rglob('*') if p.is_file() and p.name!='artifact_inventory.json']
    entries=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
    write(PHASE/'artifact_inventory.json',dict(scope='all phase artifacts except this self-referential inventory',files=entries,file_count=len(entries),final_total_files=len(entries)+1))
    print({k:final[k] for k in ('completed','cpu','committed_transitions','logged_transitions','source_final_files','local_links_checked')})
    print('phase files including inventory:',len(entries)+1)
