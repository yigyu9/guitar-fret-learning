# 과거 전문 학습·실험 보관

사용자가 앞으로 사용하지 않을 과거 전문 학습·실험을 선별해 보관하라고 요청했다. 현재 J v3 학습과 평가·영상·짧은 손가락 진단·곡 입력 도구·기존 song/CPU/오른손 실행은 유지하는 것으로 범위를 정한다. 과거 성능 자료와 학습 결과는 이번 정리 대상이 아니다.

## 범위와 방법

1. 내부 import·동적 문자열·source pin·외부 진입점을 조사한다. 검증: 유지할 실행 경로가 보관 후보를 참조하는지 확인한다.
2. 이전 소스·검사·문서를 SHA manifest와 함께 보관한다. 공용 초기화 구현만 현재 runtime으로 옮긴 뒤 과거 local_skills/joint/song/song_reward_v2/transition/transition_refinement/transition_refinement_runtime_v2/contact_recovery 및 모방·타이밍·전문가 실행기/환경과 전용 검사를 활성에서 제거한다. 검증: 보관 원문 SHA, 남은 import·선택된 모듈의 독립 import와 관련 검사를 확인한다.
3. README·문서 지도·코드 해설과 소스 기준을 갱신하고 전체 CPU 및 짧은 실제 GPU 학습·재개·평가를 확인한다. 검증: 현재 기본32파일의 계산 보존, 기존 실패와 새 실패 구분, 독립 change-reviewer 검수, 보관본 import 금지.

## 보존 조건

- native/자산·provenance·과거 입력 CAS·물리·보상·제어·성공 판정은 유지한다.
- `quality/fretting_quality.py`와 `strike_quality.py`는 CPU 곡·현재 진단이 사용하는 공용 측정이므로 남긴다.
- 기존 song의 native 준비0초를 제공하던 작은 초기화 계층은 `runtime/persistent_environment.py`에 옮긴다. 전문 timing/BC 계층을 함께 불러오지 않는다.
- 과거 전용 테스트는 해당 코드와 함께 보관한다. 공용·현재 학습 검사를 실패 회피 목적으로 제외하지 않는다. 공용 테스트의 없어진 과거 진입점 안내는 현재 도구·보관 확인으로 바꾼다.
- 이전 checkpoint는 source pin이 달라 현재 트리에서 strict 재개하지 않는다. 입력 SHA 검사를 우회하거나 보관본을 현재 import하는 facade를 만들지 않는다.

## 체크리스트

- [x] 의존성·유지 대상·보관 후보 확정
- [x] 수정 전 원문·SHA와 유지 경로 기준 보관
- [x] 공용 준비0초 초기화 계층 분리와 전용 영역 보관
- [x] 잔류 import·구문·공용 동작·전체 CPU 검사
- [x] 문서·현재 코드 목록·해설 기준 갱신
- [x] 실제 GPU 새 학습·동일 소스 재개·독립 평가
- [x] 독립 검수와 최종 기록

최종:220파일(193 Python)을 원문 SHA와 함께 보관, 활성281개 유지. 기본32파일의 계산 불변·전체CPU117모듈100통과/17기존동일실패·GPU새학습32전이/재개16전이/전곡2에피소드 정상완료·독립검수 문제없음. [결과 기록](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/README.md).
