# Native 목표 readback 실행 전 검수

검수일: 2026-10-07. 대상은 `run_native_target_readback.py`, `NATIVE_TARGET_READBACK.md` 및 연결에 필요한 기존 0.1초 runner·환경·설치 SDK getter 설명이다. 다른 코드·기존 동결 기록을 수정하지 않았으며 native 초기화·실행은 하지 않았다.

## 요약 판정

**문제없음. 실행 전 검수 완료. 남은 Critical / Warning / Suggestion 없음.** 실제 native readback 차이·움직임 재현 여부는 실행 후 확인할 사항이다.

## 코드·경계 확인

- Getter 결과를 즉시 복사하고 105개 float32/finite 계약을 검사한다(:21–33). 읽기 전후 human/guitar body·human DOF state, Python 제출 목표와 PD properties를 대조한다. 목표·pose/state를 추가 제출하는 호출은 없다.
- 원래 `step_physics` 직전과 직후에만 읽는다(:35–38). 목표 제출 이후 before-step k, 완료 after-step k+1의 48개 순서를 명시 검사한다(:75–77). 최초 t0도 getter 관측이며 0을 합성하지 않는다. stored−submitted 차이는 보고 값이고 exact 여부를 통과 gate에 넣지 않았다(:80–86).
- 기존 24step PALM_RATE runner·설정·제어 수식을 재사용한다(:60–65). 기존 runner의 sim 종료를 유지하며 outer finally가 환경 class/argv를 복원하고 실패 시 부분 readback을 보존한다(:89–96). 재사용 runner와 기본 환경을 수정하지 않는다.
- 기존 sensor 성공 실행의 raw7을 명시 SHA 입력으로 봉인하고 25/24개 prefix를 대조한다(:52–59·67–71). 새 native report/raw7도 입력에 추가하고 종료 전 SHA current 검사를 한다(:70–79). 이전 출력 보존 guard와 failure 기록을 확인했다.

## 순수 검증·해석 범위

Native import 없이 현재 observer class를 추출한 mock에서 24개 step/48개 before·after 순서가 맞았다. 의도적으로 다른 stored 값도 정상 관측으로 허용했다. 잘못된 shape·dtype·NaN 및 읽기 중 state 변경은 거절했다. 설치 SDK getter는 float32 배열을 반환하며 revolute target 단위는 rad다. 기존 센서 자료의 105개 회전형 DOF 범위를 재사용한다.

이번 단계는 저장된 native 목표와 제출 목표의 왕복 대조이며 actuator 토크·PD 원인·후기 목표 추종이나 기타 유지 성공을 증명하지 않는다. PD 변경 제안은 승인 전이고 이 코드에는 적용되지 않았다. 실행 후 native 계약, raw7 prefix, 읽기 불변성과 48개 관측의 시점·차이를 별도 검수해야 한다. 이 preflight 기록을 동결한다.
