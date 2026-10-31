"""프로젝트 이동 시 실행 경로만 정규화하고 파일 내용·학습 계약은 검증한다."""
import hashlib
import json
import os
import copy
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PATH_SCHEMA = 'guitar_learning.project_paths.v1'
PREFIX = 'project://'
# 원문 manifest와 출처 식별자는 파일 위치가 아니다. 이전 사용자 경로도 그대로
# 보존해야 원래 checkout과 이동한 checkout에서 동일한 역사자료로 비교된다.
HISTORICAL_FIELDS = frozenset(('source_manifest', 'registered_from', 'original',
                              'original_identifier', 'original_project_root'))


def report_reference(path, directory):
    """보고서 디렉토리 기준 참조. 실행 디렉토리 전체를 함께 옮기면 그대로 해석한다."""
    if path is None:
        return None
    return dict(base='report_directory', path=Path(os.path.relpath(
        Path(path).resolve(), Path(directory).resolve())).as_posix())


def project_path(value):
    """project:// 식별자를 현재 checkout에서 찾는다. 루트 탈출은 허용하지 않는다."""
    if not isinstance(value, str) or not value.startswith(PREFIX):
        raise ValueError('project:// input identifier required: ' + str(value))
    relative = PurePosixPath(value[len(PREFIX):])
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError('invalid project input identifier: ' + value)
    path = ROOT.joinpath(*relative.parts)
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError('project input resolves outside project: ' + value)
    return path


def portable(value, *, root=None):
    """실행 계약의 경로 값과 SHA 사전의 경로 키를 같은 식별자로 바꾼다."""
    root = ROOT if root is None else Path(root)
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            name = portable(key, root=root)
            if name in result:
                raise ValueError('duplicate portable path identifier: ' + str(name))
            result[name] = (copy.deepcopy(item) if key in HISTORICAL_FIELDS
                            else portable(item, root=root))
        return result
    if isinstance(value, (list, tuple)):
        return [portable(item, root=root) for item in value]
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str) and Path(value).is_absolute():
        try:
            return PREFIX + Path(value).relative_to(root).as_posix()
        except ValueError:
            pass
    return value


def localize(value):
    """저장된 설정을 실행에 사용하기 직전에 현재 프로젝트 경로로 복원한다."""
    if isinstance(value, dict):
        return {localize(key): localize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [localize(item) for item in value]
    if isinstance(value, str) and value.startswith(PREFIX):
        return str(project_path(value))
    return value


def settings_digest(settings):
    data = json.dumps(portable(settings), sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def checkpoint_inputs(pins, settings, *, settings_path=None, lineage=()):
    """현재 파일은 모두 검증한 뒤 실행 입력·설정 snapshot·계보로 구분해 저장한다."""
    from guitar_learning.native.paths import resolve_input_path
    settings_path = Path(settings_path).resolve() if settings_path else None
    ancestors = {Path(path).resolve() for path in lineage}
    required, history, snapshot = {}, [], None
    for identifier, expected in pins.items():
        path = resolve_input_path(identifier).resolve()
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('checkpoint input changed before save: ' + str(path))
        if path == settings_path:
            text = data.decode('utf-8')
            if portable(json.loads(text)) != portable(settings):
                raise ValueError('run settings snapshot differs from checkpoint settings')
            snapshot = dict(original_identifier=str(path), original_project_root=str(ROOT),
                            sha256=expected, utf8=text)
        elif path in ancestors:
            history.append(dict(original_identifier=str(path), sha256=expected))
        else:
            key = portable(str(path))
            if not key.startswith(PREFIX):
                raise ValueError('required checkpoint input is outside project: ' + str(path))
            required[key] = expected
    if settings_path is not None and snapshot is None:
        raise ValueError('run settings file must be pinned before checkpoint save')
    return dict(schema=PATH_SCHEMA, required=required, lineage=history, run_settings=snapshot)


def validate_checkpoint_inputs(metadata):
    record = metadata.get('input_contract')
    if not isinstance(record, dict) or record.get('schema') != PATH_SCHEMA:
        raise ValueError('portable checkpoint input contract required; old absolute-path checkpoints are incompatible')
    if metadata.get('settings_sha256') != settings_digest(metadata['settings']):
        raise ValueError('checkpoint settings SHA mismatch')
    snapshot = record.get('run_settings')
    if snapshot is not None:
        if (hashlib.sha256(snapshot['utf8'].encode('utf-8')).hexdigest() != snapshot['sha256']
                or portable(json.loads(snapshot['utf8']), root=snapshot['original_project_root']) != metadata['settings']):
            raise ValueError('checkpoint run settings snapshot SHA/content mismatch')
    changed = []
    for identifier, expected in record['required'].items():
        path = project_path(identifier)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(identifier)
    if changed:
        raise ValueError('checkpoint input sources changed: ' + str(changed[:8]))
