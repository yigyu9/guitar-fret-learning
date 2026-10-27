"""Preserve the selected periodic checkpoint videos alongside earlier archives."""
import hashlib,json,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=Path('/home/ajou/yigyu/3');V=ROOT/'docs/2026-10-12/video';DEST=V/'archive_v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
analysis_path=P/'analysis_v1.json';analysis=json.loads(analysis_path.read_text())
inputs={str(Path(__file__).resolve()):sha(__file__),str(analysis_path):sha(analysis_path)}
DEST.mkdir(exist_ok=False);records=[]
for name,video in analysis['evaluations']['new_checkpoint']['videos'].items():
 source=Path(video['path']);inputs[str(source)]=sha(source)
 if inputs[str(source)]!=video['sha256']:raise ValueError('video source changed')
 target=DEST/(analysis['label']+'_'+name+'.mp4');shutil.copy2(source,target)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(target)],text=True))
 if sha(target)!=inputs[str(source)] or probe['streams'][0]!=video['stream']:raise ValueError('copy or container mismatch')
 records.append({'source':str(source),'copy':str(target),'sha256':inputs[str(source)],'probe':probe})
unchanged=all(sha(p)==h for p,h in inputs.items())
with (DEST/'manifest.json').open('x') as f:json.dump({'label':analysis['label'],'records':records,'input_sha256':inputs,'inputs_unchanged':unchanged},f,indent=2)
with (DEST/'README.md').open('x') as f:
 f.write('# 추가 학습 체크포인트 전체 영상\n\n원본을 유지한 바이트 동일 복사본입니다. 정상 horizon과 실제 종료 사유는 [분석 자료]('+str(analysis_path)+')에 기록했습니다.\n\n')
 for r in records:f.write('!['+Path(r['copy']).stem+']('+r['copy']+')\n\n')
with (V/'README_ABSOLUTE_V3.md').open('x') as f:f.write('# 전체 영상 모음\n\n- [이전 전체 영상]('+str(V/'archive_v1/index_absolute_v1.md')+')\n- [직전 수정·재시도 영상14개]('+str(V/'archive_v2/README.md')+')\n- [추가 학습의 새 체크포인트 전신·손 영상]('+str(DEST/'README.md')+')\n\n기존 영상과 원본은 보존했습니다. 이후 체크포인트는 실행 결과 폴더에 계속 생성됩니다.\n')
print('archived',len(records),'new videos; inputs unchanged',unchanged)
if not unchanged:raise SystemExit('archive inputs changed')
