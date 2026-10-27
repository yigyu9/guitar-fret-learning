# 테스트 하위 디렉토리 분리 검수

**요약 판정: 문제없음.** 변경은 테스트7개 이동과 필요한 import/파일 경로 및 안내 수정에 한정된다. 추가 수정 요청 없음.

- 이전 `guitar_learning_rename_v1/source_final`과 비교하여 모든 runtime Python 파일이 바이트 단위로 동일함을 확인했다.
- 테스트의 production import는 상위 패키지를 가리키는 `..`로 변경되었고 테스트 상호 import는 같은 `tests` 패키지의 `.`를 유지한다. 기존 검사 내용과 assertion은 변경되지 않았다.
- 자산 조회의 프로젝트 루트는 한 단계 깊어진 위치에 맞춰 `parents[2]`로 변경되었다. metadata fixture의 환경 파일과 package `__init__.py` 경로도 실제 상위 패키지를 가리킨다. 새 `tests/__init__.py`가 있어 package 기반 unittest discovery 경로가 성립한다.
- manifest의15개 원본 SHA와15개 현재 SHA를 재계산하여 모두 일치함을 확인했다. 이동한 테스트의 현재 경로가 반영되어 있다.
- README의 테스트 디렉토리 링크·실행 명령과 AGENTS의 테스트 배치 규칙이 새 구조에 일치한다.
- `checks.json` 및 `tests.log`에서 새 `guitar_learning/tests` 경로로 CPU40개가 통과했고 검증 입력이 보존되었음을 확인했다. 검수자는 테스트·물리·PPO 실행을 반복하지 않았다.

검수 중 다른 파일은 수정하지 않고 이 문서만 작성했다.
