"""Copy existing contact-annotated PNGs and their explanations only."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
SOURCE = ROOT/'docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1'
DEST = MEETING/'result/images/contact_visualization'
DEST.mkdir(exist_ok=True)
SCENES = [('00015', '01_preparation_0p5s.png'),
          ('00105', '02_left_grip_A_3p5s.png'),
          ('00160', '03_release_transition_5p333s.png'),
          ('00195', '04_left_released_A_6p5s.png'),
          ('00315', '05_left_grip_B_10p5s.png'),
          ('00420', '06_left_released_B_14s.png')]
records = []
def copy(source, destination):
    data = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == data
    else:
        shutil.copy2(source, destination)
    assert source.read_bytes() == destination.read_bytes()
    row = {'source': str(source), 'copy': str(destination),
           'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    if destination.suffix == '.png':
        with Image.open(destination) as im:
            row['dimensions'] = list(im.size)
            im.verify()
    records.append(row)

for number, name in SCENES:
    copy(SOURCE/'artifacts_v1'/('three_views_'+number+'.png'), DEST/name)
for relative in ['README.md', 'artifacts_v1/README_v2.md', 'contact_summary_v1.json']:
    copy(SOURCE/relative, HERE/'source_records'/relative)
with (HERE/'manifest.json').open('x') as f:
    json.dump({'scope': 'Existing file copies; no new rendering/simulation/image editing',
               'image_count': len(SCENES), 'all_source_copy_bytes_equal': True,
               'image_open_checks_passed': True, 'files': records}, f, ensure_ascii=False, indent=2)
    f.write('\n')
print('Verified: 6 contact images and 3 source records copied byte-identically; all PNGs open.')
