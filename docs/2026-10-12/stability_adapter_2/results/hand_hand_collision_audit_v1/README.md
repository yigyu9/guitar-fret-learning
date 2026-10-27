# 왼손·오른손 형상 교차 감사

**네. 저장된 일부 자세에서 왼손과 오른손 source convex hull이 실제로 교차합니다.** 독립 hull 검증은 다섯 시점 중 0.5초, 0.670833초, 1.0초에서 교차를 확인했습니다. 다만 이는 source convex hull 교차 판정이며 PhysX cooked shape의 관통 깊이나 접촉 힘을 뜻하지 않습니다.

## 검증된 저장 시점

왼손 17개와 오른손 17개 shape의 289쌍을 시점별로 검사했습니다. 독립 검증기는 양쪽 convex-hull halfspace 안에 공통 내접구를 찾는 LP를 사용했습니다. 반지름이 양수인 공통 내부구는 해당 convex hull들이 교차한다는 증거입니다.

| 저장 step | 시간 | LP로 확인된 교차 shape 쌍 수 |
|---:|---:|---:|
| 0 | 0 s | 0 |
| 14 | 0.058333 s | 0 |
| 120 | 0.5 s | 18 |
| 161 | 0.670833 s | 15 |
| 240 | 1.0 s | 18 |

예를 들어 step 161의 `LH:pinky3`–`RH:palm` 쌍은 공통 내부구 반지름 6.642477 mm로 확인됐다. 이 반지름은 두 convex hull의 겹친 내부에 들어가는 구의 크기이지 관통 깊이가 아니다.

기존 0.1 m signed-gap 조회는 241개 상태 중 227개에서 음수였고 첫 음수는 step 14의 −0.193690 mm다. 이 조회는 cutoff 영향이 있을 수 있다. 같은 step 14의 독립 hull 검증 결과는 교차 0쌍이므로, 첫 음수 시점을 실제 교차 시작 시각으로 취급할 수 없다. 교차 onset은 이 다섯 시점만으로 확정되지 않았다.

## Native contact 기록과 의미

전체 1초의 완료 240 step contact 기록에서 왼손·오른손 사이 contact 행은 0이다. 동시에 감사 보고서는 모든 왼손–오른손 shape 쌍이 공통 collision-exclusion bit를 공유함을 확인했다. 즉 이 쌍들은 native 충돌 처리에서 제외되며, contact 행 0은 저장 source convex hull 교차와 모순되지 않는다. contact 행은 직접 측정한 반력이나 접촉 힘이 아니다.

## 그림과 한계

아래 그림은 0.5초 저장 자세의 기존 source-geometry 재생 프레임이다. 초록색 왼손과 자홍색 오른손은 저장된 pose에서 가깝게 겹쳐 보인다. 이 프레임은 PhysX renderer가 아니며, cooked collision shape·관통 깊이·힘을 시각화하지 않는다.

![0.5초 저장 pose source-geometry 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png)

감사는 native 초기화 1회와 명시적 physics step 0회로 수행됐다. 별도 hull LP 검증은 native 초기화·physics step 모두 0회다. 주 시뮬레이션, 설정, 원자료는 변경하지 않았다. 검증 대상은 다섯 저장 시점뿐이며 source convex hull 및 capsule 다각형 근사에는 원본 비볼록 mesh나 PhysX cooked shape의 정확한 접촉 판정이 포함되지 않는다.

원 signed query 및 native filter 기록은 [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/report.json), 표본별 hull 교차 결과는 [hull_frames.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hull_frames.json), 독립 검증·한계는 [hull_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hull_verification.json)에 있다. 최종 검증 로그는 [hulls_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hulls_execution.log)에 있으며 75개 입력 hash를 실행 전후 확인했다. 첫 전체 scan 시도 기록은 `interrupted_full_hull_scan/`에 보존했다. 검사 계획은 [HAND_HAND_COLLISION_AUDIT.md](/home/ajou/yigyu/3/stability_adapter_2/HAND_HAND_COLLISION_AUDIT.md)에 있다. [최종 독립 검수](review.md:7)는 완료했고 남은 finding이 없다.
