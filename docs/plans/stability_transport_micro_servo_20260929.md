# Stability Adapter 5 mm transport 개선 계획

## 목표

- 5 mm transport에서 긴 MOVE ramp로 발생하는 overshoot를 줄인다.
- BRAKE 명령이 controller 내부 어느 단계에서 줄어드는지 로그로 구분한다.
- 관절 여유와 손가락 접촉 불균형을 시작 상태/이동 상태로 분리 진단한다.

## 체크리스트

- [x] 5 mm 미세 이동을 시작부터 저속 양방향 goal servo로 제어
- [x] 미세 이동용 Cartesian·joint action rate를 별도로 제한
- [x] 위치항, 상대속도 감쇠, world 감쇠, clamp 손실 진단 추가
- [x] servo-only 포화와 residual-induced 포화 분리
- [x] transport 시작 관절 margin 진단 추가
- [x] digit 접촉률과 overload 동시발생 통계 추가
- [x] 변경 전/후 동일 체크포인트 controller-only 비교
- [x] 관련 테스트와 문법 검사
- [x] change-reviewer 검수

## 검증 기준

- 5 mm stage가 첫 제어 frame부터 BRAKE/미세 servo를 사용한다.
- 미세 servo의 선형 명령이 world X/Y 각 축 0.50 mm/frame, world Z축 0.75 mm/frame 이내다.
- 기존 10 mm 이상 curriculum의 MOVE/BRAKE 동작은 유지된다.
- 로그에서 servo clamp와 residual clamp, controller 각 항을 독립적으로 확인할 수 있다.
- 동일 snapshot controller-only 240-frame 비교에서 최종 위치 오차와 p90 속도가 악화되지 않는다.
