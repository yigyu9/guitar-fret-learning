"""Add original no-strap videos while preserving the existing collection."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/no_strap_current_pose_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    old, new = D / 'VIDEO_INDEX_v10.md', D / 'VIDEO_INDEX_v11.md'
    update = D / 'video_collection_update_v10.json'
    assert not new.exists() and not update.exists()
    before = {str(p):sha(p) for p in (D / 'videos').glob('*.mp4')}
    assert len(before) == 140
    old_sha = sha(old)
    analysis = json.loads((P / 'analysis.json').read_text())
    assert all(analysis['checks'].values())
    videos = json.loads((P / 'native/videos.json').read_text())
    pending = []
    for view, video in videos.items():
        source = Path(video['path'])
        dest = D / 'videos' / ('no_strap_current_pose_v1__native__' + view + '.mp4')
        assert not dest.exists() and sha(source) == video['sha256']
        pending.append((source, dest, video['sha256']))
    copies = []
    for source, dest, expected in pending:
        shutil.copy2(source, dest)
        assert sha(dest) == expected
        copies.append(dict(source=str(source), copy=str(dest), sha256=expected, size=dest.stat().st_size))
    assert all(sha(p) == h for p,h in before.items()) and sha(old) == old_sha
    assert len(list((D / 'videos').glob('*.mp4'))) == 142
    text = '# 영상 모음 갱신 v11 — 142개\n\n현재 초기 자세와 제어 목표를 유지하고 스트랩 힘을 끈 실제 Isaac Gym 0~5초 영상 두 개입니다. 스트랩 표시도 없으며 재인코딩 없이 원본을 복사했습니다.\n\n'
    text += '\n\n'.join('![' + Path(v['copy']).name + '](' + v['copy'] + ')' for v in copies) + '\n\n'
    new.write_text(text + old.read_text())
    update.write_text(json.dumps(dict(previous_index_sha256=old_sha, new_index_sha256=sha(new), previous_video_sha256=before, copies=copies, total_count=142, producer_sha256=sha(Path(__file__))), indent=2) + '\n')
    print(str(new))


if __name__ == '__main__': main()
