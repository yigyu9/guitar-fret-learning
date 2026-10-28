"""준비 자세를 한 번 복원한 뒤 실제 물리에서 짧고 유한한 제어를 수행한다.

읽는 순서: 입력 경로·해시 검증 → 복원 계약 로드 → 제어 시계 보기 → 상태 1회 복원.
"""
import copy
import json
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from guitar_learning.core.geometry import frame
from guitar_learning.native.paths import resolve_input_path, original_input_path, rebase_paths, verify_provenance


ROOT = Path(__file__).resolve().parents[2]
BASELINE_CONFIG = resolve_input_path(ROOT / 'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json')
PROBE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'
PREPARED_SNAPSHOT = PROBE / 'prepared.json'
INITIAL_VALUES = PROBE / 'initial_values.json'
PROBE_INPUTS = PROBE / 'inputs_before.json'
CONTROL_PHASE_OFFSET_STEPS = 5280
SOURCE_SHA256 = {
    BASELINE_CONFIG: '58d5b0946b4352abb76aebb15499269530f4f9c68a8fa9e784b5dee4c1bed26b',
    PREPARED_SNAPSHOT: '49631241132d303e36ae02cc40a3a6e035f68d3dd54982f8a4a2c3b50e0970db',
    INITIAL_VALUES: '5b84e68b085ef63133bb1834c65d25c5413584d36a7998b31c9253beaac75e1b',
    PROBE_INPUTS: '4cc689037ec0a8bd67b4e2cdca005aee1d479d82f3b957e889bae6e5a40f1588'}


# 파일 해시는 공용 스트리밍 구현으로 계산한다.
from guitar_learning.training.training_log_io import digest as _sha


def _verified_json(path):
    if _sha(path) != SOURCE_SHA256[path]:
        raise ValueError('Prepared reset source SHA mismatch: ' + str(path))
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def _prepared_input_paths():
    """정확히 봉인된 상태·설정과 모델이 선언한 모든 메시의 입력 경로를 찾는다."""
    initial = _verified_json(INITIAL_VALUES)
    paths = set(SOURCE_SHA256)
    for asset in initial['loaded_assets']:
        xml = resolve_input_path(asset['path'])
        paths.add(xml)
        tree = ET.parse(xml)
        compiler = tree.find('compiler')
        folder = xml.parent / (compiler.get('meshdir', '') if compiler is not None else '')
        paths.update((folder / mesh.attrib['file']).resolve() for mesh in tree.findall('./asset/mesh'))
    return frozenset(paths)


def prepared_input_paths():
    return set(_prepared_input_paths())


@lru_cache(maxsize=1)
def _load_prepared_reset_contract():
    verify_provenance()
    baseline, prepared, initial, before = (_verified_json(path) for path in (BASELINE_CONFIG, PREPARED_SNAPSHOT, INITIAL_VALUES, PROBE_INPUTS))
    source_pins = {str(path.resolve()): value for path, value in SOURCE_SHA256.items()}
    expected = {str(Path(path).resolve()): value for path, value in before.items()}
    for path in prepared_input_paths() - set(SOURCE_SHA256):
        value = _sha(path)
        if expected.get(str(original_input_path(path))) != value:
            raise ValueError('Prepared reset model SHA mismatch: ' + str(path))
        source_pins[str(path)] = value
    state = prepared['sample']['native']
    if state['physics_step'] != CONTROL_PHASE_OFFSET_STEPS:
        raise ValueError('Expected actual saved22s preparation sample')
    target = np.array(prepared['metadata']['prepared_target105_rad'], dtype=float)
    if target.shape != (105,) or not np.isfinite(target).all():
        raise ValueError('Finite saved final target105 required')
    return dict(config=rebase_paths(baseline), state=state, target105=target, initial=rebase_paths(initial), source_sha256=source_pins)


def load_prepared_reset_contract():
    """프로세스마다 한 번 검증하고 리셋마다 상태·목표의 수정 가능한 독립 사본을 제공한다."""
    return copy.deepcopy(_load_prepared_reset_contract())


class ControlPhaseView:
    """제어 일정의 경과 틱만 보정하며 연결된 네이티브 메서드는 실제 시계를 유지한다."""
    def __init__(self, scene):
        object.__setattr__(self, '_scene', scene)

    @property
    def steps(self):
        return self._scene.steps + CONTROL_PHASE_OFFSET_STEPS

    def __getattr__(self, name):
        return getattr(self._scene, name)

    def __setattr__(self, name, value):
        if name in ('steps', '_scene'):
            raise AttributeError('Control phase and actual scene clock cannot be assigned through the view')
        setattr(self._scene, name, value)


def _assign(record, value):
    for name in record.dtype.names:
        if record[name].dtype.names:
            _assign(record[name], value[name])
        else:
            record[name] = value[name]


def _state_all():
    from isaacgym import gymapi
    return gymapi.STATE_ALL


def _restore_once(scene, contract, state_all):
    initial, saved = contract['initial'], contract['state']
    if scene.steps != 0 or not scene.initialization_complete:
        raise ValueError('Prepared state initialization is allowed only before any actual physics step')
    for names, key in ((scene.names, 'joint_names'), (scene.human_bodies, 'human_body_names'), (scene.guitar_bodies, 'guitar_body_names')):
        if list(names) != initial[key]:
            raise ValueError('Prepared reset native name/order mismatch: ' + key)
    if scene.loaded_assets != initial['loaded_assets'] or scene.chair_placement != initial['chair_initial_placement']:
        raise ValueError('Prepared reset asset/chair configuration mismatch')
    for key in scene.pd_properties.dtype.names:
        if not np.array_equal(scene.pd_properties[key], np.asarray(initial['native_PD_properties'][key], dtype=scene.pd_properties[key].dtype)):
            raise ValueError('Prepared reset native PD property mismatch: ' + key)
    if not np.array_equal(scene.control_kp, initial['control_K105']) or not np.array_equal(scene.control_kd, initial['control_D105']):
        raise ValueError('Prepared reset original finite gains mismatch')
    target = contract['target105']
    if np.any(target < scene.lower) or np.any(target > scene.upper):
        raise ValueError('Saved prepared target outside original native limits')
    before = scene.native()
    root_index = scene.human_bodies.index('Pelvis')
    if before['human_body_states'][root_index]['pose'] != saved['human_body_states'][root_index]['pose'] or before['chair_body_states'] != saved['chair_body_states']:
        raise ValueError('Fixed human root/chair must already match the prepared sample')
    scene.initialization_complete = False
    try:
        dofs = scene.gym.get_actor_dof_states(scene.env, scene.human, state_all).copy()
        guitar = scene.gym.get_actor_rigid_body_states(scene.env, scene.guitar, state_all).copy()
        if len(dofs) != len(saved['human_dof_states']) or len(guitar) != len(saved['guitar_body_states']):
            raise ValueError('Saved prepared state dimensions mismatch')
        for record, value in zip(dofs, saved['human_dof_states']):
            _assign(record, value)
        for record, value in zip(guitar, saved['guitar_body_states']):
            _assign(record, value)
        if scene.gym.set_actor_dof_states(scene.env, scene.human, dofs, state_all) is False:
            raise RuntimeError('Prepared human DOF reset failed')
        # 인체 관절체의 강체 상태 설정 함수는 q를 손상시키므로 절대 호출하지 않는다.
        if scene.gym.set_actor_rigid_body_states(scene.env, scene.guitar, guitar, state_all) is False:
            raise RuntimeError('Prepared guitar rigid-body reset failed')
        scene.target = target.astype(np.float32)
        scene.last_target = scene.target.astype(float).copy()
        if scene.gym.set_actor_dof_position_targets(scene.env, scene.human, scene.target) is False:
            raise RuntimeError('Prepared native POSITION target reset failed')
    finally:
        scene.initialization_complete = True
    actual = scene.native()
    dof_error = max(abs(float(a[key]) - float(b[key])) for a, b in zip(actual['human_dof_states'], saved['human_dof_states']) for key in ('pos', 'vel'))
    guitar_velocity_error = max(abs(float(a['vel'][kind][axis]) - float(b['vel'][kind][axis])) for a, b in zip(actual['guitar_body_states'], saved['guitar_body_states']) for kind in ('linear', 'angular') for axis in 'xyz')
    errors = {}
    for actor in ('human', 'guitar'):
        position, angle = [], []
        for a, b in zip(actual[actor + '_body_states'], saved[actor + '_body_states']):
            ap, ar = frame(a); bp, br = frame(b)
            position.append(float(np.linalg.norm(ap - bp)))
            angle.append(float((ar.inv() * br).magnitude()))
        errors[actor] = dict(max_position_error_m=max(position), max_rotation_error_rad=max(angle))
    if dof_error > 1e-6 or guitar_velocity_error > 1e-6 or errors['guitar']['max_position_error_m'] > 1e-6 or errors['guitar']['max_rotation_error_rad'] > 1e-6:
        raise RuntimeError('Prepared DOF/guitar state reset readback failed')
    return dict(actual_initial_state=actual, human_DOF_pos_vel_max_error=dof_error, guitar_velocity_max_scalar_error=guitar_velocity_error, body_pose_readback=errors,
                human_body_exact_checkpoint_claim=False, source_velocities='Saved human DOF velocities and guitar rigid-body velocities preserved; human link velocities reconstructed by native articulation',
                state_set_calls=dict(human_DOF=1, guitar_rigid_body=1, human_rigid_body=0, native_POSITION_target=1))
