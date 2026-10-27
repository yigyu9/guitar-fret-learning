"""Collect existing posture-search images without rendering or image editing."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
IMAGES = MEETING / 'result/images/initial_pose_search'
IMAGES.mkdir(exist_ok=True)
OLD = 'docs/2026-10-12/stability_adapter_2/results/'
NEW = 'docs/2026-10-19/stability_adapter_2/results/'
SELECTION = [
 (OLD+'rounded_spine_no_left_v1/artifacts_v1/native_whole_body_frames_v1.png', '01_distributed_spine_bend_3_9_12deg.png'),
 (OLD+'om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png', '02_forward_lean_18deg_side.png'),
 (OLD+'om_axilla_initial_pose_v1/artifacts_v2/initial_strings_conditions_v2.png', '02b_forward_lean_reference_and_18deg.png'),
 (NEW+'left_lean_axilla_v1/native_v1/left4deg/media/initial_native.png', '03_neck_side_lean_4deg_initial.png'),
 (NEW+'left_lean_axilla_v1/artifacts_v1/initial_pose_four_conditions_v2.png', '03b_neck_side_lean_four_conditions.png'),
 (NEW+'body_side_lean_axilla_v1/native_v1/right4_close_support/media/initial_native.png', '04_body_side_lean_4deg_initial.png'),
 (NEW+'body_side_lean_axilla_v1/artifacts_v1/initial_native_pair.png', '04b_body_side_lean_two_controls.png'),
 (NEW+'neckward_torso_turn_v1/artifacts_v1/native_wholebody_samecrop_old_new.png', '05_reduce_bend_and_neckward_turn.png'),
 (NEW+'upright_neckward_pose_v1/artifacts_v1/native12_vs_native19_initial_and_5s.png', '06_less_bend_neckward12_vs19.png'),
 (NEW+'waist_straighten_v1/artifacts_v1/initial_whole_comparison_v1.png', '07_waist_straighten_initial_comparison.png'),
]
records = []
def copy(source, dest):
    source = ROOT / source
    data = source.read_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert dest.read_bytes() == data, 'Use a new version for changed source: '+str(dest)
    else:
        shutil.copy2(source, dest)
    assert dest.read_bytes() == source.read_bytes()
    row = {'source': str(source), 'copy': str(dest),
           'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    if dest.suffix == '.png':
        with Image.open(dest) as image:
            row['dimensions'] = list(image.size)
            image.verify()
    records.append(row)

for source, name in SELECTION:
    copy(source, IMAGES/name)
for prefix, name in [(OLD, 'rounded_spine_no_left_v1'), (OLD, 'om_axilla_initial_pose_v1'),
                     (NEW, 'left_lean_axilla_v1'), (NEW, 'body_side_lean_axilla_v1'),
                     (NEW, 'neckward_torso_turn_v1'), (NEW, 'upright_neckward_pose_v1'),
                     (NEW, 'waist_straighten_v1')]:
    copy(prefix+name+'/README.md', HERE/'source_records'/name/'README.md')
for name in ['neckward_torso_turn_v1', 'upright_neckward_pose_v1']:
    copy(NEW+name+'/artifacts_v1/README_V2.md', HERE/'source_records'/name/'ARTIFACTS_README_V2.md')
report = {'scope': 'Existing image/document copies only; no rendering, simulation, extraction, or image editing',
          'image_count': len(SELECTION), 'source_record_count': len(records)-len(SELECTION),
          'all_source_copy_bytes_equal': True, 'image_open_checks_passed': True, 'files': records}
with (HERE/'manifest.json').open('x') as output:
    json.dump(report, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'}, ensure_ascii=False))
