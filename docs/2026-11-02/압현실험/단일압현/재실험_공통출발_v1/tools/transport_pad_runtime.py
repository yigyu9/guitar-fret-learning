"""D: 준비 운반 동안 실제 고정 패드 점 위치를 추종하고 손목 방향은 약하게 안내한다.

봉인된 C 실행기의 물리·제어 제한·초기 상태·성공 판정을 그대로 재사용한다.
이 도구는 probe만 실행한다. 정책 압현 단계에는 패드 피드백을 적용하지 않는다.
"""
if __name__=='__main__':
    import isaacgym  # native 라이브러리를 Torch보다 먼저 로드한다.
import argparse
import copy
import hashlib
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
BASE_PATH=HERE/'transport_runtime.py'
BASE_SHA256='7932983cbc5e6b8f20aea8c64c1c5d5d5699efd45f9cb81261291f56b4f9e932'
SCHEMA='guitar_learning.single18.common_transport_pad.v1'
OLD_ORIENTATION_SCALE=.1
ORIENTATION_SCALE=.01


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_base():
    if digest(BASE_PATH)!=BASE_SHA256:
        raise ValueError('봉인된 운반 C 실행기 SHA 불일치')
    spec=importlib.util.spec_from_file_location('single18_transport_pad_base',BASE_PATH)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


base=load_base()
import torch


def skew(value):
    x,y,z=value.unbind(-1);zero=torch.zeros_like(x)
    return torch.stack((zero,-z,y,z,zero,-x,-y,x,zero),-1).reshape(*value.shape[:-1],3,3)


def replace_point_feedback(wrist_error,wrist_jacobian,offset_world,point_error,reset_mask):
    """실제 손목 원점의 q-position Jacobian을 실제 패드 점으로 평행 이동한다."""
    if (wrist_error.ndim!=2 or wrist_error.shape[1]!=6 or wrist_jacobian.shape!=(len(wrist_error),6,12)
            or offset_world.shape!=point_error.shape or point_error.shape!=(len(wrist_error),3)
            or reset_mask.shape!=(len(wrist_error),)):
        raise ValueError('정렬된 arm12 Jacobian·패드 위치 오차·reset 행 필요')
    angular=wrist_jacobian[:,3:]/OLD_ORIENTATION_SCALE
    linear=wrist_jacobian[:,:3]-skew(offset_world)@angular
    ratio=ORIENTATION_SCALE/OLD_ORIENTATION_SCALE
    jacobian=torch.cat((linear,ratio*wrist_jacobian[:,3:]),1)
    error=torch.cat((point_error,ratio*wrist_error[:,3:]),1)
    error=torch.where(reset_mask[:,None],torch.zeros_like(error),error)
    jacobian=torch.where(reset_mask[:,None,None],torch.zeros_like(jacobian),jacobian)
    return error,jacobian


def point_specification(catalog,row):
    """압축 valid 표본 번호를 원본 패드 번호로 매핑하고 최종 FK 위치를 대조한다."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    pad=load_fingertip_pad();finger=int(row['finger_id'])-1
    if not 0<=finger<4:raise ValueError('담당 손가락1..4 필요')
    compact=row['geometry'].get('selected_sample')
    ids=np.flatnonzero(pad['valid'][finger])
    if type(compact) is not int or not 0<=compact<len(ids):
        raise ValueError('valid 표본으로 압축된 selected_sample 번호 필요')
    full=int(ids[compact]);local=np.asarray(pad['points_local'][finger,full],dtype=float)
    body=pad['contract']['body_names'][finger]
    contract=load_gpu_prepared_reset_contract('left')
    names=contract['initial']['human_body_names']
    body_index=names.index(body)
    state=row['final_hover_state']
    finger_pose=state['human_body_states'][body_index]['pose']
    guitar_pose=state['guitar_body_states'][0]['pose']
    def pose(value):
        return np.array([value['p'][a] for a in 'xyz']),Rotation.from_quat([value['r'][a] for a in 'xyzw'])
    fp,fr=pose(finger_pose);gp,gr=pose(guitar_pose)
    expected=gr.inv().apply(fp+fr.apply(local)-gp)
    recorded=np.asarray(row['geometry'].get('selected_point_G_m'),dtype=float)
    if recorded.shape!=(3,) or not np.isfinite(recorded).all() or np.linalg.norm(expected-recorded)>1e-6:
        raise ValueError('선택 패드와 최종 FK/기타 프레임 위치 불일치')
    final=row['transport_waypoints'][-1]
    wrist_p=np.asarray(final['wrist_position_G_m'],dtype=float)
    wrist_r=Rotation.from_quat(final['wrist_quaternion_G_xyzw'])
    offset=wrist_r.inv().apply(recorded-wrist_p)
    source=dict(pad['contract']['source_sha256'])
    # 현재 패드 선택 구현도 정적 원본 봉인에 포함한다.
    import inspect
    path=Path(inspect.getsourcefile(load_fingertip_pad)).resolve();source[str(path)]=digest(path)
    return dict(schema=SCHEMA+'.point',finger_id=finger+1,body_name=body,native_body_index=body_index,
        selected_compact_valid_index=compact,selected_full_sample_index=full,
        valid_sample_count=int(len(ids)),point_body_local_m=local.tolist(),
        final_point_G_m=recorded.tolist(),point_wrist_local_m=offset.tolist(),source_sha256=source)


def feedback_contract(point):
    return dict(schema=SCHEMA+'.feedback',kind='actual_fixed_distal_pad_position_soft_wrist_orientation',
        condition='D',point=point,position_frame='native world error; target follows actual guitar frame',
        jacobian='Jpad=Jwrist_linear-skew(actual_pad_world-actual_wrist_world)Jwrist_angular; arm12 q-position coordinates',
        orientation_scale_m_per_rad=ORIENTATION_SCALE,previous_orientation_scale_m_per_rad=OLD_ORIENTATION_SCALE,
        target='moving commanded wrist G pose applies fixed final wrist-local pad offset',
        active_phase='transport and final hover settling only',policy_press_feedback=False,
        limits='original bounded_wrist_target, action bounds, PD/force/rate and all safety/acceptance criteria unchanged',
        base_runtime_sha256=BASE_SHA256,wrapper_runtime_sha256=digest(__file__))


@contextmanager
def pad_runtime(catalog,row):
    """변경은 이 probe의 함수 바인딩과 메타데이터에만 국한한다."""
    point=point_specification(catalog,row);contract=feedback_contract(point)
    original_feedback=base.wrist_error_and_jacobian
    original_load,original_write,original_schema=base.load_inputs,base.write,base.SCHEMA
    def feedback(snapshot,wrist,guitar,com,groups,goal_position_G,goal_quaternion_G):
        wrist_error,wrist_jacobian=original_feedback(snapshot,wrist,guitar,com,groups,goal_position_G,goal_quaternion_G)
        body=snapshot['body_state']
        local=body.new_tensor(point['point_body_local_m']).expand(len(body),-1)
        actual_body=body[:,point['native_body_index']]
        actual_point=actual_body[:,:3]+base.apply(actual_body[:,3:7],local)
        wrist_offset=body.new_tensor(point['point_wrist_local_m']).expand(len(body),-1)
        goal_point_G=goal_position_G+base.apply(goal_quaternion_G,wrist_offset)
        instrument=body[:,guitar]
        goal_world=instrument[:,:3]+base.apply(instrument[:,3:7],goal_point_G)
        return replace_point_feedback(wrist_error,wrist_jacobian,
            actual_point-body[:,wrist,:3],goal_world-actual_point,snapshot['reset_body_snapshot'])
    def load(*args,**kwargs):
        document,actual,pins=original_load(*args,**kwargs)
        if base.row_identity(actual)!=base.row_identity(row):raise ValueError('패드 조건과 실행 후보 identity 불일치')
        pins[str(Path(__file__).resolve())]=digest(__file__)
        pins[str(BASE_PATH.resolve())]=BASE_SHA256
        pins.update(point['source_sha256'])
        return document,actual,pins
    def write(path,value):
        value=copy.deepcopy(value)
        if Path(path).name in ('settings.json','report.json'):
            value.update(schema=SCHEMA,condition='D',feedback=contract,
                feedback_kind=contract['kind'],runtime_sha256=digest(__file__),base_runtime_sha256=BASE_SHA256)
            if Path(path).name=='report.json':
                value['limitation']='preparation-only teacher pad feedback; no learned pressing, no pad feedback during policy pressing'
        original_write(path,value)
    base.wrist_error_and_jacobian=feedback
    base.load_inputs,base.write,base.SCHEMA=load,write,SCHEMA
    try:yield contract
    finally:
        base.wrist_error_and_jacobian=original_feedback
        base.load_inputs,base.write,base.SCHEMA=original_load,original_write,original_schema


def run(catalog_path,provenance_path,case,out,condition='C',num_envs=4,render=False):
    if condition not in ('C','D'):raise ValueError('D 패드 피드백은 C/D 인자로만 실행한다')
    catalog,row,_=base.load_inputs(catalog_path,provenance_path,case)
    with pad_runtime(catalog,row) as contract:
        report=base.run(catalog_path,provenance_path,case,out,'C',num_envs,render)
    report.update(schema=SCHEMA,condition='D',feedback=contract,feedback_kind=contract['kind'],
        runtime_sha256=digest(__file__),base_runtime_sha256=BASE_SHA256,
        limitation='preparation-only teacher pad feedback; no learned pressing, no pad feedback during policy pressing')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('probe',))
    parser.add_argument('--catalog','--plan',dest='catalog',type=Path,required=True)
    parser.add_argument('--provenance',type=Path,required=True)
    parser.add_argument('--case',required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--condition',choices=('C','D'),default='C')
    parser.add_argument('--num-envs',type=int,default=4);parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    if not 1<=args.num_envs<=64:parser.error('진단환경1..64 필요')
    report=run(args.catalog,args.provenance,args.case,args.out,args.condition,args.num_envs,args.render)
    if not report['completed']:raise RuntimeError('D 운반 실행 미완료; report.json 확인')


if __name__=='__main__':main()
