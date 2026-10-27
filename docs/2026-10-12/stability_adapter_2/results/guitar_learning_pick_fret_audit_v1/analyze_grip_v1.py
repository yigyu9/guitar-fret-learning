"""Read saved RH motion only; distinguish fixed targets from measured states."""
import gzip
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from guitar_learning.control import RIGHT_GRIP_NAMES
from guitar_learning.render_pick_grip_v1 import INITIAL, RUN, FONT, ROOT
from stability_adapter_2.initial_pose_video60_v1.replay_v6 import sha, save

OUT = Path(__file__).resolve().parent
inputs = [Path(__file__).resolve(), INITIAL, RUN/'transitions.json.gz', RUN/'reset_00.json',
    ROOT/'guitar_learning/control.py', ROOT/'tab2body/assets/smpl_mpl_hands_body.xml', FONT]
pins = {str(p): sha(p) for p in inputs}
initial = json.loads(INITIAL.read_text())
reset = json.loads((RUN/'reset_00.json').read_text())
with gzip.open(RUN/'transitions.json.gz', 'rt') as stream:
    rows = json.load(stream)
states = [s['native'] for r in rows if r['episode'] == 0 for s in r['native_physics_samples240']]
assert [s['physics_step'] for s in states] == list(range(1, 1681))
indices = [initial['joint_names'].index(n) for n in RIGHT_GRIP_NAMES]
q = np.array([[s['human_dof_states'][i]['pos'] for i in indices] for s in states])
q0 = np.array([reset['prepared_reset']['actual_initial_state']['human_dof_states'][i]['pos'] for i in indices])
ref = np.array([reset['prepared_target105_rad'][i] for i in indices])
contract = reset['target_contract']
assert not set(RIGHT_GRIP_NAMES) & set(contract['action_order'])
assert set(RIGHT_GRIP_NAMES) <= set(contract['held_names'])
for name, v in zip(RIGHT_GRIP_NAMES, ref):
    assert v == contract['q_ref_rad'][contract['native_order'].index(name)]

def point(state, name):
    pose = state['human_body_states'][initial['human_body_names'].index(name)]['pose']
    p = np.array([pose['p'][a] for a in 'xyz'])
    x,y,z,w = np.array([pose['r'][a] for a in 'xyzw'])
    scale = np.linalg.norm([x,y,z,w]); x,y,z,w = np.array([x,y,z,w])/scale
    R = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    return p, R
relative = []
for s in states:
    p, R = point(s, 'RH:index2')
    relative.append(R.T @ (point(s, 'RH:pick')[0]-p))
relative = np.array(relative)
per_joint = [dict(name=n, reset_reference_rad=float(ref[i]),
    measured_min_rad=float(q[:,i].min()), measured_max_rad=float(q[:,i].max()),
    max_change_from_initial_rad=float(np.abs(q[:,i]-q0[i]).max()),
    max_reference_error_rad=float(np.abs(q[:,i]-ref[i]).max())) for i,n in enumerate(RIGHT_GRIP_NAMES)]
# A clearer two-view presentation of the inspected, unchanged source renders.
media = OUT/'media_views_v1'
for p in (media/'view_1.png', media/'view_3.png'):
    pins[str(p)] = sha(p)
image = Image.new('RGB', (1280, 590), (24,30,38))
image.paste(Image.open(media/'view_1.png'), (0,110))
image.paste(Image.open(media/'view_3.png'), (640,110))
draw = ImageDraw.Draw(image); font = ImageFont.truetype(str(FONT),24)
for y,line in ((8,'최신 평가 4.200초 · 엄지(주황)와 검지(파랑)의 실제 저장 자세'),
    (42,'노랑: 피크 기준점 표시(2.5mm). 실제 피크 물체/형상이 아닙니다.'),
    (76,'손을 보기 위해 몸통·기타를 숨긴 원본 mesh 재구성 · 물리 재실행 없음')):
    draw.text((18,y),line,font=font,fill='white')
image.save(OUT/'right_hand_detail.png')
assert all(sha(p)==h for p,h in pins.items())
save(OUT/'grip_audit_v1.json', dict(completed=True, inputs=pins, inputs_unchanged=True,
    source_episode=0, physics_samples=1680, physical_time_s=7., new_physics_steps=0,
    policy_controlled_RH_fingers=False, held_target_count=21,
    max_actual_joint_change_from_initial_rad=float(np.abs(q-q0).max()),
    max_actual_joint_change_from_initial_degrees=float(np.rad2deg(np.abs(q-q0).max())),
    max_actual_joint_reference_error_rad=float(np.abs(q-ref).max()),
    pick_parent='RH:index2', pick_source_local_position_m=[.007,-.048,-.005],
    max_pick_relative_position_error_from_xml_m=float(np.linalg.norm(relative-np.array([.007,-.048,-.005]),axis=1).max()),
    per_joint=per_joint,
    scope='finite held finger targets, not trained grasp; empty fixed child pick marker, no pinch pressure/slip validation',
    detail_image=dict(path=str(OUT/'right_hand_detail.png'),sha256=sha(OUT/'right_hand_detail.png'))))
print(json.dumps(dict(max_actual_joint_change_degrees=float(np.rad2deg(np.abs(q-q0).max())),
    max_actual_joint_reference_error_rad=float(np.abs(q-ref).max()),
    max_pick_relative_error_m=float(np.linalg.norm(relative-np.array([.007,-.048,-.005]),axis=1).max())),indent=2))
