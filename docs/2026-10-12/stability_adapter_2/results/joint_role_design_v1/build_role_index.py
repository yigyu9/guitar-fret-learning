"""Create a documentation index from original XML joint names, not runtime config."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
source = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = {str(p): sha(p) for p in (source, Path(__file__).resolve(),
    ROOT/'stability_adapter_2/music_pipeline_v2/control.py', ROOT/'stability_adapter_2/music_pipeline_v3/control.py')}
with (PHASE/'role_index_inputs_before.json').open('x') as stream:
    json.dump(inputs, stream, indent=2)
roles = {
    'Torso': '상체 기준 자세 유지', 'Spine': '몸통과 기타의 상대 배치 유지',
    'Chest': '가슴을 통한 기타 지지에 기여', 'Neck': '목의 기준 자세 유지', 'Head': '머리 기준 자세 유지',
    'R_Thorax': '오른팔 지지 위치 유지', 'R_Shoulder': '상완 지지와 타현 작업 공간 유지',
    'R_Elbow': '피크의 큰 이동과 줄 접근', 'R_Wrist': '피크의 세밀한 배치와 타현 교차 조절',
    'L_Thorax': '왼팔의 전체 작업 위치 설정', 'L_Shoulder': '목표 프렛 부근으로 팔 이동',
    'L_Elbow': '손과 넥 사이 거리 및 접근 자세 조절', 'L_Wrist': '압현 방향과 손바닥 배치 조절',
    'left_thumb': '압현에 적합한 엄지 배치와 필요시 반력 보조',
    'left_finger': '할당된 줄과 프렛의 압현 유지 해제 및 다음 운지 준비',
    'right_grip': '초기 피크 그립과 손모양 목표 유지',
    'Hip': '허벅지 지지 배치 유지 및 제한된 조정', 'Knee': '하체 자세와 다리 및 발 배치 보완',
    'Ankle': '발 자세와 의도한 지면 접촉 안정화', 'Toe': '발 앞부분 자세와 접촉 조건 유지',
}
xml = ET.parse(source).getroot()
assert xml.find('compiler').get('angle') == 'degree'
rows = []
for index, joint in enumerate(xml.findall('.//worldbody//joint')):
    name = joint.get('name')
    limits = list(map(float, joint.get('range').split()))
    zero = limits[0] == limits[1]
    lower = name.startswith(tuple(side+'_'+part+'_' for side in ('L','R') for part in ('Hip','Knee','Ankle','Toe')))
    if name.startswith('LH:'):
        role = 'left_thumb' if name.startswith('LH:thumb') else 'left_finger'
        active = True
    elif name.startswith('RH:'):
        role, active = 'right_grip', False
    elif lower:
        role, active = name.split('_')[1], False
    else:
        role = name.rsplit('_', 1)[0]
        active = role in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Elbow','R_Wrist')
    assert role in roles and (not active or not zero)
    proposed = active or (lower and not zero)
    rows.append(dict(name=name, source_xml_order=index, role=role,
        source_range_degrees=limits, zero_range=zero, lower_body=lower,
        current_cpu_target_owner='policy' if active else 'reference',
        proposed_55_target_owner='policy' if proposed else 'reference',
        axis_specific_function='not assigned; verify model coordinates before interpretation'))
assert len(rows) == len({row['name'] for row in rows}) == 105
counts = dict(total=105, current_policy=sum(row['current_cpu_target_owner']=='policy' for row in rows),
    proposed_policy=sum(row['proposed_55_target_owner']=='policy' for row in rows),
    lower_channels=sum(row['lower_body'] for row in rows), zero_range=sum(row['zero_range'] for row in rows),
    lower_nonzero=sum(row['lower_body'] and not row['zero_range'] for row in rows))
assert counts == dict(total=105,current_policy=39,proposed_policy=55,lower_channels=24,zero_range=8,lower_nonzero=16)
after = {p: sha(Path(p)) for p in inputs}
assert inputs == after
document = dict(schema='joint_role_design_index.v1', scope='documentation only; not runtime configuration',
    proposed_status='55-output design not implemented or trained',
    source_order_scope='XML order, not an assumed native importer/action order',
    root_included=False, role_definitions=roles, counts=counts, joints=rows, source_inputs_sha256=inputs)
with (PHASE/'joint_role_map.json').open('x') as stream:
    json.dump(document, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(counts))
