# 학습 작업 영역별 통합 (2026-10-28)

사용자 요청은 실제 학습 코드를 읽고 이해하기 쉽도록 비슷한 작업 영역을 크게 묶는 것이다. 단순한 파일 수뿐 아니라 기본 GPU 경로가 구형 CPU 환경을 불러오는 연결도 줄인다.

## 작업 범위

1. 실행·설정은 `training/launch.py`, GPU 수집은 `training/rollout.py`, 정책은 `training/policy.py`, 학습 일정은 `training/finger_skill_runner.py`, 로그·운영은 `training/training_log_io.py`로 모은다.
2. GPU18개 파일을9개로 묶는다. 환경·제어·보상은 유지하고, 접촉·기하·장면·진단·손가락 환경 보조를 각각 통합한다.
3. CPU 공통 좌표·관측은 `core/geometry.py`, 접촉·측정·안전은 `core/measurement.py`로 모은다.
4. 공용 설정·관측 상수·초기 자세 입력을 읽으려고 구형 CPU 실행기/장면까지 연결되는 참조를 분리한다. 준비 상태 클래스는 CPU native 세션 파일에 두고 GPU가 읽는 초기 자세 입력은 독립적으로 유지한다.

예상 활성 Python507→487개(25개 흡수,5개 새 통합 파일). 기본 진입점의 정적 의존성152개도 전후 동일 방법으로 재집계한다. 조건부 import를 포함한 수이며 실행 추적 수로 부르지 않는다.

## 체크리스트

- [x] 관련 지침·현행 문서 읽기 및 영역별 독립 조사
- [x] 변경 전507개 Python·문서·SHA와 기존 검사 기준 보존
- [x] 실행·수집·정책·로그·일정 통합
- [x] GPU 작업 영역 통합 및 순환/이름 충돌 해소
- [x] 공통 관측·측정 통합, CPU 전용 연결 분리
- [x] 실제 import·patch·명시적 소스 목록 및 활성 문서 갱신
- [x] 전체 CPU 검사 및 기존 실패 전후 비교
- [x] 독립 change-reviewer 검수·필요 보정
- [x] 파일 수·의존성 수·읽는 순서와 결과 문서화

## 보존 조건

- 변경 전 원문은 `guitar_learning/archive/20261028_before_domain_consolidation/`에 보관한다. 이전 보관본·과거 결과는 수정하지 않는다.
- native 소스·자산·`music_task.py`·`song/task.py`·`song/__init__.py`는 유지한다. 상속·관측561·J33·정책/물리 주기·보상·종료·PPO·저장 계약의 수치는 유지한다.
- `LEFT_FIELDS/LEFT_SCALES`와 `HISTORY_FIELDS/HISTORY_SCALES`는 공용 관측 파일에서 CPU/GPU가 같은 값을 사용하게 한다.
- 일반 CPU 세션은 별도 보존한다. 전체 native 구현을 한 파일로 억지로 묶거나 물리 동작을 변경하지 않는다.
- JSON·로그·실행 설정의 지연 import와 Isaac Gym 선행 로딩을 유지한다. 정의가 겹치는 private 이름만 명시적으로 바꾸고 AST 대조로 검증한다.
- 변경 전 checkpoint의 전체 소스 SHA 검증은 유지한다. 과거 모델을 새 소스에서 바로 재개하도록 pin을 바꾸거나 검사를 완화하지 않는다.
- 직전 통합의 전체188모듈 검사 결과를 사용한다. 독립 검수의507개 SHA와 현재 원문이 전부 일치함을 확인했다. 기존30모듈 실패는 변경 전후 원문 비교로 구분한다.

## 결과

완료. 활성507→487개, 기본 정적 연결152→40개(구현132→31개)로 줄였다. 전체188모듈158PASS/기존30실패의 전후 사례가 같고 새 실패는 없다. 정책9조건의 파라미터·RNG·출력 일치, 실제 GPU2환경/H8/small fresh2업데이트와 strict재개1업데이트를 확인했다. 보상·물리·종료·성공 계산과 protected/native 원문을 유지했다. 독립41모듈 표본·전체결과 대조·최종문서/GPU 원결과 검수 판정은 문제없음이다.

[완료 보고서](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_domain_consolidation/README.md)와 [현재 코드 읽기 지도](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md)를 따른다.
