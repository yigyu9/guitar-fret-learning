# 넥 전면 위치 이동을 허용한 초기각 검색 결과

25좌표(왼팔12·엄지5·검지/중지8)의 초기각 검색3개를 11.432675초/exit0으로 완료했다. 세 후보 모두 source검사에서 제외됐고 새native/physics0이다. 다른56초기각, 기존81PD목표/기타p·q/LA1.1018469719600776m를 유지했다. 실제grip 유지나 초기기타복원을 달성하지 못했다.

| 초기 추정값 | 엄지 오차 mm | 손바닥 오차 mm | 검지 오차 mm | 중지 오차 mm | source 겹침 행 |
|---|---:|---:|---:|---:|---:|
| saved_half | 8.070674 | 13.212180 | 6.472459 | 16.405753 | 3 |
| previous_near | 5.753987 | 6.705212 | 6.469098 | 16.851927 | 1 |
| linear12x25 | 8.867046 | 4.322111 | 5.143676 | 15.479188 | 5 |

![여섯 source후보의 대표점 목표 오차 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifacts/six_source_candidates.png)

이 그림은 CPU 원본형상/FK의 정적 검사이며 Isaac Gym 렌더나 기타이동·회전 경과가 아니다. 겹침은 전체human–guitar의source LP 교차 기록이고 공통반경을 PhysX 침투 깊이로 해석하지 않는다. 두 batch의 near/linear 초기 추정값은 서로 다르므로 단일 항의 인과효과 비교가 아니다. 같은 half 초기 추정값에서는 XY 이동 허용 후 엄지/손바닥오차가6.192352/11.664586에서8.070674/13.212180mm로 커졌다. XY 목표만이 실패 원인이었다고 결론짓지 않는다.

![sliding previous_near의 source지점·목표를 기타G좌표의 GY–GZ로 투영](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifacts/source_points_Gyz.png)

이 조건은 thumb/palm 오차 중 큰 값을 최소로 한 sliding 후보이며 여전히 거절됐다. 엄지5.753987mm/손바닥6.705212mm이고 middle3–fret4 source교차가 남는다. 점은 선택source facet 지점이며 전체 손가락 형상이나 actual contact feature가 아니다. GY–GZ 그림만으로 옆면접촉/관통을 판단하지 않는다.

root 사전검증12개와 저장pose의 재계산13개가 통과했다. 각batch의thumb/palm거리witness6개를 독립적으로 재구성하고 전체human–guitar LP교차/25좌표bounds/다른56초기각/81목표/전면지점오차를 대조했다. 검증은source범위이며cooked/물리접촉 인증이 아니다.

[원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/proposal.json), [초기 추정값/선형계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/initial_guesses.json), [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/search_execution.json), [자체 결과 재계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/interval_data_verification.json), [그림 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifact_execution.json), [그림 입력·출력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifacts/artifact_manifest.json)를 보존했다. 그림2개는6.707739초/exit0으로 생성해 root가 실제PNG를 확인했다. 이번후보용 실제5초영상은 source에서모두제외돼 없다.

독립검수 및Luna 위임을 사용할 수 없어 root가 구현·실행·산출물과 자체검증을 수행했다. change-reviewer호출의 agent thread limit 오류를 [범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/review_status.json)에 남겼으며 독립 최종 검수를 완료로 표시하지 않는다. 기존near/source그림의 독립 최종 검수도 보류 상태를 그대로 보존했다.

다음 [왼손 전체 초기각 탐색 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_WIDER_HAND_INITIAL_PLAN.md:1)은 약지·소지까지 포함하고 팔 초기 범위를 ±0.15rad로 확대한다. 아직 미실행이며 최종양팔·양손66 제어권/몸통9목표/root하체 물리고정/자유기타·수동strap 조건을 유지한다.

root의 44개 실행·입력·원자료·그림·이전보존 검사를 통과했다. [최종root검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/final_verification.json)이며 독립 최종 승인은 보류다.
