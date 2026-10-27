"""Copy this correction's completed videos, preserving all original paths/bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT/'docs/2026-10-12/stability_adapter_2/results'
DEST = ROOT/'docs/2026-10-12/video/archive_v2'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


DEST.mkdir(exist_ok=False)
records = []
for name in ('stability_update_correction_v1', 'stability_support_nominal_v1'):
    for report_path in sorted((RESULTS/name).rglob('native/episode_*/report.json')):
        report = json.loads(report_path.read_text())
        for video in report.get('videos', {}).values():
            source = Path(video['path']); expected = sha(source)
            if expected != video['sha256']: raise ValueError('recorded video changed: '+str(source))
            target = DEST/source.relative_to(ROOT/'docs/2026-10-12')
            if target.exists(): raise FileExistsError(target)
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
            probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
                '-show_entries','stream=codec_name,width,height,nb_frames:format=duration','-of','json',str(target)],text=True))
            if not probe['streams'] or sha(target)!=expected or sha(source)!=expected: raise ValueError('copy/probe failed')
            records.append({'source':str(source),'copy':str(target),'sha256':expected,'bytes':target.stat().st_size,
                'native_report':str(report_path),'native_report_sha256':sha(report_path),'probe':probe})
with (DEST/'manifest.json').open('x') as f: json.dump({'producer':str(Path(__file__).resolve()),
    'producer_sha256':sha(__file__),'count':len(records),'records':records},f,indent=2,ensure_ascii=False)
lines=['# 수정 학습 영상 모음\n','원본을 유지한 채 바이트가 같은 복사본을 모았습니다. 영상마다 실제 종료 사유는 원본 보고서에 있습니다.\n']
for record in records:
    lines.append('- ['+str(Path(record['source']).relative_to(RESULTS))+']('+record['copy']+')\n')
with (DEST/'README.md').open('x') as f: f.writelines(lines)
print('archived',len(records),'completed videos; originals unchanged')
