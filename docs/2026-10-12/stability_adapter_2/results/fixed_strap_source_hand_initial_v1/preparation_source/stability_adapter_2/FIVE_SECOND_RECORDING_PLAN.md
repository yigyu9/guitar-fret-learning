# 실험마다 초기 값과 실제 Isaac Gym 5초 영상 저장

사용자 요청: 앞으로 각 실험의 초기 값을 저장하고 그 값으로 환경을 시작한 뒤
약5초의 경과를 실제 Isaac Gym camera로 녹화한다. 이전 결과·producer는 보존한다.

## 이번 소단계

- [ ] 재사용 녹화 helper와 새 recorded trial 진입점을 추가한다.
- [ ] 설정 JSON, 실제 초기81관절각/기타 world p·xyzw q/속도, 초기 PD 목표와 property,
  절대 strap rest length, 초기 경로 길이, 물리 조건과 입력 SHA를 저장한다.
- [ ] 시뮬레이션 시간0~5초(240Hz에서1200step)를 연속 실행한다.
  실제 camera의 전신·손 근접 두 시점을30fps로 저장하고 MP4를 만든다.
  t0 및5초 끝 장면을 포함한151frame이므로 영상 길이는151/30≈5.033초다.
  느린 재생이나 이전0.1초 영상 반복으로5초를 만들지 않는다.
- [ ] 현재 기준 목표각/PD/초기q/LA를 사용하는 smoke trial 한 번을 실행한다.
  첫24step 원자료5배열이 기존 기준과 exact인지 확인한다. 새 후보 탐색이 아니다.
- [ ] 영상의 실제 초기·중간·끝 frame, ffprobe 길이/프레임 수, 물리 로그/제약 위반,
  rendering 전후 상태 보존을 검증하고 독립 검수를 받는다.

새 recorded trial은 초기 설정·기타 초기 이동과 named main target offsets,
왼팔 kp/kd 배율을 명시적으로 받는다. 현재 상수 목표 비교에 사용하고 이후 feedback
runner에서도 같은 녹화 helper를 사용한다. 오래된 runner/batch를 변경하지 않는다.
새 실험의 기본 경로는 run_recorded_trial이며, 짧은 진단이 따로 필요하면 진단을
별도 실행으로 기록하고 동일 조건의5초 녹화를 함께 남긴다.

root·하체 물리고정, 몸통9 초기 목표, main66 합성 경로, self-collision ON,
기타 free/gravity/passive strap을 유지한다. 초기화 이후 state/pose 덮어쓰기는 없다.
잘못된 자세·palm-up proxy 위반은 시각화를 숨기지 않고 위반 기록과 함께 끝까지
관측한다. 이는 제약 통과나 후보 채택이 아니다. 비유한 물리값/API 오류/사용자 중단은
partial 기록과 확보된 실제frame의 영상을 남기고 정상5초 완료로 표시하지 않는다.

계획·helper·runner·trial은 stability_adapter_2에 저장한다. 검증 결과와 로그/원본PNG/
MP4/초기설정/설명은 docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1이다.
봉인 후 완료 체크는 메인 PLAN.md와 run 결과에 남긴다.
