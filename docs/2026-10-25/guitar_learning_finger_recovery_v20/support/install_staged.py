"""Install reviewed v20 only after immutable v19 evaluation and archive checks."""
import hashlib
import json
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    baseline = json.loads((PHASE/'baseline_v19/checkpoint_evaluation.json').read_text())
    assert baseline['evaluated_updates'] == [500,3000]
    summaries = []
    for label in ('evaluation_update_0500_1024','evaluation_final_1024'):
        folder = PHASE/'baseline_v19'/label
        report = json.loads((folder/'report.json').read_text())
        assert report['completed'] and len(report['episodes']) == 1024
        pins = json.loads((folder/'inputs_before.json').read_text())
        assert all(sha(Path(path))==value for path,value in pins.items())
        es=report['episodes']
        summaries.append(dict(updates=report['source_optimizer_updates'],episodes=len(es),
            mean_notes=sum(e['song']['left_success_count'] for e in es)/len(es),
            safe=sum(e['reason']=='timeline_complete' for e in es),
            input_pins_verified=len(pins),report_sha256=sha(folder/'report.json')))
    before = json.loads((PHASE/'baseline_sources.json').read_text())
    archive = ROOT/'guitar_learning/archive/20261025_before_finger_recovery_v20'
    assert all(sha(ROOT/path)==value and sha(archive/path)==value for path,value in before.items())
    review=json.loads((PHASE/'independent_review.json').read_text())
    assert review['summary']=='문제없음' and not review['critical'] and not review['warning']
    installed={}
    for path in sorted((PHASE/'staging').rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(PHASE/'staging')
        assert path.suffix in ('.md','.py')
        destination=ROOT/relative
        assert not destination.exists() or str(relative) in before
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination)
        installed[str(relative)]=sha(destination)
    (PHASE/'installed_manifest.json').write_text(json.dumps(installed,indent=2)+'\n')
    sources={str(path.relative_to(ROOT)):sha(path) for path in sorted((ROOT/'guitar_learning').rglob('*.py'))
             if 'archive' not in path.relative_to(ROOT/'guitar_learning').parts}
    (PHASE/'source_manifest.json').write_text(json.dumps(dict(python_count=len(sources),source=sources),indent=2)+'\n')
    (PHASE/'baseline_preservation.json').write_text(json.dumps(dict(verified=True,
        archived_files_verified=len(before),evaluations=summaries,
        scope='Both evaluations closed and all pins matched before installing the new source; historical source is preserved in archive'),indent=2)+'\n')
    print(json.dumps(dict(installed=len(installed),active_python=len(sources),baselines=summaries),indent=2))


if __name__ == '__main__':main()
