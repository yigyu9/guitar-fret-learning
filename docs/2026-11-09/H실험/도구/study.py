#!/usr/bin/env python3
"""H 비교의 입력을 봉인하고 명령만 생성한다. 학습·평가는 실행하지 않는다."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


SCHEMA = 'guitar_learning.horizon_study_seal.v1'
STUDY = Path(__file__).resolve().parents[1]


def project_root():
    return next(parent for parent in STUDY.parents if (parent/'guitar_learning/train.py').is_file())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def validate_design(design):
    """모든 조건의 경험량·전곡 전환·평가 시점이 같은 PPO 경계인지 확인한다."""
    if (design.get('schema') != 'guitar_learning.horizon_study.v1' or
            design.get('target') != 'C1' or design.get('horizons') != [32, 64, 128] or
            design.get('num_envs') not in (256, 512, 1024)):
        raise ValueError('등록된 C1/H32·64·128/공통 환경 수가 필요합니다')
    total = design['total_transitions']
    interval = design['checkpoint_every_transitions']
    quarter = design['full_song_after_transitions']
    if any(type(value) is not int or value <= 0 for value in (total, interval, quarter)):
        raise ValueError('전이 예산은 양의 정수여야 합니다')
    if quarter != total // 4 or total % 4 or interval != quarter:
        raise ValueError('전곡 전환과 저장 간격은 전체 경험 예산의 정확한 1/4입니다')
    if design['evaluation_transitions'] != list(range(0, total + 1, interval)):
        raise ValueError('평가는 초기·1/4·1/2·3/4·최종 경험량에 수행합니다')
    if (design.get('profile') != 'corrected' or design.get('size') != 'large' or
            design.get('include_pelvis') is not False or design.get('initial_support_std') != .15 or
            design.get('initial_finger_std') != .35 or design.get('evaluation_num_envs') != 32 or
            type(design.get('seed')) is not int):
        raise ValueError('H 이외의 공통 실험 조건이 올바르지 않습니다')
    for horizon in design['horizons']:
        if total % (design['num_envs'] * horizon) or interval % (design['num_envs'] * horizon):
            raise ValueError('경험 예산·저장·평가 시점은 모든 H의 수집 경계와 일치해야 합니다')
    return design


def source_paths(root):
    """실행 코드와 필수 입력만 선택한다. 생성 로그와 다른 연구 사본은 제외한다."""
    root = Path(root)
    paths = []
    selections = (('guitar_learning', True), ('guitar_learning/assets', False),
                  ('data/song_bundles/press_sequence_c1_v1', False),
                  ('scripts', True), ('isaacgym/python/isaacgym', False))
    for relative, python_only in selections:
        base = root/relative
        if not base.is_dir() or base.is_symlink():
            raise ValueError('필수 원본 디렉토리 누락 또는 링크: ' + relative)
        for current, dirs, files in os.walk(str(base), followlinks=False):
            dirs[:] = sorted(name for name in dirs if name != '__pycache__' and
                             not (python_only and name in ('tests', 'assets')))
            for name in list(dirs):
                path = Path(current)/name
                if path.is_symlink():
                    paths.append(path)
                    dirs.remove(name)
            for name in sorted(files):
                if not name.endswith(('.pyc', '.pyo')) and (not python_only or name.endswith('.py')):
                    paths.append(Path(current)/name)
    paths.append(root/'isaacgym/python/setup.py')
    return sorted(set(paths))


def manifest(root, paths=None):
    root = Path(root).resolve()
    result = {}
    for path in source_paths(root) if paths is None else paths:
        key = path.relative_to(root).as_posix()
        resolved = path.resolve(strict=True)
        if root not in resolved.parents or path.is_symlink() and os.path.isabs(os.readlink(str(path))):
            raise ValueError('프로젝트 외부/절대 링크는 복사할 수 없습니다: ' + key)
        if path.is_symlink():
            result[key] = {'link': os.readlink(str(path))}
        elif path.is_file():
            result[key] = {'sha256': sha(path), 'bytes': path.stat().st_size}
        else:
            raise ValueError('일반 파일이 아닌 입력: ' + key)
    return result


def copy_sources(root, destination, entries):
    for relative, record in entries.items():
        source, target = root/relative, destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if 'link' in record:
            target.symlink_to(record['link'])
        else:
            shutil.copy2(str(source), str(target))


def prepare(root, study):
    """임시 사본을 완전히 검증한 뒤 공개한다. 완성 사본은 덮어쓰지 않는다."""
    root, study = Path(root).resolve(), Path(study).resolve()
    design = study/'설계.json'
    validate_design(json.loads(design.read_text(encoding='utf-8')))
    destination, seal_path = study/'작업자료/source_snapshot', study/'기준봉인.json'
    if destination.exists() or destination.is_symlink() or seal_path.exists():
        raise ValueError('기존 사본/봉인을 덮어쓰지 않습니다. check로 검증하세요')
    destination.parent.mkdir(parents=True, exist_ok=True)
    design_sha, before = sha(design), manifest(root)
    temporary = Path(tempfile.mkdtemp(prefix='.snapshot_', dir=str(destination.parent)))
    try:
        copy_sources(root, temporary, before)
        if manifest(temporary) != before or manifest(root) != before or sha(design) != design_sha:
            raise ValueError('복사 중 입력/설계가 변경되었습니다. 안정된 입력에서 다시 준비하세요')
        payload = {'schema': SCHEMA, 'design_sha256': design_sha, 'files': before}
        payload['seal_sha256'] = hashlib.sha256(canonical(payload)).hexdigest()
        temporary.rename(destination)
        seal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    finally:
        if temporary.exists():
            shutil.rmtree(str(temporary))
    return check(root, study)


def differences(expected, actual):
    return sorted(key for key in expected.keys() | actual.keys() if expected.get(key) != actual.get(key))


def check(root, study):
    """봉인된 사본과 설계는 엄격 검증하고, 원 프로젝트의 후속 변경은 별도 보고한다."""
    root, study = Path(root).resolve(), Path(study).resolve()
    payload = json.loads((study/'기준봉인.json').read_text(encoding='utf-8'))
    seal_digest = payload.pop('seal_sha256')
    if payload.get('schema') != SCHEMA or hashlib.sha256(canonical(payload)).hexdigest() != seal_digest:
        raise ValueError('기준봉인 자체의 무결성 불일치')
    design = study/'설계.json'
    validate_design(json.loads(design.read_text(encoding='utf-8')))
    if sha(design) != payload['design_sha256']:
        raise ValueError('봉인 후 설계가 변경되었습니다. 새 연구 디렉토리가 필요합니다')
    snapshot = study/'작업자료/source_snapshot'
    if snapshot.is_symlink():
        raise ValueError('봉인 사본 루트는 링크일 수 없습니다')
    snapshot_changes = differences(payload['files'], manifest(snapshot))
    if snapshot_changes:
        raise ValueError('봉인 사본 변경: ' + ', '.join(snapshot_changes[:10]))
    try:
        active_changes = differences(payload['files'], manifest(root))
        active_error = None
    except (OSError, ValueError) as error:
        active_changes, active_error = [], str(error)
    return {'snapshot_valid': True, 'design_valid': True, 'files': len(payload['files']),
            'active_matches': not active_changes and active_error is None,
            'active_changes': active_changes, 'active_error': active_error,
            'seal_sha256': seal_digest}


def commands(root, study):
    verification = check(root, study)
    design = json.loads((study/'설계.json').read_text(encoding='utf-8'))
    snapshot = study/'작업자료/source_snapshot'
    prefix = [sys.executable, str(snapshot/'scripts/tab2body.py'), '--cache-root',
              str(snapshot/'.runtime/cache'), 'run', '-m', 'guitar_learning.tool.experiments.press_sequence']
    conditions = []
    for horizon in design['horizons']:
        batch = design['num_envs'] * horizon
        name = 'H%d_seed%d' % (horizon, design['seed'])
        output = snapshot/'study_outputs'
        training = output/'학습'/name/'attempt01'
        train = prefix + ['train', 'C1', '--size', design['size'], '--num-envs', str(design['num_envs']),
            '--horizon', str(horizon), '--updates', str(design['total_transitions']//batch),
            '--checkpoint-every', str(design['checkpoint_every_transitions']//batch), '--seed', str(design['seed']),
            '--improvement-profile', design['profile'], '--initial-support-std', str(design['initial_support_std']),
            '--initial-finger-std', str(design['initial_finger_std']), '--no-include-pelvis', '--out', str(training)]
        evaluations = []
        for transitions in design['evaluation_transitions']:
            filename = ('initial.pt' if transitions == 0 else 'final.pt' if transitions == design['total_transitions']
                        else 'checkpoint_%06d.pt' % (transitions//batch))
            checkpoint = training/'J'/filename
            evaluations.append({'transitions': transitions, 'checkpoint': str(checkpoint),
                'argv': prefix + ['evaluate', str(checkpoint), '--scope', 'full_song', '--num-envs',
                                 str(design['evaluation_num_envs']), '--out', str(output/'평가'/name/('T%09d' % transitions))]})
        conditions.append({'name': name, 'horizon': horizon, 'batch_transitions': batch, 'train': train,
            'evaluations': evaluations, 'render': prefix + ['render', str(training/'J/final.pt'), '--scope',
                'full_song', '--num-envs', '1', '--out', str(output/'동영상'/name)]})
    return {'verification': verification, 'cwd': str(snapshot), 'conditions': conditions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'check', 'commands'))
    args = parser.parse_args()
    try:
        result = globals()[args.command](project_root(), STUDY)
    except (OSError, ValueError, KeyError, StopIteration) as error:
        parser.exit(1, str(error)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
