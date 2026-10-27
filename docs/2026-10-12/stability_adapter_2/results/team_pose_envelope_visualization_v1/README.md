# 팀원 기타 자세 판정표 시각화

팀원 자료의 판정 표본과 별도로 제시된 자세 후보를 함께 살펴볼 수 있도록, 사용자가 자료의 유용성을 확인한 뒤 요청한 시각화다. 원자료는 `fret_041000` 바디 중심·골반 기준 자세 판정 CSV 96행이다. 이는 현재 StabilityAdapter 2 환경의 허용 범위 변경이나 실험 결과가 아니다. 이번 작업에서 새 물리 실행 0회, 학습 갱신 0회, 설정 변경 0회다.

## 결과 그림

### 후보 위치와 회전 기준 개념도

왼쪽 위의 상자는 팀원 설명에 나온 골반 기준 바디 중심 위치 후보를 cm로 표시한다. 기준점은 (오른쪽 17, 앞 24.5, 위 8) cm이고 후보 범위는 오른쪽 17–23, 앞 24.5–34.5, 위 8–10 cm다. 가운데 보라색 마름모 (20, 29.5, 9) cm는 이 후보 상자의 조합 목표 제안이다. 이 점과 상자는 기록된 실제 기타 궤적이나 물리적으로 검증된 허용 체적이 아니다.

넥 고도 패널은 팀원 기준 22°, 보고서 후보 구간 17–22°와 그 중앙 제안 19.5°를 개념선으로 보여준다. 우리 쪽 수평 넥 후보 0°는 다른 기준으로 함께 표시했다. 기타 형상과 실제 회전 중심은 확인되지 않았다.

방위 패널의 빗금 ±2°는 제안 오차이며 검증된 허용 범위가 아니다. 실제 CSV 점은 −5°와 +5°부터 있어 이 구간을 직접 표본화하지 않았다. +15°에는 숫자 판정 노랑이 있지만 visual 판정 기록은 없다. roll 패널은 보고서의 두 후보 구간 −20°~−15°와 0°~+25°를 끊어서 표시한다. 원자료 빨강 표본 −10°와 −5°는 별도 점이다. 보라색 +10° ±10° 선분은 제안 목표와 오차 표시다. 이 후보·선분은 구간 전체 또는 다른 축과의 동시 조합 검증을 뜻하지 않는다.

![골반 기준 위치 후보와 넥 고도·방위·roll의 제안 및 원자료 표본 개념도](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/pose_candidates.png)

### CSV 96개 판정 표본

여섯 축별 점은 CSV 원행을 그대로 나눠 표시한다. 색은 원자료의 최종 판정(노랑 자연, 주황 경계, 빨강 무너짐)이고, 원은 visual 판정 기록 있음, 삼각형은 visual 미기록이다. 보라색 빈 사각형은 원자료에서 재확인 대상으로 표시된 이상치다. 보라색 마름모와 가로 error bar는 축별 제안 목표와 오차를 나타내며 CSV의 추가 측정값이 아니다. 축별 제안 후보는 dx +3±3 cm, dy +5±5 cm, dz +1±1 cm, 넥 고도 −2.5±2.5°, 방위 0±2°, roll +10±10°다. 점 사이를 선이나 면으로 잇지 않아 관측하지 않은 중간 값을 판정하지 않는다.

96행 가운데 visual 판정 기록은 39행, 미기록은 57행이다. CSV에는 기준 변화량 0의 행이 없어, 그림의 0 기준선이나 제안 목표가 실제 0 변화 표본을 뜻하지 않는다. dy +2 cm 한 행은 원자료에서 numeric/final 빨강과 anomaly로 기록됐고, 판정 메모는 `허벅지 관통(68574, R_Hip)`이다. 이는 팀원 자료에 기록된 표기를 옮긴 것이며 새 물리 확인 결과가 아니다.

![CSV 96개 판정 행의 축별 색상·visual 기록 여부·이상치·제안 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/judgment_samples.png)

## 해석 범위

두 그림은 좌표 개념도와 원자료 표본 도표다. Isaac Gym 장면 렌더, 실제 기타 형상 배치, 접촉·관통·힘 측정, 6축 조합의 허용 영역 인증이 아니다. 첨부 자료에는 접촉력 단위·깊이·측정 시점과 회전 피벗 정보가 없어 그 의미를 새로 추정하지 않았다. 기존 StabilityAdapter 2 허용 box나 각도 조건을 이 후보 그림으로 대체하거나 승계하지 않는다.

첫 analysis 그림은 범례와 제목 배치 문제를 확인한 뒤 원본 그대로 보존했다. 최종 설명은 별도 `analysis_v2` 그림만 사용한다. v2에서는 범례를 아래로 옮기고 roll의 원자료 빨강 −10°·−5°를 두 점으로 그려 분리했다. 최종 그림과 facts를 만들 때 CSV, v2 producer, 글꼴, leaf 계획의 4개 입력 SHA가 전후 동일했다.

입력·producer 줄 근거와 main PLAN의 진행 위치는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/FILE_INDEX.md:1)에 정리했다. 독립 검수 기록 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/review.md:1)와 root 보존 검증 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/final_verification.json:1)을 참조한다. 최종 SHA 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/artifact_inventory.json`.
