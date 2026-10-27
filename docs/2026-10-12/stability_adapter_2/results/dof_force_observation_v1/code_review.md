# DOF force 관측의 실행 전 코드 검수

검수일: 2026-10-07. 대상은 `run_dof_force_observation.py`, `DOF_FORCE_OBSERVATION.md`와 연결에 필요한 기존 runner·환경·SDK API 설명이다. 코드와 기존 기록은 수정하지 않았으며 native 초기화·실행은 하지 않았다.

## 요약 판정

**문제없음. 실행 전 코드 검수 완료. 남은 Critical / Warning / Suggestion 없음.** 실제 센서 지원·측정값·동일 trajectory 여부는 실행 뒤 검증할 사항이다.

## 경계·보존 확인

- 관측 subclass는 scene 생성 후 `prepare_sim` 전에 센서를 활성화하고 지원 false를 중단한다(:21–31). Asset/actor DOF 이름을 대조하고 native type에 따른 Nm/N을 기록하며, 알 수 없는 type은 미검증으로 남긴다.
- 기존 `step_physics` 완료 뒤 force vector를 복사한다(:33–45). Shape·float32·finite 검사, human/guitar body 및 human DOF 상태·목표·PD properties 읽기 전후 비교가 있다. 추가 pose/state/목표 제출은 없다. Step0은 미측정 null이고 완료 step1–120을 기록한다.
- 원래 PALM_RATE runner와 제어 수식·설정·길이·물리를 재사용한다(:69–85). 기존 runner의 생성 실패 정리 및 종료 시 sim 해제를 유지하며, outer finally에서 환경 class와 argv를 복원하고 부분 센서 기록을 저장한다(:99–108). 실패한 실행은 failure와 부분 자료를 보존한다.
- 원자료 SHA 누락 Warning은 해소됐다. 이전 PALM_RATE의 직접 대조 배열 7개를 실행 전 봉인하고(:63–68), 새 native 배열 7개와 report를 명시 입력에 추가한 뒤 current SHA를 검사한다(:77–85). 기존 결과를 덮어쓰지 않는 출력 guard와 7개 배열 exact 대조도 확인했다.

## 순수 검증·해석 한계

Native import 없이 현재 observer class를 추출한 mock 검사에서 0인 force 값은 허용하고 잘못된 shape·dtype·NaN은 거절했다. 읽기 중 native 상태가 바뀌는 fixture도 중단했다. 센서 활성화와 단위 API는 설치 SDK 설명과 맞는다.

본 preflight는 실제 sensor 값이나 trajectory 동일성을 입증하지 않는다. DOF sensor 값을 actuator 전용 토크·접촉력·effort 포화·PD 원인 또는 기타 안정화 성공으로 해석하지 않는 계획과 report 범위가 일치한다. 실행 후 지원 여부, 120개 정렬 표본, 읽기 불변성, native 13개 계약 및 기존 7개 배열 exact 여부를 확인해야 한다. 이 코드 검수 기록은 동결한다.
