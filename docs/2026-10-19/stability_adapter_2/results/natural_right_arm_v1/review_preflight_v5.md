# 자연 오른팔 V7 제어 조정 사전 검수

요약 판정: **문제없음 — 같은 초기 후보의 재시도에 코드 차단 사항 없음.** Critical 0 / Warning 0 / Suggestion 0. 변경 코드·분석기·후보 SHA·Python 3.8 구문을 확인했다. 새 native 실행·학습은 하지 않았다.

- [계획 V7](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_RIGHT_ARM_REFERENCE_PLAN_V7.md:4)은 V6의 Jacobian 속도 gate 중단을 실패로 구분한다. 제어 강도가 떨림에 기여했을 가능성은 가설이며 원인 확정·수정 성공으로 설명하지 않는다.
- [runner V7](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v7.py:87)의 81차원 posture 배열은 right12에만 Thorax30/1, Shoulder60/3, Elbow40/1, Wrist10/0.35를 지정한다. 실제 joint 이름으로 12개 매핑과 다른69 K/D=0을 대조했다. point K1500/D25/요청 cap30N 및 로그 값도 일치한다. 초기 world motor 목표·목표 속도0·gravity 항·native effort 상한·owner window·POSITION69 읽기/상태 불변 검사·4개 물리 소단계·Jacobian 속도 오차 0.01m/s gate는 유지한다. 기타 pose 고정·직접 기타 힘·strap을 추가하지 않는다. 이탈 플래그는 토크가 계속되는 관측 래치다.
- [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_natural_right_arm_v1.py:24)는 완료된 1200 물리/300 제어만 수락한다. 전완 endpoint 상태를 이용해 점 위치/속도와 고정 world 목표를 재구성하고, 배열 posture·요청 토크·native clip·혼합69 제출을 검사한다. 240Hz 전완/상완/left/Head 접촉을 구분한다. root 이동과 body bbox 중심 이동, 초기 대비 회전과 2→5초 변화도 구분한다.
- 분석기는 저장된 gravity 항으로 합산 토크를 확인하며 전체 gravity/Jacobian 정확성을 독립 인증하지 않는다. 요청 cap30N과 raw 접촉 lambda는 측정 접촉력 N이 아니다. 이 한계는 [출력 scope](/home/ajou/yigyu/3/stability_adapter_2/analyze_natural_right_arm_v1.py:56)에 명시되어 있다. 분석기는 V7 배열 형식과 완료 자료를 대상으로 하며, 실패 V6 자료의 성공 인증용이 아니다. 실제 5초 결과·자세·접촉·자연스러움은 후속 검증 대상이다.

V6 후보의 SHA는 이전 검수와 동일했다. 기존 소스·실패 자료·리뷰는 수정하지 않았다.

검수 SHA256:

- 계획 V7: `8c74f3f3699db80435b360ddf184b0a5dc47189e2399f47d6d1e64d3f1304bd1`
- runner V7: `2c4a7fa5addb4221f242f16fd46be8519882fcb49434b61e01942479fa88236f`
- 분석기 V1: `af237dedb8e4bfba4b17f0ab9b6bafc5f6660d7516c6a7f60247ec57662f26b4`
- 초기 후보: `077ddd78562807651804cc989746ef55ae747d06100f18fcc80e846574a5cc4d`
