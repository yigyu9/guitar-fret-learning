"""Verify meeting copies and finished media; no simulation, training or source writes."""
import json
import re
import subprocess
import hashlib
from pathlib import Path
from PIL import Image


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def main():
    meeting=Path(__file__).resolve().parents[2]
    copies=json.loads((meeting/'supporting/provenance/copied_files_v1.json').read_text())['files']
    errors=[];videos=[];images=[];documents=[]
    for item in copies:
        for role in ('source_absolute','destination_absolute'):
            if sha(Path(item[role]))!=item['sha256']:errors.append(dict(file=item[role],error='digest changed'))
    for path in sorted((meeting/'result/videos').glob('*.mp4')):
        probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames','-of','json',str(path)],capture_output=True,text=True)
        if probe.returncode:errors.append(dict(file=str(path),error=probe.stderr))
        decode=subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(path),'-f','null','-'],capture_output=True,text=True)
        row=dict(path=str(path.relative_to(meeting)),probe=json.loads(probe.stdout) if probe.returncode==0 else None,
                 full_decode_passed=decode.returncode==0 and not decode.stderr.strip(),decode_stderr=decode.stderr)
        videos.append(row)
        if not row['full_decode_passed']:errors.append(dict(file=str(path),error='full decode failed',detail=decode.stderr))
    for path in sorted((meeting/'result/images').glob('*.png')):
        with Image.open(path) as im:
            size=im.size;im.verify()
        images.append(dict(path=str(path.relative_to(meeting)),size=list(size),read_passed=True))
    docs=[meeting/'README.md',meeting/'supporting/README.md']+sorted((meeting/'result').rglob('*.md'))
    for path in docs:
        text=path.read_text();missing=[]
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http:','https:','#')):continue
            dest=target.split('#')[0]
            if not (path.parent/dest).exists():missing.append(target)
        documents.append(dict(path=str(path.relative_to(meeting)),missing_local_links=missing))
        if missing:errors.append(dict(file=str(path),missing_links=missing))
    invalid=[str(p.relative_to(meeting)) for p in (meeting/'result').rglob('*') if p.is_file() and p.suffix not in ('.mp4','.png','.md')]
    if invalid:errors.append(dict(nonpresentation_files_in_result=invalid))
    result=dict(completed=not errors,copied_files=len(copies),source_and_copy_sha_unchanged=not any(e.get('error')=='digest changed' for e in errors),
        video_count=len(videos),image_count=len(images),videos=videos,images=images,documents=documents,errors=errors,
        scope='assembly and media integrity only; original experiment claims retain their recorded conditions')
    output=meeting/'supporting/qa/verification_v1.json'
    with output.open('x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ('completed','copied_files','video_count','image_count','errors')},ensure_ascii=False))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
