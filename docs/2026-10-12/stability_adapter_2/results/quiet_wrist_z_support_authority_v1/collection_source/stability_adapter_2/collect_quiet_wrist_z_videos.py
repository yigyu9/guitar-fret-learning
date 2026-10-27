"""Preserve 162 collected videos and append the four completed wrist videos."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/2026-10-12/stability_adapter_2'
PHASE=DATA/'results/quiet_wrist_z_support_authority_v1'
VIDEO_DIR=DATA/'videos'
OLD_INDEX=DATA/'VIDEO_INDEX_v15.md'
NEW_INDEX=DATA/'VIDEO_INDEX_v16.md'
UPDATE=DATA/'video_collection_update_v15.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    assert not NEW_INDEX.exists() and not UPDATE.exists()
    old={str(p):sha(p) for p in sorted(VIDEO_DIR.glob('*.mp4'))}
    assert len(old)==162
    old_index_sha=sha(OLD_INDEX)
    analysis=read(PHASE/'analysis.json')
    assert analysis['checks'] and all(analysis['checks'].values())
    pending=[]
    for condition in ['plus','minus']:
        videos=read(PHASE/'native'/condition/'videos.json')
        assert set(videos)=={'whole_body','hands'}
        for view,item in videos.items():
            source=Path(item['path'])
            destination=VIDEO_DIR/('quiet_wrist_z_support_authority_v1__native__'+condition+'__'+view+'.mp4')
            assert not destination.exists() and sha(source)==item['sha256']
            assert item['ffmpeg_exit_code']==item['ffprobe_exit_code']==0
            assert item['stream']['nb_read_frames']=='151' and item['stream']['avg_frame_rate']=='30/1'
            duration=float(item['stream']['duration']);assert abs(duration-151/30)<1e-6
            pending.append((condition,view,source,destination,item['sha256'],duration))
    copies=[]
    for condition,view,source,destination,digest,duration in pending:
        shutil.copy2(source,destination);assert sha(destination)==digest
        copies.append(dict(trial=condition,view=view,partial=False,source=str(source),copy=str(destination),
            sha256=digest,copy_sha256=sha(destination),size=destination.stat().st_size,duration_s=duration))
    assert all(sha(p)==digest for p,digest in old.items()) and sha(OLD_INDEX)==old_index_sha
    assert len(list(VIDEO_DIR.glob('*.mp4')))==166
    lines=['# 영상 모음 v16 — 166개','','Quiet L_Wrist_z 목표 ±0.005 rad 비교의 실제 Isaac Gym 0~5초 영상 4개다. 기존 162개는 그대로 보존하고 재인코딩 없이 복사했다. 각 영상은 151 frame/30 fps, 재생 5.033333초이며 마지막 시뮬레이션 시각은 5초다. 스트랩 경로 표시를 포함한다.','']
    for condition in ['plus','minus']:
        lines.extend(['## quiet_wrist_z_support_authority_v1 — '+condition,'','| 카메라 | 영상 | 재생시간(초) |','|---|---|---:|'])
        for item in copies:
            if item['trial']==condition:
                lines.append('| '+item['view']+' | ['+Path(item['copy']).name+']('+item['copy']+') | '+format(item['duration_s'],'.6f')+' |')
        lines.append('')
        lines.extend('!['+item['view']+']('+item['copy']+')' for item in copies if item['trial']==condition)
        lines.append('')
    NEW_INDEX.write_text('\n'.join(lines)+'\n'+OLD_INDEX.read_text())
    UPDATE.write_text(json.dumps(dict(previous_index_sha256=old_index_sha,new_index_sha256=sha(NEW_INDEX),
        previous_video_sha256=old,copies=copies,total_count=166,producer_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(str(NEW_INDEX))


if __name__=='__main__':main()
