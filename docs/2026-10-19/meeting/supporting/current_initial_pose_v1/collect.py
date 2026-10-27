"""Collect current baseline native media and separately labelled diagnostic images."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
BASE = ROOT/'paper/initial_pose/current_v3'
DIAG = ROOT/'docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1'
rows = []
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source, dest, scope):
    before = sha(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert sha(dest) == before
    else:
        shutil.copy2(source, dest)
    assert before == sha(source) == sha(dest)
    row = {'source': str(source), 'copy': str(dest), 'sha256': before, 'scope': scope}
    if dest.suffix == '.png':
        with Image.open(dest) as image:
            row['dimensions'] = list(image.size)
            image.verify()
    if dest.suffix == '.mp4':
        metadata = subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height,r_frame_rate,nb_frames:format=duration',
            '-of','json',str(dest)],check=True,capture_output=True,text=True)
        row['video'] = json.loads(metadata.stdout)
        subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(dest),
                        '-f','null','-'],check=True,capture_output=True)
        row['full_decode_passed'] = True
    rows.append(row)

for path in sorted((BASE/'images').glob('*.png')):
    copy(path, MEETING/'result/images/current_initial_pose_v3'/path.name,
         'current_v3: Root fixed, lower body finite control; 035/native v14')
for name in ['baseline','repeat','release','free_strike','regrasp']:
    copy(BASE/'videos'/(name+'_whole_body.mp4'),
         MEETING/'result/videos/current_initial_pose_v3'/(name+'_whole_body.mp4'),
         'current_v3: original Isaac Gym camera, 5fps; separate native trials')
for path in sorted((DIAG/'native_v1/media').glob('initial*.png')):
    copy(path, MEETING/'result/images/diagnostic_initial_pose_20261019'/path.name,
         'Separate diagnostic: Root and lower body fixed, right strike OFF')
for name in ['README.md','MEDIA.md','VALUES.md']:
    copy(BASE/name,HERE/'source_records/current_v3'/name,'baseline source explanation')
copy(BASE/'configs/baseline_v1.json',HERE/'source_records/current_v3/baseline_v1.json','baseline config')
copy(DIAG/'README.md',HERE/'source_records/diagnostic_20261019/README.md','diagnostic source explanation')
with (HERE/'manifest.json').open('x') as output:
    json.dump({'scope':'Existing native PNG/MP4 copies; no new render, simulation, or video edit',
               'image_count':sum(Path(r['copy']).suffix=='.png' for r in rows),
               'video_count':sum(Path(r['copy']).suffix=='.mp4' for r in rows),
               'all_source_copy_hashes_equal':True,'files':rows},output,ensure_ascii=False,indent=2)
    output.write('\n')
print('Verified 9 PNGs, 5 native videos (full decode), 5 source records; all original/copy hashes equal.')
