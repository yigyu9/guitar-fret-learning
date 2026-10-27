"""Preserve the video collection and add two completed middle3-trial copies."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/initial_middle3_alignment_v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    old, new = D / 'VIDEO_INDEX_v9.md', D / 'VIDEO_INDEX_v10.md'
    update = D / 'video_collection_update_v9.json'
    assert not new.exists() and not update.exists()
    before = {str(p):sha(p) for p in (D / 'videos').glob('*.mp4')}
    assert len(before) == 138
    old_sha = sha(old)
    report = json.loads((P / 'native/report.json').read_text())
    assert report['completed'] and report['physics_steps'] == 1200 and len(report['videos']) == 2
    assert set(report['videos']) == {'whole_body', 'hands'}
    pending = []
    for view, video in report['videos'].items():
        source = Path(video['path'])
        dest = D / 'videos' / ('initial_middle3_alignment_v1__native__' + view + '.mp4')
        assert not dest.exists() and sha(source) == video['sha256']
        pending.append((source, dest, video['sha256']))
    copies = []
    for source, dest, expected in pending:
        shutil.copy2(source, dest)
        assert sha(dest) == expected
        copies.append(dict(source=str(source), copy=str(dest), sha256=sha(dest), size=dest.stat().st_size))
    assert all(sha(p) == h for p,h in before.items()) and sha(old) == old_sha
    assert len(list((D / 'videos').glob('*.mp4'))) == 140
    text = '# 영상 모음 갱신 v10 — 140개\n\n중지3 초기각을52.09°로맞추되최종81목표를유지한 실제 Isaac Gym0~5초 두 스트랩 영상이다. 다른80초기각/기타p·q/LA는 기존과같고 원본/이전목록을보존한다.\n\n'
    text += '\n\n'.join('![' + Path(v['copy']).name + '](' + v['copy'] + ')' for v in copies) + '\n\n'
    new.write_text(text + old.read_text())
    update.write_text(json.dumps(dict(previous_index_sha256=old_sha, new_index_sha256=sha(new), previous_video_sha256=before, copies=copies, total_count=140, producer_sha256=sha(Path(__file__))), indent=2) + '\n')
    print(str(new))


if __name__ == '__main__':
    main()
