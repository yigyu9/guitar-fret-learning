# 고정 LA 두 초기 자세의 source 범위 비교

이 결과는 고정 스트랩 길이 `1.1018469719600776 m`의 두 저장 시작 조건에서, 81개 scalar 관절 좌표의 native limit·source profile·normalized history가 허용하는 교집합까지의 최소 signed 변화를 계산한 CPU 범위 조사다. 실제 자세 보정, geometry prediction, native 재실행은 아니다. 이번 조사 자체의 native 초기화·물리 step·actor 추론·학습 업데이트는 모두 0이다.

![저장 시작각과 공통 유지목표에서 유효 관절 범위까지의 signed 최소 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/fixed_strap_source_range_changes.png)

막대는 `signed_minimum_change_rad`를 degree로 환산한다. 양수는 그 좌표를 증가시켜야 함을, 음수는 감소시켜야 함을 나타낸다. 0선의 hollow marker는 실제 0값이다. 관절명은 독립 scalar coordinate이며 다축 joint나 해부학적 회전량을 뜻하지 않는다.

| 좌표 | held-only 실제 시작각 변경 (rad) | initial-aligned 실제 시작각 변경 (rad) | 두 조건의 공통 유지목표 변경 (rad) |
|---|---:|---:|---:|
| LH:thumb1_x | −0.167204916 | −0.167204916 | −0.094772160 |
| LH:thumb1_y | +0.661268771 | +0.661268771 | +0.617647946 |
| LH:thumb3 | −0.602567554 | −0.602567554 | −0.505324721 |
| LH:index1_x | −0.168908358 | −0.168908358 | −0.204711854 |
| LH:ring1_x | −0.141499698 | −0.141499698 | −0.206355035 |

| 비교 종류 | held-only 범위 밖 | initial-aligned 범위 밖 |
|---|---:|---:|
| 실제 초기각 | 6/81 | 5/81 |
| 초기 PD 목표 | 6/81 | 5/81 |
| 유지 목표 | 5/81 | 5/81 |
| 명령 최솟값 | 5/81 | 5/81 |
| 명령 최댓값 | 5/81 | 5/81 |

남은 5개 좌표는 양쪽 조건 모두 LH:thumb1_x, LH:thumb1_y, LH:thumb3, LH:index1_x, LH:ring1_x다. 새 시작각의 최대 변화는 thumb1_y에서 `+0.661268771 rad` (`+37.887910°`)이다. 그림에는 held-only 실제 시작 middle3의 `−0.08358854055404663 rad` (`−4.789271°`)도 표시되어 있다. 이는 이 저장각의 현재 source-range 경계까지 필요한 scalar 변화다. 다른 LA 조건에서 나온 이전 값을 이 run에 옮겨 쓰지 않았다.

이 수치는 교집합 경계까지의 수학적 signed range distance다. 막대 값을 실제 joint에 적용하지 않았으며 자세 교정량, 접촉 위치, geometry 적합성 또는 동작 결과의 예측이 아니다. 다섯 관절의 큰 엄지 변경을 작은 보정으로 부르지 않는다. Native 관절 범위 안이라는 사실만으로 source profile이나 normalized-history 호환성이 확보되는 것도 아니다.

현재 유지 목표를 입력한 CPU `PlayingTargetBridge` warm-start는 두 조건 모두 거절됐다. 이 warm-start의 range/history 입력 거절과 fret·strike checkpoint의 strict G0 qualification 상태는 서로 다른 검사다. 두 checkpoint 모두 `qualified_for_g0=false`이며, 자격을 추가하거나 loader를 우회하지 않았다. 이 결과는 task-specific fret/strike postprocessing, 연주 기능, 자연스러운 자세나 실제 contact를 인증하지 않는다.

아래는 앞선 `initial_middle3_alignment_v1` 실행의 실제 Isaac Gym t=0 손 프레임이며 재사용 이미지다. 이번 CPU source 범위 조사에서 생성한 새 렌더가 아니다.

![앞선 native 초기 조건의 실제 t=0 손 프레임 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00000.png)

아래 MP4도 앞선 native 실행의 약 5초 기록을 재사용한다. 이번 조사에서 새 물리 실행이나 새 영상 수집은 없었다.

![앞선 native 실행에서 기록한 실제 손 영상, 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/hands.mp4)

후속 후보는 현재 initial-aligned 시작 조건에서 이 다섯 관절의 시작각과 유지 목표를 각각 source/native 교집합 안쪽으로 옮긴 뒤, 새 초기화에서 직접 검사하는 계획이다. 그 후보 설정, fresh native gate와 5초 실험은 아직 실행하지 않았다. [후속 초기 배치 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md:1)을 따른다.

원자료는 [compatibility.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/compatibility.json:1) 34개 검사, [joint_ranges.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl:1) 810개 행, [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/execution.json:1) 48개 입력 해시 전후 동일 기록으로 보존했다. 전체 판단은 [root 결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md:1), 범위와 계약은 [계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_PLAN.md:1), 독립 확인 내용은 [root 검증 노트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/ROOT_VERIFICATION_NOTES.md:1)에서 확인할 수 있다.
