"""Copy the two completed videos; append a new index without editing old ones."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/2026-10-12/stability_adapter_2'
P=D/'results/coupled_palm_witness_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=D/'VIDEO_INDEX_v4.md';new=D/'VIDEO_INDEX_v5.md'
    before=sha(old);report=json.loads((P/'native/report.json').read_text())
    assert report['completed'] and report['physics_steps']==1200 and not new.exists()
    assert len(list((D/'videos').glob('*.mp4')))==126
    rows=[]
    for view,video in report['videos'].items():
        source=Path(video['path']);dest=D/'videos'/('coupled_palm_witness_v1__native__'+view+'.mp4')
        assert not dest.exists() and sha(source)==video['sha256']
        shutil.copy2(source,dest);assert sha(dest)==video['sha256']
        rows.append(dict(source=str(source),copy=str(dest),sha256=sha(dest),size=dest.stat().st_size))
    head='# 영상 모음 갱신 v5 — 128개\n\n손바닥 접근 초기18각과 유지 목표를 바꾼 실제 Isaac Gym 0~5초·스트랩 표시 두 영상이다. 원본/이전 목록은 보존한다.\n\n'
    head+='\n'.join('- ['+Path(v['copy']).name+']('+v['copy']+')' for v in rows)+'\n\n'
    new.write_text(head+old.read_text())
    assert sha(old)==before and len(list((D/'videos').glob('*.mp4')))==128
    update=D/'video_collection_update_v4.json';assert not update.exists()
    update.write_text(json.dumps(dict(previous_index_sha256=before,new_index_sha256=sha(new),copies=rows,total_count=128,producer_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(str(new))
if __name__=='__main__':main()
