# 파일 색인

각 파일 경로는 절대 경로다. 코드·계획·검증 링크는 실제 관련 줄을 가리킨다. 표와 문장에 적은 측정치는 저장된 분석 JSON 및 승인 brief에 근거한다.

## 산출물

- [결과 설명과 10개 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/README.md:1)
- [이 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/FILE_INDEX.md:1)

## 저장 분석 자료

- [분석 요약 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/summary.json:1)
- [113개 표본 지표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/metrics.json:1)
- [입력·정합 검사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/checks.json:1)
- [입력 SHA 목록 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/inputs_before.json:1)
- [입력 SHA 목록 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/inputs_after.json:1)
- 원본 실행 자료: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/`

## 그림 파일

- [frame 000 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_000_whole_body.png)
- [frame 000 손 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_000_hands.png)
- [frame 060 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_060_whole_body.png)
- [frame 060 손 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_060_hands.png)
- [frame 090 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_090_whole_body.png)
- [frame 090 손 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_090_hands.png)
- [frame 112 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_112_whole_body.png)
- [frame 112 손 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_112_hands.png)
- [2초·종료 비교 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/comparison.png)
- [113개 표본 추세 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/trends.png)

## 구현·계획·의미 검증

- [후처리 계획: 입력 run과 한계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:5)
- [저장 실행과 113개 표본 기준](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:7)
- [지표 정의·해석 한계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:9)
- [시간·좌표 정합 및 표시 기준](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:21)
- [다음 제어 소단계의 승인 범위](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md:29)
- [자세·기준축 계산](/home/ajou/yigyu/3/stability_adapter_2/playing_posture_diagnostic.py:44)
- [12관절 한계 여유 계산](/home/ajou/yigyu/3/stability_adapter_2/playing_posture_diagnostic.py:57)
- [420D 활성 목표 계산](/home/ajou/yigyu/3/stability_adapter_2/playing_posture_diagnostic.py:71)
- [관측 시점 정렬](/home/ajou/yigyu/3/stability_adapter_2/playing_posture_diagnostic.py:91)
- [후처리·입력 SHA 검사](/home/ajou/yigyu/3/stability_adapter_2/playing_posture_diagnostic.py:166)
- [자세·quaternion·공통 변환 의미 검증](/home/ajou/yigyu/3/stability_adapter_2/test_playing_posture_diagnostic.py:14)
- [한계 초과 signed margin 검증](/home/ajou/yigyu/3/stability_adapter_2/test_playing_posture_diagnostic.py:38)
- [저장 ABI 활성 목표·단위 검증](/home/ajou/yigyu/3/stability_adapter_2/test_playing_posture_diagnostic.py:45)
- [카메라 투영 검증](/home/ajou/yigyu/3/stability_adapter_2/test_playing_posture_diagnostic.py:64)
- [적분 전·종료 관측 시각 검증](/home/ajou/yigyu/3/stability_adapter_2/test_playing_posture_diagnostic.py:73)

## 상위 계획·기록 반영

- [실행 계획의 현재 연주 자세 소단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:603)
- [StabilityAdapter 2 인계 요약의 결과 추가](/home/ajou/yigyu/3/stability_adapter_2/README.md:10)
- [누적 결과 README의 진단 항목](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:546)
- [누적 시각 보고서의 진단 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2260)
- [누적 시각 보고서의 해석 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2266)

## 검수·보존 기록

- [독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/review.md:1)
- [보존 소스 디렉토리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/source_final/)
- [root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/final_verification.json:1)

최종 산출물 SHA 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/artifact_inventory.json`.
