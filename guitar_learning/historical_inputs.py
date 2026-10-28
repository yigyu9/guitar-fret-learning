"""과거 학습 근거에 봉인된 원본 바이트를 다시 검증한다.

과거 코드는 자료로만 취급한다. 현재 실행 소스는 별도로 해시를 계산하며,
옛 근거 목록의 검증을 통과해도 과거 프로그램을 불러오지 않는다.

읽는 순서: 보관 목록 조회 → fingerprint_paths → 근거 경로·해시 반환.
"""
from collections.abc import Mapping
from functools import lru_cache
import json
import os
from pathlib import Path

_STORE = Path(__file__).resolve().parent / 'assets/historical_inputs'
_PROJECT = Path(__file__).resolve().parents[1]
_LEGACY_ROOTS = tuple(str(_PROJECT / name) + '/' for name in ('tab2body', 'stability_adapter_2'))


@lru_cache(maxsize=1)
def _index():
    document = json.loads((_STORE / 'index.json').read_text())
    if document.get('schema') != 'guitar_learning.historical_inputs.v1':
        raise ValueError('unsupported historical input index')
    return document['entries']


# 파일 해시는 공용 스트리밍 구현으로 계산한다.
from guitar_learning.training.training_log_io import digest as _digest


def _checked_sha(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in '0123456789abcdef' for char in value)):
        raise ValueError('expected input SHA256 must be lowercase hexadecimal')
    return value


def fingerprint_paths(paths):
    """현재 입력의 해시를 구하거나 정확히 보존된 과거 입력 버전을 검증한다.
    
    Mapping은 예상 SHA256을 제공하며 원래 키를 유지한다. 등록된 과거
    (경로, SHA) 버전은 내부 자료를 다시 해시한다. 나머지 Mapping 항목은
    현재 파일의 SHA가 정확히 일치해야 한다. 반복 가능한 경로 입력에서는
    현재 경로는 실제 파일을, 옛 경로는 유일하게 봉인된 원본을 사용한다.
    알 수 없는 옛 경로를 외부의 과거 폴더에서 대신 찾지 않는다.
    """
    expected = paths if isinstance(paths, Mapping) else None
    result = {}
    for source in paths:
        # 옛 경로 이름은 문자열 경로로 정규화한다. 심볼릭 링크를 해석하면 보존된
        # 원본 바이트를 선택하기 전에 삭제된 외부 디렉터리를 살펴보게 된다.
        lexical = os.path.abspath(os.fspath(source))
        legacy = lexical.startswith(_LEGACY_ROOTS)
        wanted = _checked_sha(expected[source]) if expected is not None else None
        entry = _index().get(lexical) if legacy or wanted is not None else None
        if legacy and wanted is None:
            wanted = entry.get('default_sha256') if entry else None
            if wanted is None:
                raise ValueError('unknown or ambiguous historical input: ' + lexical)
        if entry and wanted in entry['versions']:
            actual = _digest(_STORE / 'objects' / (wanted + '.data'))
            if actual != wanted:
                raise RuntimeError('historical input SHA mismatch: ' + lexical)
            key = source if expected is not None else lexical
        elif legacy:
            raise ValueError('unknown historical input SHA: ' + lexical)
        else:
            path = Path(source).resolve()
            actual = _digest(path)
            if wanted is not None and actual != wanted:
                raise RuntimeError('live input SHA mismatch: ' + str(path))
            key = source if expected is not None else str(path)
        result[key] = actual
    return result


def evidence_input_pins(expected):
    """정확한 근거 Mapping에 필요한 실제 파일의 SHA를 반환한다.
    
    실제 경로로 변환한 뒤에도 필요한 원본 SHA를 유지한다. 이후 파일 전수
    검사에서는 실제 읽은 해시를 이 원래 값과 비교해야 한다.
    """
    if not isinstance(expected, Mapping):
        raise TypeError('expected input SHA Mapping required')
    fingerprint_paths(expected)
    pins = {}

    def require(path, sha):
        key = str(path)
        if key in pins and pins[key] != sha:
            raise RuntimeError('conflicting physical evidence SHA: ' + key)
        pins[key] = sha

    for source, wanted in expected.items():
        lexical = os.path.abspath(os.fspath(source))
        entry = _index().get(lexical)
        if entry and wanted in entry['versions']:
            index_path = _STORE / 'index.json'
            if str(index_path) not in pins:
                require(index_path, _digest(index_path))
            require(_STORE / 'objects' / (wanted + '.data'), wanted)
        else:
            require(Path(source).resolve(), wanted)
    return pins


def evidence_input_paths(expected):
    """정확한 근거 Mapping을 유지하면서 실제로 사용하는 경로를 반환한다."""
    return {Path(path) for path in evidence_input_pins(expected)}
