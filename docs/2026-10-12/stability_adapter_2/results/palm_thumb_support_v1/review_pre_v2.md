# 손바닥·엄지 지지 v2 — 실행 전 독립 검수

요약 판정: **문제없음**. 신규5개 파일과 leaf 계획의 정적 검수 범위에서 Critical/Warning/Suggestion은 없다. 검수자는 source/native trial을 실행하지 않았다. v1 계획·소스·실패 실행·검수 기록을 수정하지 않았다.

## 검수 대상

- [PALM_THUMB_SUPPORT_V2_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_SUPPORT_V2_PLAN.md:1)
- [palm_thumb_support_search_v2.py:47](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_search_v2.py:47)
- [run_palm_thumb_support_v2.py:21](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v2.py:21)
- [palm_thumb_support_preserved_v2.py:48](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_preserved_v2.py:48)
- [run_palm_thumb_support_v2.sh:1](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v2.sh:1)

## 확인 사항

- source 탐색은 왼팔12+왼손21의33관절만 변경한다. 다른16손가락은 각 trial 폭과0.18rad 중 작은 값을 사용하고 엄지5/왼팔12는 최대0.3rad, 모두 native joint limit과 교집합이다. closest witness를 기타 frame 목표와 손 부위 local 점으로 변환한다.
- 겹침 LP는 단위 plane normal을 유지하고 교집합 AABB 중심 주변에서 거리·radius를 mm로 계산한다. 양의 radius만 관통 벌점에 사용한다(81–86). 최종 후보는 별도의 `intersection()`으로 다시 검사한다(97–100). source 결과는 native 접촉 인증으로 설명하지 않는다.
- 동적 runner의 제어는 v1 최종 소스와 같다. ON 왼팔 hold PI는 비활성화하고 접촉점 잔차 적분 하나만 사용한다. 엄지5/왼팔12의 단일 제출 목표와 native limit·목표 속도·palm-up·고정 root/하체·다른 목표 유지 검사는 보존된다.
- journal은 초기 상태와 각 완료 제어tick의 제출 목표·4개240Hz접촉 표본·native 상태를 flush한다(58,97). 카메라/API crash 중 미완료tick은 journal에 없을 수 있으며, 계획이 그 한계를 명시한다. 정상 완료는1200step·151frame이다.
- wrapper는 직접 subprocess child를 실행하므로 child의 SIGSEGV가 Python finally를 우회하지 않는다. 실제 child returncode와 입력 SHA 사후 대조를 남긴다(56–65). 입력 보존과 물리/영상 정상 완료는 별도다.
- 재사용 controller의 수치 검증 producer [test_palm_thumb_support_v1.py:24](/home/ajou/yigyu/3/stability_adapter_2/test_palm_thumb_support_v1.py:24)의10조건을 읽었다. 이는 저장 native 상태를 이용한 FK/목표 한계·속도/좌표변환/anti-windup 확인이며 새 native 접촉 효과의 검증은 아니다. 실행 결과는 root 기록으로 별도 대조한다.

## 실행 범위와 한계

이번 단계는 source 탐색과 checkpoint 없는5초 settle 비교다. Fret 모듈은 아직 후속 단계이며 wrapper의 `--mode fret`을 실행 가능한 완성 기능으로 설명하지 않는다. source search의 `--native`는 `initial_angles_rad`와 초기 audit가 있는 기존 입력을 사용한다. 새 settle의 `actual_initial_angles_rad` 필드와 서로 바꾸지 않는다.

v1 카메라 실패 및 새 버전의 효과·실제 보존 결과는 최종 원자료 검수에서 대조한다. 정적 검수 통과는 자유 기타 지지 성공 판정이 아니다.
