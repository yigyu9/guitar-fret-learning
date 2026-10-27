# CP86 후속 학습 결과 독립 검수

요약 판정: **완료된 CP86 평가·분석·산출물은 문제없음**. 장기 학습 전체 완료, 음악 성공, 다음 후보 시험의 효과는 인증하지 않는다.

## Critical

없음. 추가 물리 실행이나 학습 없이 저장된 자료와 소스를 읽기 전용으로 대조했다.

## 확인 결과

- [분석 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/analysis_v1.json): CP1 이후 고정 로그의 추가 85회 갱신(총 86회·22,016 전이), 체크포인트 ABI·설정·평가 식별자, Actor/Critic 변경, RMS 불변을 확인했다. 로그의 최대 최종 rollout KL은 0.01999991로 설정 상한 0.02 이내다.
- 두 deterministic 평가는 동일 초기 상태·PD·ABI·RMS로 각각 16.3667초, 982 제어·3,928 물리 단계와 492프레임을 완료했다. 안전 종료 없이 42이벤트를 정산했지만 음악 성공·인정 crossing은 0이며, 양쪽 실제 crossing 3회는 모두 wrong_string이다.

| 지표 | CP1 | CP86 |
|---|---:|---:|
| 위치 상자 밖 비율 | 45.82485% | 49.89817% |
| 최대 외부 거리 | 0.473142m | 0.419738m |
| 평균 외부 거리 | 0.0940894m | 0.0831205m |
| 초기 기타 quaternion 대비 최대 SO(3) 회전 | 95.8645° | 88.9132° |
| 외부 거리 10cm 초과 최초 시각 | 13.2167초 | 13.2667초 |

최대·평균 거리 감소와 범위 밖 비율 악화를 함께 기록하는 해석이 맞다. 약 13.3초부터 큰 위치 이탈이라는 표현은 그 이전 자세·회전의 안정성을 뜻하지 않는다. PLAY press-cell 427→466/3,448프레임은 압현 진단이며 목표 음 성공 인증이 아니다.

- [보상 분해](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/reward_analysis_v1.json)의 deterministic return −41.04112→−35.68874는 저장 ledger 재구성 오차 0이다. 주된 개선은 위치·회전 항이며 음악 성공으로 해석할 수 없다. 설정 half-life에서 도출한 γ·λ와 GAE 계수는 산술 진단이다. 학습 중 정책이 바뀌는 22개 stochastic episode return과 구분했다.
- [행동 규모 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/action_scale_diagnosis_v1.json): CP86 최대 요청 residual은 팔 0.004977rad·손가락 0.003699rad(각 cap의 1.66%·1.85%)이다. latent std 약 0.01831 및 t0 변환 분포 95% 반폭 약 0.6167°·0.4110°는 native clipping/rate 전 요청값이며 실제 관절 이동이 아니다. 작은 요청값만으로 실패 원인을 확정하지 않는다.
- 실제 PNG 5개를 열어 프레임·곡선·범례를 원자료와 대조했다. 입력 57개와 행동 진단 추가 입력 18개의 전후 SHA, 영상·프레임 SHA, 절대 링크를 확인했다. archive_v3 영상 2개의 원본·사본 SHA와 ffprobe 정보는 일치하며, 이는 전체 영상 decode나 실험 성공 인증이 아니다. 실패한 보상 분석 v1 소스와 실패 기록은 보존되어 있다.

## Warning

미해결 항목 없음. [README_V2.md:32](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/README_V2.md:32)의 ‘탐색 폭을 낮춘’ 문장은 [README_V3.md:32](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/README_V3.md:32)에서 ‘늘린 조건(std 0.06 우선)’으로 정정되었다. [다음 단계 계획:9](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/NEXT_STEP_BRIEF_V1.md:9)과 일치하며 기존 약 0.0183 대비 약 3.3배 증가, cap·몸통/머리 설정 유지, 미실행 후보임이 명확하다. V2는 보존됐으며 V3는 이 문장만 바뀌었다. 새 문서·색인·추가 provenance SHA도 전달값과 일치한다.

## Suggestion

선택적 다음 시험은 동일 CP86 평균 정책과 초기 상태에서 탐색 분포만 바꿔 비교하도록 범위를 유지한다. 현재 결과를 보상 변경이나 탐색 폭 부족의 인과적 증거로 단정하지 않는다.

## 검수 범위

검수자가 새 native 실행·정책 학습·기존 파일 수정은 하지 않았다. CP86까지 고정된 완료 자료만 판정했으며, 계속 실행 중인 long_on_v1의 이후 갱신·최종 완료·일반화 성능 및 미실행 탐색 후보는 제외한다.

