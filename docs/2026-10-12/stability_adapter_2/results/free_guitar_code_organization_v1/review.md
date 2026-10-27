# 최상위 개발 패키지 정리 검수

**요약 판정: 문제없음.** 현재 개발 코드와 과거 실험 소비 소스의 구분, 새 import/루트 경로, source census와 원본 parity 분류가 정리 의도에 맞다. 추가 수정 요청 없음.

검수 범위는 `free_guitar_learning`의 README·AGENTS·origin_manifest, manifest에 대응하는15개 원본/현재 파일의 diff와 SHA, archive 링크, 두 실행기의 수집·pin·원본대조 경로, CPU 검증 로그, 단계1/2 결과 README다. 다른 담당자 파일은 수정하지 않았으며 검수 중 물리 실행·학습·기존 CPU 검사를 반복하지 않았다.

- manifest의15개 원본 SHA와15개 정리본 SHA를 직접 재계산하여 모두 일치함을 확인했다. 실제 변경은 import, 파일 위치에 따른 프로젝트 루트 깊이, 새 소스 수집·분류 및 관련 검사에 한정된다. 기하·접촉 기준·제어 동작은 바뀌지 않았다.
- `archive`는 `../stability_adapter_2/free_guitar_learning_v1`로 연결된다. README/AGENTS는 링크 대상과 과거 소스가 재현용 원본이며 수정 대상이 아니라고 명시한다.
- 두 실행기의 프로젝트 루트는 새 위치에서 `parents[1]`로 계산되며, 원035 설정과 기존 native runtime/assets를 참조한다. 새 기본 환경과 접촉 adapter의 native 의존성은 절대 패키지 import로 연결된다.
- source census는 새 최상위 패키지 자체의 `__init__.py`와 하위 모듈을 포함한다. namespace의 None-valued `__file__`를 건너뛰는 처리는 유지된다. 두 실행기는 기존 adapter와 새 패키지의 Python 소스를 실행 전 pin에 포함한다.
- 새 `free_guitar_learning` 소스는 bridge 의존성으로 분류하여 현재 실행의 사전/사후 SHA를 검사한다. 기존 native runtime과 자산에 대한 과거 expected SHA 검사는 유지한다. 새 package 소스를 과거 native expected map과 비교하여 실행을 차단했던 이전 종류의 오류는 발견되지 않았다.
- 제어 관련 테스트의 루트 경로와 import도 새 패키지에 맞춰 수정되었다. 저장된 로그에서 CPU40개 통과와 실행기 두 개의 도움말 정상 종료를 확인했다.
- 단계1/2 결과 README는 과거 실제 소스의 결과를 그대로 설명한다. 새 안내는 그 결과를 새 패키지의 native 재실행 성공으로 소급하지 않고, 이번 물리 실행/PPO 업데이트가0임을 명시한다.

검수의 한계: 새 경로의 실제 native 전체 실행은 수행하지 않았다. 이번 판정은 구조 정리와 정적 경로/분류 검수 및 보존된 CPU 검사 증거의 범위다.
