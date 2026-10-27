# 연속 연주 연결 작업 현황

목표는 기타가 사용자 허용 자세를 유지하는 가운데 실제 Strike 또는 Fret를 수행하는 것이다. **아직 지속 연주 성공은 확인되지 않았다.** 단일 타현이나 준비 성공은 완료로 판정하지 않는다. 기타 자유·스트랩 없음·root/하체 고정·몸통 PD 유지 조건이다. 기타/손 고정이나 계속되는 상태 덮어쓰기는 없다.

| 5초 조건 | 적시 타현 | 기타 최대 회전 변화 | PLAY 허용 범위 표본 | 판정 |
|---|---:|---:|---:|---|
| timed-wait rebase / POSITION policy+PI | 1 | 7.095° | 164/178 | 첫 회복 성공, 후속 실패/종료. 비교 기준으로 보존 |
| damped-arm / EFFORT policy+PI | 0 | 46.354° | 3/251 | 미채택 |
| geometry PI / EFFORT actual+PI | 1 | 44.868° | 3/251 | 미채택 |
| geometry PI / POSITION actual+PI | 0 | 45.021° | 45/251 | 미채택 |

기타 회전 변화는 각 실행의 초기 quaternion과의 회전 거리이다. 표본 비율은 저장 control 자료의 수치이며 연속 시간 전체를 인증하지 않는다. Strike checkpoint는 strike_010000.pt를 동결해 사용했고 현재 학습 update는 0이다. 물리 CPU 환경과 학습 당시 구동 방식의 동등성은 아직 인증하지 않았다.

현재 다음 단계는 기존 POSITION policy+PI 기준에서 현재 기타 기준 손 방향을 약하게 유지하는 IK residual 한 요인을 비교하는 것이다. 위치·방향·관절규제를 공동 soft cost로 계산하고 native/rate bounds는 hard 유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md:1), [구현](/home/ajou/yigyu/3/stability_adapter_2/run_strike_soft_orientation.py:177).

각 실행에는 초기값, source/입력 SHA, 원자료, 0·2·5초 전신/손 이미지, 5초 전신/손 영상이 있다. 문서 링크:

- [비교 기준 및 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/README.md:1)
- [EFFORT policy+PI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/README.md:1)
- [EFFORT actual+PI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/README.md:1)
- [POSITION actual+PI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/README.md:1)

이 현황은 위 네 조건 완료 시점의 기록이다. 실시간 실행 상태는 [CONTINUOUS_WORK_STATUS.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/CONTINUOUS_WORK_STATUS.json)에 기록한다. 변경 전 main PLAN/README와 실행 당시 A 소스는 각 phase/main_before_progress 및 native/source_before에 보존했다.

## 추가 경과: 네 손가락 보정 및 READY 제어 분리

중지·약지 두 마디씩 source 목표+.2rad를 추가한5초는 적시타현0/물리타현1(목표보다226.674ms일찍)/기타최대회전9.230°였다. source는3.4초에 잘못된타현으로 종료했지만HOLD물리·영상은5초까지계속했다. native카메라151프레임과 상태trace152행(3.4초terminal전환추가1행)을 구분한다. 음악성공으로 채택하지 않는다. 결과·영상: [free4 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/README.md).

다음 비교는 같은 손가락조건에서 READY 및닫힌APPROACH를 이전팔목표+2δ로통일하고 열린APPROACH에서만 체크포인트policy+PI를사용한다. 원본타현시간/성공판정/기타허용범위·RECOVER경로는 유지한다. 현재5초native실행중이며 완료/성공판정은 report와검수로별도확인한다. [설계와실제변경줄](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:187).

저장자료 native속도좌표 및기타몸체·손형상감사는 독립검수와root봉인을완료했다. 추가물리0회이며 force좌표등가/cooked충돌형상/제어성공인증은 아니다.


## 최신 연속 비교: 적시 타현 4회와 5초 연주 제어 유지

- Terminal retraction: 적시4/회복4, 3.633333초 source wrong4 종료 뒤 오른손 회수. 기타 최대7.095°/끝2.720°. 원자료·문서·독립 검수·보존 봉인706 완료.
- Lateral staging: 적시4/physical5(마지막 약612ms 조기)/회복5/wrong2/miss6. PREP49·PLAY251·HOLD0, 5초 끝까지 source PLAY. 기타 최대7.095°/끝4.355°, 위치최대46.354mm/끝33.298mm. 기존202 commoncontrols/102 native prefix exact, 251 geometry/125 native anchors·300 최종목표 검증. 문서/최종 검수 진행 중. 완주/학습 성공이 아니다.
- 다음 비교: 준비 xy≤4mm 도달을 한 번 기억해 READY↔ENTRY 반복 전환을 줄인다. 신규 계획은 /home/ajou/yigyu/3/stability_adapter_2/STRIKE_LATERAL_LATCH_PLAN.md, 사전 검수 중이며 실제효과 미검증.

[영상 목록 v19](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v19.md)에는 완료 영상266개가 모여 있다. 직후 생성된 lateral staging 영상은 후속 수집 대상이다.

![실제 Isaac Gym 5초 lateral staging 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/whole_body.mp4)
