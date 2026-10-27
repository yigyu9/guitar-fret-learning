"""Preserve the video collection and add two completed middle3-trial copies."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/fixed_strap_middle_relax_v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    old, new = D / 'VIDEO_INDEX_v7.md', D / 'VIDEO_INDEX_v8.md'
    update = D / 'video_collection_update_v7.json'
    assert not new.exists() and not update.exists()
    before = {str(p):sha(p) for p in (D / 'videos').glob('*.mp4')}
    assert len(before) == 134
    old_sha = sha(old)
    report = json.loads((P / 'native/report.json').read_text())
    assert report['completed'] and report['physics_steps'] == 1200 and len(report['videos']) == 2
    copies = []
    for view, video in report['videos'].items():
        source = Path(video['path'])
        dest = D / 'videos' / ('fixed_strap_middle_relax_v1__native__' + view + '.mp4')
        assert not dest.exists() and sha(source) == video['sha256']
        shutil.copy2(source, dest)
        assert sha(dest) == video['sha256']
        copies.append(dict(source=str(source), copy=str(dest), sha256=sha(dest), size=dest.stat().st_size))
    assert all(sha(p) == h for p,h in before.items()) and sha(old) == old_sha
    assert len(list((D / 'videos').glob('*.mp4'))) == 136
    text = '# 영상 모음 갱신 v8 — 136개\n\n중지3 유지목표만−0.05rad 완화한 실제 Isaac Gym0~5초 두 스트랩 영상이다. 초기각/기타p·q/LA는 기존과같고 원본/이전목록을보존한다.\n\n'
    text += '\n\n'.join('![' + Path(v['copy']).name + '](' + v['copy'] + ')' for v in copies) + '\n\n'
    new.write_text(text + old.read_text())
    update.write_text(json.dumps(dict(previous_index_sha256=old_sha, new_index_sha256=sha(new), previous_video_sha256=before, copies=copies, total_count=136, producer_sha256=sha(Path(__file__))), indent=2) + '\n')
    print(str(new))


if __name__ == '__main__':
    main()
