# 앞면 clamp source·코드 사전 검수

판정: **문제없음(거절 처리 정상)**. Critical 0 / Warning 1 / Suggestion 0. **source 후보가 거절됐으므로 현재 native 진행 후보는 없다.** v14 실행 코드·search v7·V15 계획과 완료된 source 결과만 검토했다. 추가 native 실행·학습·다른 파일 수정은 하지 않았다.

- [source gate:20](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v7.py:20): 전체 source clear·모든 capsule 양수 간격·상완10~100µm 간격·world normal +Y>0.85를 함께 요구한다. [결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v7/search.json)는 `selected=[]`, `accepted_for_native=false`, `native_runs=0`이다. candidate/config 디렉터리도 생성되지 않았다.
- [audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v7/audit.json): full R_Shoulder gap은 **−21.806805mm**, R_Shoulder–G:body source overlap7개이며 `source_clear=false`다. world normal은 [−0.155118,0.912345,0.378901]로 방향 조건은 통과했다. 저장 기타 회전으로 normal을 재계산해 일치를 확인했다. 음수 source gap은 source 교차 지표이며 native cooked 관통 깊이를 측정한 값은 아니다.
- [변경 범위:15](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v7.py:15): 오른12만 ±.6rad∩모델 한계에서 최적화하고 다른69와 G 초기 p/회전은 코드상 유지한다. 결과에 다른69 불변과 오른 초기 최대 변화 .585119rad가 기록돼 있다. 거절된 q 전체가 candidate로 저장되지 않아 새 candidate의 독립 상태/계약 비교는 수행할 수 없는 범위다.
- [실행 제어:95](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v14.py:95): 현재 G 상대 희망점8mm·요청cap40N으로 변경했고 상대 속도 감쇠·gravity/posture·native effort cap은 유지한다. guard·construction·혼합 모드 step/factory·Head callback은 v13과 AST가 동일하다. 오른팔 human effort 외 권한, 다른69 POSITION/rootlower·strapOFF/freeG 조건을 바꾸는 코드가 아니다. 기본 초기 계획과 현재 초기 계획 metadata도 분리했다.

Warning 1 — [source 최적화:19](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v7.py:19): 이번 결과는 이 초기값·범위·목적함수로 얻은 후보의 거절이다. 앞면 clamp 자세가 모든 조건에서 불가능하다는 증명이 아니다. 거절 후보를 실행하거나 source 방향 통과만으로 지지 가능성을 인정하지 말아야 한다.

source 입력553개 SHA가 현재 파일과 일치한다. 검수 시점 핵심 SHA-256은 다음과 같다.

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v14.py | 9bd1123f969e696a81d505369f12a3c9a5e6507e0d01c3e36b21f8512e46fa11 |
| search_om_no_strap_upper_arm_v7.py | bf5a0073dd57c392c3cc5573947881e7a59e7f9a08aa8843dd09b4050f1c30b1 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V15.md | a242e68236a55bf27d77c6a5820d48fe6f2d2e9898acebedb4a413d9250eb271 |
| search_v7/search.json | 24628abcb176a6ba720e93a60cc0154412dded23c998a0329a76cb2deb82e33a |
| search_v7/audit.json | f89c04a56e6c48f509519409069e86f6698764645f988495cc12cf1686c7832f |

현재 코드에서 추가 실행 차단 버그는 발견하지 않았지만 **source 수락 gate가 실행을 막는다**. source 충돌 전체 재계산·새 native 물리·접촉/힘 기여·기타 유지 성공은 이번 검수 범위가 아니다. 지정한 새 리뷰 파일만 작성했다.
