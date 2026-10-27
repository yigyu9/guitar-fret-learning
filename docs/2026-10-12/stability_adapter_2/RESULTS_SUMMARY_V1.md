# 현재 작업 결과 정리

기타를 자유롭게 두고 적시 타현 4회를 수행하는 단계까지 왔다. 최신 준비구간 감쇠 비교는 잘못된 타현 0회, 5초 전체 PLAY 지속을 기록했다. 이후 음표 6개를 놓쳤으며, 반대 방향·다른 줄 연주와 사용자 기타 범위의 전 구간 유지까지 해결한 상태는 아니다.

## 현재 환경과 제어

- Isaac Gym/PhysX 실제 5초 시뮬레이션이다. Strap은 없으며 기타는 중력·실제 접촉으로 자유롭게 움직인다. Root와 하체는 fixed-link, Torso/Spine/Chest는 기존 PD 목표를 유지한다.
- 기타 고정, 손 강제 부착, 지속 pose 덮어쓰기, 기타를 잡아당기는 외력은 사용하지 않는다. 왼손 손바닥의 지속 접촉은 성공 필수 조건이 아니다.
- Strike 체크포인트는 [strike_010000.pt](/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt)다. 현재 실제 오른팔 9관절 목표는 기타의 현재 위치 기준 기하 보정기가 소유한다. 체크포인트 팔 9출력은 기록용이고 손가락 21출력은 실제 제어하며 중지·약지 4개 관절에 +0.2rad 보정을 적용한다. 전체30출력이 그대로 구동된다고 해석하지 않는다.
- 학습 업데이트는 0이다. Fret는 아직 연결·검증하지 않았다.

## 최근 조건 비교

모든 비교는 같은 초기값의 실제5초/1200 physics steps/151 camera frames다. 회전 변화는 초기 기타 방향에 대한 SO3 각거리이며, 사용자 Euler box의 통과 여부와 다른 지표다. 적시타현과 잘못된타현은 원본 source 판정을 그대로 집계했다.

| 조건 | 적시 타현 | 잘못된 타현 | 놓친 음표 | 기타 최대 / 끝 회전 변화 | 상태 |
|---|---:|---:|---:|---:|---|
| [종료 후 오른손 회수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/analysis/summary.json) | 4 | 4 | 2 | 7.10° / 2.72° | 3.633초 종료 후 회수 |
| [타현 전 측면 접근](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/analysis/summary.json) | 4 | 2 | 6 | 7.10° / 4.36° | 5초 PLAY 계속 |
| [준비 도달을 기억](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/analysis/summary.json) | 4 | 4 | 4 | 9.37° / 5.84° | 3.817초 종료 후 회수 |
| [회복 후 현재 음표 미리 준비](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/analysis/summary.json) | 4 | 1 | 6 | 7.10° / 3.35° | 5초 PLAY 계속 |
| [준비 이동 중 감쇠 복원](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/analysis/summary.json) | 4 | 0 | 6 | 7.10° / 4.36° | 5초 PLAY 계속 |

종료 후 회수는 종료 시 목표를 그대로 유지해 기타가 크게 기울던 현상을 줄였다. 측면 접근은 잘못된 줄 통과를 줄였지만 준비와 타현 목표가 반복 전환됐다. 도달을 기억하는 조건은 실제 ENTRY까지 도달하지 못했고 결과가 나빠 미채택했다. 회복 완료 뒤 현재 음표를 미리 준비하면 잘못된 타현은1회로 줄었지만, UP 물리 타현이 시간 조건만 통과하고 위치 조건에서 제외됐다. 최신 준비구간 감쇠 복원은 잘못된 타현을0회로 줄였지만 적시 타현 수는4회 그대로다. 각 변화의 단독 인과를 확정한 결과는 아니다.

## 최신 완료 결과

- 적시 타현4회는 모두 zero-based string2 DOWN, native 이름 G:string3이다. command 시각은1.316667/1.583333/2.433333/2.816667초, source timing 오차는+16.481/−17.501/−0.714/−3.153ms다.
- 이후 miss6회. 추가 physical 타현은4.233333초에약649ms 일찍 발생해 적시 타현에 포함되지 않는다. Physical 타현은 source의 swept virtual pick 판정이며 native 강체 접촉 자체와 같은 뜻이 아니다.
- 최신 기타 최대 회전7.095455°/종료4.364181°, 최대 위치 변화46.353646mm/종료33.242454mm. 초기 배치에서 이동이 남아 있어 초기상태를 완전히 유지했다고 표현하지 않는다.
- 사용자 기타 범위 판정은 전체236/300, PLAY190/251이다. 전 구간 범위 유지가 아니다. 초기 방향이 Euler singularity 근처라 작은 실제 회전도 box 위반으로 판정되는 구간을 별도 감사했으며, 현재 임계값은 바꾸지 않았다.
- PREPARE49/PLAY251/HOLD0. 최신 영상 끝까지 실제 물리와 연주 제어가 진행됐다. 종료 후 회수나 물리적 평형의 영상으로 설명하지 않는다.
- Native28/28 checks 및1118 입력 SHA 불변, 원본 weights 불변을 확인했다. 최신 두 조건의 추가 독립 검수·봉인은 아직 완료하지 않았다.

## 남은 문제와 다음 방향

직전 current-event 준비 조건에서UP crossing은+25.274ms로±50ms 시간창 안이었으나 목표 lane에서24.123mm 벗어나 원래 위치 허용 반폭12.5mm를 넘었다. Source info의 zone_lane_allowed는 다음 event reset의 tensor alias를 참조해 단일 bool만으로 통과를 판정하면 안 된다. 원본 source를 수정하지 않고 command lane와 실제 crossing 좌표로 실패를 재구성했다.

다음에는 최신 감쇠 조건의 실제 pick 위치·높이·속도와 준비/ENTRY 전환을 분석해 UP 및 줄 변경 접근을 개선한다. 성공 기준을 완화하지 않고 적시 타현과 기타 사용자 범위 유지, 반복 재현성을 함께 확인한다. 작업 목표는 active이며 아직 성공 완료를 선언하지 않았다. 산출물 담당 Luna와 진단 담당의 usage limit가 발생해 최근 두 조건의 문서·감사 일부는 root 정리 및 후속 검수가 남아 있다.

## 실제 영상과 초기값

![최신 준비구간 감쇠 복원 실제 Isaac Gym 전신5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/native/data/images/whole_body.mp4)

![최신 실제 Isaac Gym 손 근접5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/native/data/images/hands.mp4)

![최신5초 끝 전신 실제 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/native/data/images/frames/whole_body/00150.png)

- [최신 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/native/data/initial_values.json) · [최신 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/analysis/summary.json) · [원본 판정/제어](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_staging_damping_v1/native/data/controls.json)
- [검수된 영상 모음266개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v20.md): 최신3조건의 영상은 아직 해당 모음에 추가하지 않았으며 위 run 원본에서 볼 수 있다.
- [주요 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_STAGING_DAMPING_PLAN.md:1) · [최신 PD 조건 코드](/home/ajou/yigyu/3/stability_adapter_2/run_strike_staging_damping.py:178)

기존 stability_adapter/와 원본 공용 모델, 실행된 실험·소스·영상은 보존했다. 본 문서는 완료된 원자료의 현재 정리이며 새 물리실험을 추가하지 않는다.
