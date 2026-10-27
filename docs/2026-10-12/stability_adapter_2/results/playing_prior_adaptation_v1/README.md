# 자유 기타 연주 전이 — 계약 조사와 학습 설계

이번 단위는 기존 fret·strike 정책을 어떻게 사용하고 학습으로 보정할지 정리했다.
신규 물리 실행0, physics step0, 학습 update0, actor inference0이다.
실행 계획은 [PLAYING_PRIOR_ADAPTATION_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:1)에 저장했다.

## CPU 조사 결과

| 항목 | Fret 예시 | Strike 예시 |
|---|---|---|
| 파일 | `20261001_2232…synergy/fret_047500.pt` | `20260920_Jazz1_sync_baseline/strike_010708.pt` |
| 관측/행동 | 420 / 30 | 303 / 30 |
| 저장된 학습 단계 | goal_pair | S3_SONG_INTEGRATION |
| action alpha / scale | 0.5 / 1.0 | 0.5 / 1.0 |
| 정규화 mean·var·count | 크기·finite 검사 통과 | 크기·finite 검사 통과 |
| 이번 채택 여부 | ABI 조사용, 미선정 | ABI 조사용, 미선정 |

[실제 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/contract_audit.json:1)에
절대 파일 경로·SHA·계약·관절 이름/현재 native 인덱스·정규화 통계 요약을 보존했다.
두 action 이름 집합은 겹치지 않으며 현재 주요66관절 안에 전부 포함된다.
추가6개는 좌우 Thorax x/y/z다. 네 가지 검사(계약 자체 무결성, 차원/이름 대응,
정규화 buffer, 입력 SHA 전후 일치)를 통과했다. 실행은 Python/Torch CPU metadata 읽기뿐이다.
원본 source assets와 현재 environment의 동등성, 원래 성능, frozen loader 자격,
actuator 동등성, 자유 기타 연주 성능은 이 검사로 인증하지 않았다.

## 권장 설계

기존 정책은 현재 기타 기준 관측을 받고, 가중치와 정규화를 먼저 동결한다.
한 개의 공동 residual이 연주 목표와 기타 초기 world p/q 오차를 함께 보아 66관절 목표를 보정한다.
후처리/제한/EMA/history를 정합시킨 뒤 하나의 최종 PD 목표만 물리에 제출한다.
연주 정확도와 기타 유지 성능을 별도로 기록해 양쪽 목적의 tradeoff를 확인한다.
몸통9 목표 유지, root·하체 고정, 자유 기타·수동 스트랩 조건은 유지한다.

다음은 source 평가 기록 기반 후보 선택과 작은 CPU 관측/action bridge 검사다.
그 뒤 짧은 실제 양손 연주 비교를 하고 residual 학습으로 진행한다.
LA total−4mm 실험은 별도의 미실행 계획으로 보존한다.

## 기존 물리 증거와 이미지 설명

아래는 **이전 LA−2mm·작은 손목 움직임 실험**의 실제 측정 그래프다.
새 연주 정책이나 이번 설계의 학습 성능을 보여주는 그림은 아니다.
0~5초 기타 초기 위치 오차(mm), 초기 회전 오차(°), 이전 step에 적용된 cable 법칙 장력(N)을
그린 기존 산출물이다. 길이를 줄이니 회전/후기 변화는 감소했지만 장력 peak는 증가했다.
이런 물리적 tradeoff에 연주 정확도 평가를 추가해야 한다는 근거로 인용한다.

![이전 LA−2mm 손목 시험의 기타 오차와 strap 장력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/artifacts/guitar_errors_and_strap_tension.png)

아래도 **이전 실험**의 실제 Isaac Gym 손 근접0~5초 영상이다. 실제 스트랩 경로 표시가 포함된다.
Fret/Strike actor는 실행하지 않았고 L_Wrist_x의 작은 목표 파형만 적용했다.

![이전 LA−2mm 손목 시험 실제 Isaac Gym 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/body9_strap_minus2mm_v1__native__hands.mp4)

[이전 물리 실험 조건/수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/README.md:1),
[전체 영상 목록124개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v3.md:1).
이번에는 새 영상 복사나 기존 영상/목록 수정이 없다.

## 검토와 역할

root가 설계·CPU 검사·문서 정리를 수행했다. Luna 작업 배정과 explorer 재사용,
change-reviewer 배정은 모두 `agent thread limit reached`로 실패했다.
독립 검수는 미완료이며 자체 검토와 구분한다. 승인 대기 조건은 아니다.
[자체 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/review.md:1),
[변경 줄 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/CHANGED_FILES.md:1),
[최종 보존 감사 예정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/final_verification.json:1).
