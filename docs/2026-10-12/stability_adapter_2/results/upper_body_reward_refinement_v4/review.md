# 보상 정리 v4 독립 검수

요약 판정: **문제없음 — 설계·합성 산술·설명 산출물 범위**. 최종 원문, 검사기와 두 JSON, 수정된 README/PNG, 변경 색인과 네 main 문서의 추가 기록을 대조했다. 실제 detector·물리·학습 구현의 승인이나 성능 인증은 아니다.

## 발견 사항

- Critical: 없음.
- Warning: 없음. 음악 예산과 종료 처리에서 앞서 지적한 사항은 아래 계약에 반영됐다.
- Suggestion: 없음. 설명의 실패 상한/정음 하한 및 단일 event 조건 표기는 정정 완료됐다.

## 확인 근거

- [설계 32–42행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:32): 원래 음악 event·required target·고정 시간표/분모를 사용한다. REST/idle은 음악 점수와 event 수에서 제외하고 timeline은 유지하며, 개방현은 평가한다. source 총 reward의 중복 합산이 없다.
- [설계 50–62행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:50): 양손 음악 상태는 인정 crossing 시점의 sounding fret·실제 누름·dwell로 정의한다. 뒤늦은 수정으로 잘못된 onset을 성공으로 바꾸지 않는다. 유지의 현별 고정 시간 분모·최솟값 누적, 필요한 해제와 무해한 추가 압현의 구분, 원본 finger 지표 보존을 명시한다.
- [설계 66–79행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:66): 인정 hit는 required target 수로 정규화하고 기본 −2는 deadline에 한 번 정산한다. 고유 wrong crossing은 서로 다른 crossing마다 세며 동일 crossing을 중복 벌하지 않는다. 유지·전환·gesture·timing의 전체 2차 예산은 고정 평균으로 제한한다.
- [설계 85–107행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:85): 기타 허용범위 내부 비용 0, 학습용 cap과 raw 이탈 기록 분리, 유효 press 영역 접근 plateau, 작은 시선·자세 예산이 일치한다. 2차 범위 [−0.100,+0.200]와 3차 범위 [−0.074,+0.076]의 합계 폭은 0.450β다. β=6/m_max에서 2.700/m_max < 4/m_max가 성립하며, 다른 1차·기타 항이 같은 undiscounted 비교로 한정한다.
- [설계 119–125행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:119): fatal 이전의 실제 증거·지급값을 보존하고 미래 미관측분만 실패로 정산한다. 고정 deadline/분모와 γ ledger를 유지하며 실제 중단 step과 미래 tail을 분리한다. 무상한 wrong-crossing 비용의 회피 문제는 M_cross·최악 잔여 예산 검증 전 pilot 금지 조건으로 남겼다. 가상 실패 return과 실제 source counter, 측정 실패와 물리 fatal도 구분한다.
- [설계 111–113행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:111): 상체 81 제어권·512→256 구조, root/하체 고정, 몸통의 작은 목표 범위와 실제 자세 deadband, Thorax부터 손가락 66의 native 권한을 유지한다. 실제 각도 고정이나 팔·손 초기각 복원으로 바뀌지 않았다.

## 산술·산출물 대조

[검사기](/home/ajou/yigyu/3/stability_adapter_2/check_reward_design_v4.py:1)와 [formula_checks.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/formula_checks.json)을 읽어 42개 PASS 기록, count 및 검사 범위를 확인했다. 별도 읽기 전용 계산으로 두 예산의 320개 꼭짓점, [원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/plot_data.json)의 접근 251개 표본·기타 거리 5개 표본·hold/onset 값을 재계산했고 일치했다. 동결 설계와 검사기 SHA는 두 JSON의 기록과 일치한다.

[최종 설명 11–13행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/README.md:11)과 [PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/reward_refinement.png)를 육안 대조했다. 정음 하한 1.826 > 실패 상한 1.609, hold 예시 β=1/N_F=1 및 일반 event 기여 0.10β/N_F, 접근 거리 mm 변환이 원자료와 일치한다. 독립 y축·설계 산술·새 물리/학습 0 표시를 확인했다. 정정 전 산출물은 별도 보존되어 있다.

[변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/CHANGED_FILES.md)과 실제 main 추가본문을 대조했다: PLAN 783행, A README 1924행, D README 611행, VISUAL_REPORT 2377행. 최신 설계와 미구현 조건을 일치하게 설명한다. 전체 기존 파일 보존 감사와 최종 봉인은 root 담당이며 이 검수에서 대신 수행했다고 주장하지 않는다.

## 검증 한계

42개 검사는 합성 수식·간단한 계약 사례의 산술 검사다. crossing 중복/잘못된 onset/종료 ledger 사례는 실제 detector나 tracker를 구동한 시험이 아니다. sounding-state·pad/depth·현재 기타 변환·SO(3) 회전집합·subframe snapshot/dwell·접촉 목록·시선 축·단일 clock, M_cross/γ/미정산 ledger 및 무학습 행동 시험은 [원문의 구현 전 조건](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:127)으로 남는다. 조건이 봉인되기 전에는 실제 pilot을 시작할 수 없다. 가중치 최적성이나 PPO 성공을 확인하지 않았다.

동결 설계 SHA-256: `0d7cff02416874ce98a60697503e1ce79e5fce8be52cdea8d9462617b80e56f1`.

이 검수 담당자가 작성한 파일은 이 `review.md` 하나다. 새 환경 변경·물리 실행·학습은 수행하지 않았다.
