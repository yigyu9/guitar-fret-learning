# V11: Chest 방향을 유지하는 Spine–Chest 상대 위치 목표

V10은 source4 초기 상태를 유지하고 Chest finite 목표만 전방0.2°로 바꿨으나 전체 정지 기준을 통과하지 못했다. 마지막1초의 source Chest gap은0.055294~0.079390mm로 V8의0.060393~0.085125mm보다 약0.005mm 작을 뿐이다. Chest 원점은 Spine capsule 중심에 비해0.01309mm 후퇴했다. 더 큰 기울기나 압력으로 곧바로 대체하지 않는다. V9의20N 정상 포화와 Spine 최대4.722689°도 보존한다.

## 실행 후보와 가정

새 `posture_target_v2`에서 source4의 초기 candidate·기타·Root·cube·하체·손가락은 그대로 둔다. Spine world 방향을 humanoid 수평 hip-right의 음의 방향으로0.3° 회전시키고, Chest world 방향은 source4의 방향으로 유지하도록 Spine3+Chest3 finite 목표를 fit한다. 이것은 Chest 원점을 Spine에 대해 전진시키려는 **검증 전 가설**이며 실제 동적 전진과 접촉 성공을 보장하지 않는다. 필요시 기존과 같은 제한적인 left12 world-palm/self-clearance 보정을 명시한다. 실제 오른팔12 world IK와 발 최종목표의 소유권을 유지한다.

상체 K150/D1·원 effort cap·Chest cap20N·기존7→9mm(.75..1.25초) spring-preload schedule을 보존한다. 10mm/더 큰 힘을 쓰지 않는다. 초기상태 덮어쓰기나 기타 직접힘·고정·부착·스트랩을 추가하지 않는다. 원105 입력/97 비영범위/zero8을 구분한다.

1. 새 목표의 calibrated FK·원 limits·보존 채널·source 전체 충돌 관련성을 검증하고 입력 SHA를 기록한다. 초기 형상 적합과 finite 목표 예측은 별개로 적는다.
2. 새 wrapper/analyzer를 만들고 독립 검수·문법 검사를 한다. 기존15 동적 기준과 schedule/KD/target 연결을 유지하며, 이번에는 실제 Spine 전체 tilt≤5°도 추가로 판정한다.
3. `native_static_v11`을5초 실행한다. 기타 이동≤30mm/회전≤5°/넥≤3°/좌우≤20mm, Torso·Chest total≤5°/right≤3°,1..5초 Chest+오른상완 접촉≥95%/양발≥95%,last1 네 발 부위 높이·각·속도·흔들림을 그대로 요구한다.
4. 전체 통과 시 동일 실행 재현 후 압현·타현, 그다음 왼손 해제15초를 진행한다. 그 전에는 새 PPO를 시작하지 않는다.

- [ ] 새 목표 생성·source 검증과 변경 근거 기록
- [ ] 새 실행·분석 코드 검수와 문법 검사
- [ ] 실제5초 전체 기준 및 Spine 추가 기준 판정
- [ ] 통과 재현→압현/타현→왼손 해제, 실패라면 원자료 진단부터 이어가기

이 leaf 계획은 소비 후 수정하지 않고 결과는 새 progress 및 같은 자료 디렉터리에 기록한다.
