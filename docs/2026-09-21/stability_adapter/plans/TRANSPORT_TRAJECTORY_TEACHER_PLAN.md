# TRANSPORT trajectory teacher 개선 계획

상태: 구현·학습·렌더 완료, 승격 실패

## 목표

실패한 teacher를 더 오래 모방하지 않고, grip을 유지한 상태에서 `L_Thorax`
하위 9DoF가 기타를 초기 위치·회전 방향으로 실제 이동시키는 teacher를 만든다.

## 체크리스트

- [x] LOAD_SETTLE 종료 자세 기준 1 mm + 1 deg 목표 생성
- [x] minimum-jerk 기타 궤적과 guitar-relative palm 목표 생성
- [x] 0.75 mm hybrid lead smoke: grip 유지, overload 없음, 그러나 strap drift로
  position error=17.86 mm, rotation error=2.68 deg timeout
- [x] grip force 여유를 이용해 2.0 mm translation / 0.5 deg rotation lead 적용
- [x] 2.0 mm smoke: position error=23.60 mm, finger loss; lead 증가가
  반대 방향 drift를 키우므로 contact 반력 방향이 command와 반대임을 확인
- [x] -0.75 mm / -0.25 deg reverse-lead audit: 215 MOVE frame에
  position error=11.70 mm로 증가, 단순 부호 문제 아님
- [x] 2 mm / 0.5 deg SE(3) leash smoke: grip/pressure 정상,
  position error=3.07 mm, rotation error=0.68 deg timeout
- [x] 3 mm / 1 deg SE(3) leash smoke: grip/pressure 정상,
  position error=1.94 mm, rotation error=0.60 deg timeout
- [x] 5 mm / 2 deg SE(3) leash smoke: finger loss, position error=10.13 mm;
  과도한 leash로 폐기
- [x] 3 mm / 1 deg leash + arm anti-windup ±0.04 rad smoke: ±0.02 rad와
  결과 동일, 병목 아님; 더 안전한 ±0.02 rad로 복귀
- [x] 최종 teacher gate: grip/pressure 정상, position error=1.94 mm,
  rotation error=0.60 deg timeout, 승격 실패
- [x] 상대속도 감쇠에 60 Hz `dt` 적용
- [x] arm target 누적 및 실측각 ±0.02 rad anti-windup
- [x] 접촉 flicker 시 궤적 정지 + 25% arm recovery
- [x] angular palm task 연결
- [x] 실패 teacher BC 차단
- [x] 단위 테스트와 1 mm + 1 deg GPU teacher smoke
- [x] 실패 라벨 diagnostic BC 20,000 update: 1,743 samples,
  loss=2.68e-6, teacher/promotion eligible=false
- [x] teacher-guided learned-arm 진단 영상 렌더: 4,428 frame에서
  finger loss, position error=24.58 mm, rotation error=3.57 deg
- [x] reviewed 오버레이와 JSON/README 저장

## 승격 조건

- teacher와 learned-arm이 모두 SETTLE 30 frame을 완료한다.
- 위치 오차는 0.2 mm 이하, 회전 오차는 0.2 deg 이하이다.
- grip loss, dangerous pressure, hard overload가 없다.
