# 바디 쪽4° 근접 초기 후보 V5 사전 검수

요약 판정: **문제없음 — 한 후보의 제한된 native 근접 진단에 코드 차단 없음.** Critical 0 / Warning 1 / Suggestion 0. 새 계획·준비 코드·실행 diff와 저장 후보를 검토했다. 새 물리 실행·학습은 하지 않았다.

[계획 V5](/home/ajou/yigyu/3/stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V5.md:5)는3mm가 실제 접촉/안전성 문턱이 아니었음을 명시하고, 근위 문턱만5mm로 바꾸어 **native 진단용**으로 수락한다. [준비 코드](/home/ajou/yigyu/3/stability_adapter_2/prepare_body_side_lean_axilla_v5.py:11)는 전체 source clear·최소capsule0.05mm·R_Hip0.05~3mm·normalZ·팔 방향·손 위치·설계 box·other72 조건을 유지한다. 최종 유지 초기값 채택이나 cooked 무관통 인증이 아니다.

V5의 초기81 q·기타 p/q는 V4 원해를 직접 재구성해 비교한 값과 exact였다. 다른72는 raw right4 seed와 exact이며 body/head/Wrist/left/fingers를 보존한다. contract q_ref도 후보와 exact, native 모델 한계를 통과한다. G delta는 world[−32.779, +10.632, +21.925]mm로 선언 범위 안이다. row 변경은 `accepted_for_native`와 `adoption_scope`뿐이며 원래 V4 거절 자료를 수정하지 않는다. 입력598개 현재 SHA 불일치0개를 확인했다.

근위 gap4.313937mm, 전체 capsule 최소0.123462mm, R_Hip1.782223mm, normal world Z0.999734, 손 위치30.483mm와 팔 방향이 새 진단 gate를 통과한다. 기타 회전은 기준과 동일하다. source 근접은 실제 상완 접촉·힘 기여·안정화·팔 자연스러움을 보장하지 않으며 실제 이미지·접촉·이동으로 별도 판단해야 한다.

[runner V4](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v4.py:116)는 V3 대비 PLAN/search 경로만 변경한다. 전완 초기-world human motor 목표·관절별 gain·모델 토크 cap·owner window·혼합69 POSITION/12 EFFORT·상태 불변/Jacobian 가드가 유지된다. 기타 고정·직접 기타 힘·부착·runtime pose 덮어쓰기를 추가하지 않는다. 이탈 래치는 관측값으로 토크가 계속된다. 새 후보의 native 완료/품질은 아직 인증하지 않는다. Python3.8 구문은 정상이다.

## Warning

1. [BODY_SIDE_LEAN_AXILLA_PLAN_V5.md:3](/home/ajou/yigyu/3/stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V5.md:3): ‘두Hip및상완전체가약.1mm’는 raw와 다르다. L_Hip0.131361mm·R_Hip1.782223mm·상완전체0.123462mm로 구분해야 한다. 소비 계획은 보존하고 후속 정정 설명/최종 결과에 실제값을 사용해야 한다. 코드의 R_Hip<3mm gate 통과나 실행 가능성에는 영향이 없다.

검수 SHA256:

- 계획 V5: `ace35570f9e5f2c995f2e9947ae900984189df578fefb255d8d9e221d82f6a76`
- 준비 V5: `c34f107ebc6b20bfe47817f12d1acdac75ba630d1bffb5ac34f05c07d215f8a7`
- runner V4: `513be05c253cba255383aeab5ddb768749696d347c2f877f7ee6b8dbca838253`
- search V5: `c8a1744b71eff530455f77b24bf206008c5461bc34d23e8e4b82841ce3823b03`
- candidate: `0743ef3b743d8eeb90585d5858ae77286ce53713a942f5ffb3bbc847a3990b81`

이 새 리뷰 외 원본·기존 결과·이전 리뷰는 수정하지 않았다.
