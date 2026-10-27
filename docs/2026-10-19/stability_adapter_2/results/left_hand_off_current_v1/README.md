# 왼손 없이 현재 기타 자세가 유지되는가

**이번 조건에서는 유지되지 않았다.** 실제 Isaac Gym에서 왼손·왼팔이 기타에 닿지 않도록 시작했고, 약0.93초에 기타 이동/회전 안전한계로 중단했다.

| 검사항목 | 실제 결과 |
|---|---|
| 왼팔·손 전체 기타접촉 | 0/224 물리step |
| 왼손목 추종 / 가상힘 / task | 모두0, 처음부터OFF |
| 물리 실행 | 0.933333초, 224step·56control |
| 기타 바디 BB중심 변화 | 최대/종료77.452mm |
| 기타 SO3회전 변화 | 최대/종료35.625° |
| 기타 actorroot 변화 | 최대/종료208.335mm |
| 오른 상완 기타접촉 | 185step, 마지막0.7875초 |
| 오른 허벅지 기타접촉 | 222step, 종료까지 |
| 동일시각 왼손있는 기준과 BB차이 | 최대/종료55.547mm |

기타 초기p/q와 오른팔·몸통 초기 배치 및 제어 설정은 유지했다. 왼12각만 변경하고69각과G39 초기state 동일을 검증했다. PD·중력보상·오른쪽 현재기타기준 보정은 계속 작동한다. 스트랩·기타 고정·손 부착·기타에 직접 힘이나 pose쓰기·체크포인트·학습은 없다. t=0부터 왼손이 분리된 시험이며, 기존 상태에서 손을 빼는 동작을 실행한 시험은 아니다. 바디중심 이동과 actorroot 이동을 혼동하지 않는다. 부분 영상을5초로 늘리지 않았다.

상완의 접촉이 먼저 끊어져 회전지지가 부족해진 것으로 보인다. 초기 왼팔의 질량 배치 변화도 포함되어 있어 왼손접촉만의 인과효과로 단정하지 않는다. 실제5초 유지 검증은 실패했으며 2→5초·후기4.5→5초 수치도 없다.

CPUsource6후보 중2수락/4제외, 실제native1회. V1/V2 실패원본을 보존하고 V3 search_v3/back100mm만 사용했다. 소비PLAN_V3에 남은V2 제목/경로는 수정하지 않고 여기서 실제경로를 구분한다. 향후 오른 상완·허벅지 접촉 위치를 조정하는 별도 실험으로 이어갈 수 있다.

[구현·한계](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_COMPLETION_V1.md:1) · [접촉/명령 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/left_off_analysis_v1.json) · [실제 경과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/timelines_v1.json) · [동일시각 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/same_time_v1.json)

이미지·영상 색인은 artifacts_v1/README.md와 video/left_hand_off_current_v1/INDEX.md에 추가한다. 독립 검수 및 보존 봉인 경로는 후속 검증 뒤 확정한다.

[확정 이미지·설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/README_V3.md:1) · [확정 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_hand_off_current_v1/INDEX_V3.md:1) · [표시자료 이력의 제한](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/ARTIFACT_HISTORY_LIMITATION_V1.md:1)
