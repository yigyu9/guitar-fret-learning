# 오른 허벅지 waist native 코드 사전 검수

판정: **검토한 실행 코드에 Critical 없음. 후보·정확한 config 확인 전 native 실행 판정은 보류.** Critical 0건, Warning 2건, Suggestion 0건. source1/2가 모두 거절됐으므로 이 기록은 해당 후보의 실행을 승인하지 않는다.

기존 run_right_block_cradle_v9와 새 runner1/2 diff를 확인했다. baseline은 B/native_elbow5_close 초기 자료이며, 새 candidate의 전체 predicted guitar body pose 배열 길이와 위치<3µm·회전<1e−5rad, 기존 root G회전<1e−6rad 보존을 [초기 gate](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v2.py:52)에서 검사한다. 사용자 요청에 따라 기타 초기 위치만 원래 위치 exact 조건에서 제외하고 실제 delta를 기록한다. root/하체·finger42·q_ref/model·현재 PD/질량 검사는 유지된다.

[runner2:33](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v2.py:33)은 실제 human mesh37개를 포함한다. 생성 전 attempt SHA, 초기 실제 source LP/state 보존, 단일 제어/4 physics·33 EFFORT/48 POSITION·body150/1·Thorax40/16mm/Shoulder10/4mm·왼 wrist 추적 및 기존 finite/model/속도/기타 변위 가드는 로직 변경이 없다. 추가 runtime 상태 쓰기·기타 힘·checkpoint/학습 연결은 없다. 첫 카메라 capture와 부분 실패 자료 보존 경로도 기존과 같다. 두 새 Python 파일 AST 검사를 통과했다.

[analyzer1:25](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:25)의 좌표식 `Groot_R^-1*(Gbody_p+Gbody_R*localPos−Groot_p)`는 실제 body-origin local 접촉점을 G frame으로 옮기는 식이다. right_hip_body_contacts의 G:body 쪽 localPos0/1을 선택하고 양수 Gx·후보 waist Y 구간과 raw λ 양수를 분리한다. 기존 support analyzer7의 명령 검증과 결합하며 waist 부재도 저장한다.

## Warning

- [runner2:57](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v2.py:57): `guitar` 이름의 boolean은 pose 허용오차 검사이며 전체 JSON 상태 exact가 아니다. 기타 속도0를 독립적으로 검사하는 boolean은 추가되지 않았다. 실제 초기 상태와 FK 오차·guitar delta를 보존하고, 실제로 확인된 pose/상태 범위를 구분한다. 새 후보·SHA·config 및 initial gate 통과는 결과 준비 후 확인해야 한다.
- [analyzer1:29](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:29), [같은 파일:37](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:37): 양수 Gx/Y 구간은 source proxy에 따른 접촉 위치 분류다. `passed=True`는 명령·자료 감사이며 waist 걸침 유지 성공이 아니다. raw λ는 N·지지 분담이 아니고 240Hz endpoint는 연속시간 접촉 인증이 아니다. 실제 기타 변위·접촉 지속·왼손/기존 상완 기여와 성공/실패를 별도로 판단한다.

검수 SHA-256: run_right_thigh_waist_v2.py `416a642eac68d14e3ebe2e162a9417f45b01cc7a2e6c10988cf16e234dc0b87e`, analyze_right_thigh_waist_v1.py `bf19142a757641c22b099c7cadf1b87b50f78945f183489ade7f28802ac52569`.

후보가 미확정인 코드 준비 검수다. 새 native·source 탐색·정책 추론/학습을 실행하거나 다른 소스·원자료·기존 리뷰를 수정하지 않았다. 최종 보존 감사도 수행하지 않았다.
