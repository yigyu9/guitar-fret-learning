"""Collect earlier right-tilted and rounded-spine postures from saved evidence."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
DEST = MEETING/'result/images/initial_pose_search'
OLD = ROOT/'paper/initial_pose/archive/experiment_records/lower_body_release_v1'
ROUNDED = ROOT/'docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1'
records = []
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source, destination):
    before = sha(source)
    if destination.exists():
        assert sha(destination) == before
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    assert sha(source) == sha(destination) == before
    records.append({'method': 'byte-identical copy', 'source': str(source),
                    'copy': str(destination), 'sha256': before})

copy(OLD/'upright_chest_support_v1/figures_static_v17/before_after_native_5s.png',
     DEST/'08b_right_tilt_vs_upright_at5s.png')
for case, name in [('rounded9_left_support', '09_rounded_spine_9deg_left_support_t0.png'),
                   ('rounded9_left_away', '09b_rounded_spine_9deg_left_away_t0.png'),
                   ('rounded12_left_away', '10_rounded_spine_12deg_left_away_t0.png')]:
    copy(ROUNDED/'native_v2'/case/'media/raw/frames/whole_body/00000.png', DEST/name)
for source, name in [(OLD/'upright_chest_support_v1/README.md','upright_result.md'),
                      (OLD/'upright_chest_support_v1/figures_static_v17/verification.json','upright_figure_verification.json'),
                      (ROUNDED/'README_V2.md','rounded_result_V2.md'),
                      (ROUNDED/'artifacts_v1/README.md','rounded_media.md')]:
    copy(source, HERE/'source_records'/name)
video = OLD/'native/rotational_stable_pd_interior_static_v1/media/whole_body.mp4'
output = DEST/'08_right_tilt_original_t0.png'
video_before = sha(video)
command = ['ffmpeg', '-v', 'error', '-nostdin', '-i', str(video),
           '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', 'pipe:1']
encoded = subprocess.run(command, check=True, capture_output=True).stdout
if not output.exists():
    output.write_bytes(encoded)
with Image.open(io.BytesIO(encoded)) as decoded, Image.open(output) as existing:
    assert decoded.convert('RGB').tobytes() == existing.convert('RGB').tobytes()
assert sha(video) == video_before
records.append({'method': 'first frame decoded from existing native video; no rerender/crop/overlay',
                'source': str(video), 'source_sha256': video_before,
                'frame_index': 0, 'time_s': 0, 'copy': str(output), 'sha256': sha(output)})
for row in records:
    path = Path(row['copy'])
    if path.suffix == '.png':
        with Image.open(path) as image:
            row['dimensions'] = list(image.size)
            image.verify()
with (HERE/'manifest.json').open('x') as f:
    json.dump({'image_count': 5, 'original_files_unchanged': True,
               'first_frame_pixel_check_passed': True, 'png_open_checks_passed': True,
               'scope': 'Four existing PNG copies plus one saved-video first frame; no simulator run',
               'files': records}, f, ensure_ascii=False, indent=2)
    f.write('\n')
print('Verified four PNG copies, one pixel-matched saved-video frame, four evidence copies; original files unchanged.')
