"""네이티브 실행 입력의 경로·출처 검증과 105축 준비 상태 복원을 관리한다.

읽는 순서: 내부 경로·출처 매핑 → 원 식별자·현재 바이트 검증 → 입력 봉인·준비 상태 복원.
"""
import json
import hashlib
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = Path(__file__).resolve().parent
ASSETS = NATIVE.parent / 'assets'
A = ASSETS / 'stability_adapter_2'
PROVENANCE = ASSETS / 'native_provenance.json'
# Historical identities are immutable labels, never external runtime locations.
HISTORICAL_ROOT = Path('/home/ajou/yigyu/3')


@lru_cache(maxsize=1)
def provenance_records():
    return tuple(json.loads(_project_file(PROVENANCE).read_text())['files'])


def _lexical(path):
    """Normalize before mapping, without following archived external symlinks."""
    path = Path(path)
    return Path(os.path.abspath(os.fspath(path if path.is_absolute() else ROOT / path)))


def _internal(path):
    path = Path(path)
    if path.is_absolute():
        if path == ROOT or ROOT in path.parents:
            return _project_file(path)
        # Accept the preceding manifest format while resolving inside this copy.
        try:
            path = path.relative_to(HISTORICAL_ROOT)
        except ValueError:
            return _project_file(path)
    return _project_file(ROOT / path)


def _project_file(path):
    """실제 파일을 읽기 전에 프로젝트 밖 경로와 외부 심볼릭 링크를 거부한다."""
    path = Path(path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError('Runtime input resolves outside project: ' + str(path))
    return path


@lru_cache(maxsize=1)
def _mapping():
    forward, reverse = {}, {}
    for row in provenance_records():
        original, internal = Path(row['original']), _internal(row['internal'])
        forward[str(original)] = internal
        for alias in row.get('aliases', []):
            forward[alias] = internal
            try:
                forward[str(ROOT / Path(alias).relative_to(HISTORICAL_ROOT))] = internal
            except ValueError:
                pass
        try:
            forward[str(ROOT / original.relative_to(HISTORICAL_ROOT))] = internal
        except ValueError:
            pass
        reverse[str(_lexical(internal))] = original
    return forward, reverse


def resolve_input_path(path):
    """Resolve runtime locations in this project; original identifiers stay stable."""
    path = _lexical(path)
    internal = _mapping()[0].get(str(path))
    if internal is not None:
        return _project_file(internal)
    for root in (ROOT, HISTORICAL_ROOT):
        if any((root / name) in path.parents for name in ('tab2body', 'stability_adapter_2')):
            raise FileNotFoundError('Legacy runtime input has no internal copy: ' + str(path))
    if path == ROOT or ROOT in path.parents:
        return _project_file(path)
    try:
        path = ROOT / path.relative_to(HISTORICAL_ROOT)
    except ValueError:
        pass
    return _project_file(path)


def original_input_path(path):
    """Return the immutable original identity of a migrated input or module."""
    path = _lexical(path)
    original = _mapping()[1].get(str(path))
    if original is not None:
        return original
    try:
        return HISTORICAL_ROOT / path.relative_to(ROOT)
    except ValueError:
        return path


def rebase_paths(value):
    """Rebase registered path values, preserving historical keys and all numbers."""
    if isinstance(value, dict):
        return {key: rebase_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rebase_paths(item) for item in value]
    if isinstance(value, str):
        if value.startswith('/') or value.startswith(('tab2body/', 'stability_adapter_2/', 'paper/', 'docs/')):
            resolved = _mapping()[0].get(str(_lexical(value)))
            if resolved is not None:
                return str(resolved)
    return value


def verify_provenance():
    """호출할 때마다 명시된 이전 목록의 해시와 현재 바이트가 일치하는지 검사한다."""
    import hashlib
    manifest = json.loads(_project_file(PROVENANCE).read_text())
    records = manifest['files'] + manifest.get('generated_files', [])
    for row in records:
        path = _internal(row['internal'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['internal_sha256']:
            raise ValueError('Internal native provenance SHA mismatch: ' + str(path))
    return {'verified_files': len(records), 'manifest': str(PROVENANCE)}


# 네이티브 105축 준비 상태의 입력 읽기·봉인·복원.
BASE = ROOT / 'paper/initial_pose/lower_body_release_v1'
HUMAN = ASSETS / 'tab2body/assets/smpl_mpl_hands_body.xml'
H0 = ROOT / 'docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125'
MANIFEST = A / 'working_initial_pose_v1/manifest.json'
LOWER = tuple(s+'_'+p+'_' for s in ('L','R') for p in ('Hip','Knee','Ankle','Toe'))


def read(path):
    return rebase_paths(json.loads(resolve_input_path(path).read_text()))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(resolve_input_path(path).read_bytes()).hexdigest()


def pin(config=None, extra=()):
    """현재 실행 입력을 봉인하고 과거 통과 근거의 경로 식별자는 유지한다."""
    import os
    from guitar_learning.historical_inputs import fingerprint_paths
    verify_provenance()
    paths = set(NATIVE.rglob('*.py')) | {PROVENANCE}
    if config:
        paths.add(resolve_input_path(config))
        candidate = read(config).get('candidate')
        if candidate:
            paths.add(resolve_input_path(candidate))
    historical = []
    for path in extra:
        lexical = _lexical(path)
        if any((root / name) in lexical.parents for root in (ROOT, HISTORICAL_ROOT)
               for name in ('tab2body', 'stability_adapter_2')):
            historical.append(str(original_input_path(lexical)))
        else:
            paths.add(resolve_input_path(path))
    pins = {str(path.resolve()): sha(path) for path in sorted(paths)}
    pins.update(fingerprint_paths(historical))
    return pins


def verify(pins):
    """보존된 과거 원본 바이트와 현재 내부로 이전한 구현을 모두 검증한다."""
    from guitar_learning.historical_inputs import fingerprint_paths
    actual = fingerprint_paths(pins)
    verify_provenance()
    return actual == {str(path): expected for path, expected in pins.items()}


def restore():
    import numpy as np
    manifest = read(MANIFEST)
    upper = dict(zip(manifest['joint_names'], manifest['target81_rad']))
    report, state = read(H0/'report.json'), read(H0/'states.json')[0]
    names = report['human_joint_names']
    assert len(names) == 105 and len(set(names)) == 105
    lower = {name: float(state['pos']) for name, state in zip(names, state['human_dof_states']) if name.startswith(LOWER)}
    assert len(lower) == 24
    q = np.array([upper[name] if name in upper else lower[name] for name in names], dtype=np.float32).astype(float)
    return {'schema': 'sa2_native105_initial_v1', 'joint_names': names, 'q_ref_rad': q.tolist(),
            'upper81_source': str(MANIFEST), 'lower24_source': str(H0), 'lower24_q_rad': lower, 'lower_deltas_rad': {},
            'guitar_position_W_m': manifest['guitar_actor_root_W_m'], 'guitar_quaternion_xyzw': manifest['guitar_quaternion_xyzw'],
            'expected_initial_state': read(manifest['native_initial'])['native_initial_state'],
            'support_candidate': manifest['candidate'],
            'scope': 'H0 lower24 restored by name with original upper81; actual native FK/property validation remains required.'}
