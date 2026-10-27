# 엄지2 단일축 source 간극 검사 — 7개 표본 모두 겹침 유지

저장된 scalar source 결과의 일곱 점만 그린 정적 도표다. 점은 `actual_delta_rad`에 대응하는 `LH:thumb2`–기타 source LP 공통 내접 반경이며, 실제 Gym 움직임이나 PhysX 접촉/관통 깊이가 아니다. 부호 있는 각도 변화와 초기각은 다음과 같다.

| 요청 변화 (rad) | 실제 변화 (rad) | 초기 thumb2 q (rad) | thumb2–기타 공통 내접반경 (mm) | thumb3 후면 witness 거리 상한 (mm) | source clear |
|---:|---:|---:|---:|---:|:---:|
| −0.20 | −0.200000003 | 0.138412789 | 3.054824 | 8.436476 | 아니오 |
| −0.10 | −0.099999994 | 0.238412797 | 3.679258 | 9.053841 | 아니오 |
| −0.05 | −0.050000012 | 0.288412780 | 3.984986 | 9.221647 | 아니오 |
| 0.00 | 0.000000000 | 0.338412791 | 4.288365 | 9.294899 | 아니오 |
| +0.05 | +0.050000012 | 0.388412803 | 4.590763 | 9.252235 | 아니오 |
| +0.10 | +0.099999994 | 0.438412786 | 4.893355 | 9.053857 | 아니오 |
| +0.20 | +0.200000018 | 0.538412809 | 5.500940 | 8.375426 | 아니오 |

`thumb3` 열은 후면 patch까지의 source convex witness 거리 상한이다. 하한/상한은 대략 8.375–9.295 mm 범위지만, 이 값은 실제 접촉이나 지지를 인증하지 않는다. 손바닥 up proxy는 모든 조건에서 0.956547이고 cross-hand 및 1,188개 self-pair 검사는 모두 clear다. 8개 저장 검사는 통과했으며 선택된 후보는 없다.

![일곱 thumb2 source 오프셋과 공통 내접반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/artifacts/thumb2_source_radius_sweep.png)

0과 ±0.2 rad를 포함해 검사한 모든 표본에서 thumb2–기타 교집합이 남았다. −0.2 rad에서 반경은 기준 4.288365 mm보다 작아진 3.054824 mm지만 겹침은 해소되지 않았다. 이 일곱 점의 ±0.2 rad 범위가 thumb2 전체 가동범위에서 해결 불가능하다는 증명은 아니다. 새 native 초기화·물리 단계·actor 추론·학습은 0회이며 5초 안정성은 측정하지 않았다.

![직전 phase의 실제 Gym t=0 손 장면 재사용 — 이번 검색의 새 Gym 렌더가 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

이 프레임은 직전 실제 초기화의 장면을 설명하기 위해 재사용했다. 이번 일곱 source 조건의 native 렌더나 통과 후보 장면이 아니다.

이전 v1 source 실행은 `other_pose_identity` 검사에서 멈췄다. thumb_pad는 thumb2의 자식 pose로 따라가지만 충돌 geometry 검사 대상은 thumb2와 thumb3이며 pad는 제외된다. v1 오류, 로그, 입력 사본은 보존했고 v2는 XML의 네 자식 pose(thumb2, thumb3, thumb_pad, thumb_top)를 검사해 정정했다. v1 결과를 7개 검증 결과로 섞지 않는다. 아래 v2 입력 closure의 68개 SHA가 실행 전후 동일하다.

다음으로 계획된 [thumb1 기저부 source/native 검사](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md:1)는 thumb1_x −0.05, thumb1_y +0.05, thumb1_x −0.10, thumb1_y +0.10 rad의 한 축 네 초기값을 순서대로 확인한다. Finger1 다축 FK를 근거로 통과를 예측하지 않고, source 범위 검산 뒤 fresh native gate가 첫 통과하면 같은 초기화에서 5초를 기록할 계획이다. 이 후속 단계는 아직 실행하지 않았다.

[저장 검색 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/search.json:1) · [검색 실행과 68 입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/search_execution.json:1) · [v1 실패 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v1/search.log:1) · [v1 종료/입력 해시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v1/search_execution.json:1).
