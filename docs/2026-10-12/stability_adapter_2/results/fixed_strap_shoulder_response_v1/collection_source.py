"""Collect four completed shoulder-probe videos without changing earlier files."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'docs/2026-10-12/stability_adapter_2';P=D/'results/fixed_strap_shoulder_response_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=D/'VIDEO_INDEX_v6.md';new=D/'VIDEO_INDEX_v7.md';update=D/'video_collection_update_v6.json'
    assert not new.exists() and not update.exists() and len(list((D/'videos').glob('*.mp4')))==130
    before=sha(old);rows=[];pending=[]
    for label in ['minus008','plus008']:
        report=json.loads((P/label/'report.json').read_text());assert report['completed'] and report['physics_steps']==1200 and set(report['videos'])=={'hands','whole_body'}
        for view,video in report['videos'].items():
            source=Path(video['path']);dest=D/'videos'/('fixed_strap_shoulder_response_v1__'+label+'__'+view+'.mp4')
            assert not dest.exists() and sha(source)==video['sha256']
            pending.append((source,dest,video['sha256']))
    for source,dest,expected in pending:
        shutil.copy2(source,dest);assert sha(dest)==expected
        rows.append(dict(source=str(source),copy=str(dest),sha256=expected,size=dest.stat().st_size))
    head='# 영상 모음 갱신 v7 — 134개\n\n동일 초기 자세·고정 LA에서 왼쪽 어깨 유지 목표만 ±0.008rad 바꾼 두 조건의 실제 Isaac Gym 0~5초 영상이다. 실제 스트랩 경로를 표시한다.\n\n'
    head+='\n'.join('- ['+Path(v['copy']).name+']('+v['copy']+')' for v in rows)+'\n\n'
    new.write_text(head+old.read_text());assert sha(old)==before and len(list((D/'videos').glob('*.mp4')))==134
    update.write_text(json.dumps(dict(previous_index_sha256=before,new_index_sha256=sha(new),copies=rows,total_count=134,producer_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(str(new))
if __name__=='__main__':main()
