# 분산 척추 굽힘·왼손 비지지 초기 조건 사전 검수

요약 판정: **문제없음 — source 후보 생성과 기존 5초 runner 연결의 사전 범위.** 미결 Critical은 없습니다. 실제 왼팔 비접촉과 초기 기타 유지 성공은 native 결과로 확인해야 합니다.

## 확인 사항

- [검색:24](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v1.py:24)의 Torso/Spine/Chest 누적 world orientation 목표는 전체 전경의25%/62.5%/100%이며 몸통9 scalar 초기 변화는 기준±5°와 모델 한계 안에서 풉니다. 9°/12°는 몸통 각 관절에 같은 각도를 반복해서 더하는 방식이 아닙니다. 기존 calibrated FK를 사용하며 실제 척추 모델을 새 곡선으로 변경하지 않습니다.
- [검색:19](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v1.py:19)의 왼손 목표는 원 palm에서 world 위8cm·Pelvis forward 반대 방향3cm입니다. 왼팔±0.6rad/오른팔±0.3rad, 머리·손가락 scalar 초기각 유지, 지지 조건의 원 palm world pose 유지 및 위치2mm/방향1° 미만 수용 조건을 확인했습니다. 기타 초기 p/q는 그대로입니다.
- [검색:21](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v1.py:21)은 이전3° 자세의 왼손 철수, 분산9°의 지지/철수 쌍, 분산12° 철수 후보만 만듭니다. source overlap·관절 한계·몸통 목표/IK 오차를 통과한 후보만 설정을 저장합니다.
- [검색:47](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v1.py:47)은 prep2/horizon5로 기존 관측 분모가3입니다. 기존 frozen runner의 초기 q_ref 고정 목표/단일81 제출/제어당4물리 step과 초기화 state-write guard·원본 strap ON 법칙을 재사용합니다. 전5초 음악 정책·preload·학습·실시간 IK를 실행하는 경로가 아닙니다.
- [계획:7](/home/ajou/yigyu/3/stability_adapter_2/ROUNDED_SPINE_NO_LEFT_PLAN_V1.md:7)은 처음부터 손이 빠진 조건을 시간 중 release 및 strapOFF와 구분합니다. 후기 정착과 초기 유지도 별도 비교하도록 정의했습니다.

## Warning

- [검색:43](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v1.py:43): source_clear와 palm IK 오차는 PhysX cooked 왼손/왼팔 접촉0을 보장하지 않습니다. [계획:16](/home/ajou/yigyu/3/stability_adapter_2/ROUNDED_SPINE_NO_LEFT_PLAN_V1.md:16)대로 native의 모든 L_팔/LH:–기타 접촉을 대조해야 합니다. 시작 시 비접촉이어도 동적 시험 중 다시 접촉하면 ‘전구간 왼손 비지지’로 설명하지 않아야 합니다.
- 같은 수용 행의 gap≥0/지지점 fit<2mm는 실제 source gap≤2mm를 보장하지 않습니다. `gap500` 목표는 요청값이며 실제 signed gap과 cooked/native 접촉을 따로 보고해야 합니다. 기존3° 참조에서 수용한 source gap도 실제 지속 상완 지지의 증거가 아닙니다.

## 검수 SHA·제한

[사전 소스 핀](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/source_before_search_v1.json:1)과 현재 두 파일 SHA를 대조했습니다.

- 계획 SHA256: `9fbb57e4aefce5293439d2a3f5693822daa31d0dee7f1ee51446d3e566f46703`
- 검색 SHA256: `6fe490aaba7a3fe67d5b2c4edbdc9eb913cdd46c9a4f6dd2b1bbaf158b04c880`

이 기록은 source 코드·계획의 읽기 전용 검토이며9°/12° 후보의 실제 native FK·5초 접촉/이동·영상·안전 판정은 포함하지 않습니다. 검수자는 이 새 문서만 작성했으며 추가 실행이나 기존 파일 수정은 하지 않았습니다.
