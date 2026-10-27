# Lower-body native damping-zero comparison v1

작성일: 2026-10-06. 상체 native gain/target 66개와 몸통 gain/target 9개, 초기 전신 각도/root, 기타 목표, 절대 strap rest length는 기준 H0와 동일하게 유지하고 하체 native damping을 0으로 둔 두 조건을 비교했다. 두 조건 모두 0.1초 실제 H0 CPU PhysX 실행이며 main baseline 설정은 바꾸지 않았다. 기타 Z +5 mm는 아직 적용하지 않았다.

| Condition | Solver | Max guitar position error (mm) | Max guitar rotation error (°) | Max raw leg target deviation (°) | Max native scalar-limit violation (°) |
|---|---|---:|---:|---:|---:|
| `leg_kd0` | TGS 4/2 | 182.725 | 18.948 | 92.622 | 92.622 |
| `pgs_leg_kd0` | PGS 4/2 | 19.908 | 3.551 | 99.455 | 55.292 |

![TGS 4/2와 PGS 4/2의 하체 damping-zero 진단 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/images/lower_kd0_v1_comparison.png)

두 조건은 모두 안정 자세 기준에서 실패했다. PGS 4/2에서 기타 오차는 작아졌지만 하체 raw 목표편차는 99.455°이고 native scalar-limit 위반은 55.292°다. 그러므로 `damping=0`이 문제를 해결했다고 볼 수 없으며 오히려 큰 하체 목표 편차가 남았다. 이 두 trial에서 안정 성공이나 후보 채택을 주장하지 않는다.

이 독립 진단 단위는 여기서 마친다. 다음 유의미한 actual 비교는 기타 Z 오프셋이지만, +5 mm는 아직 적용 승인이 대기 중이고 이번 실행에도 반영되지 않았다.

원자료는 [비교 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/comparison.json), [TGS run report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/leg_kd0/report.json), [PGS run report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/pgs_leg_kd0/report.json)에 있다. 그림은 원자료 비교값을 기존 `plot_lower_body_pd.py`로 그린 것이며 native renderer 출력이 아니다. 별도 검수에서 두 native run과 그림을 독립 재현했으며 남은 Critical/Warning/Suggestion 없음이다. [검수 기록](review.md).
