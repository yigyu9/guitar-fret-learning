# 팀원 자세 판정표 시각화 검수

요약 판정: **문제없음**. Producer·원자료·최종 PNG·결과 문서/색인 및 상위 기록을 검수했다.

검수 범위는 두 후처리 producer, 세부 계획, 입력 CSV/기존 PNG와 analysis_v2의 두 최종 PNG 및 지표다. 원문·다른 담당자의 코드/문서는 수정하지 않았다.

- **Critical:** 없음.
- **Warning:** 없음.
- **Suggestion:** 없음.

## 코드·원자료 정합성

- 최종 [producer](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:1)는 CSV의 final 판정을 그대로 색상으로 사용하고 visual 기록 유무를 원/삼각형으로 구분한다. 판정을 재계산하거나 numeric_note의 미확인 수치를 물리 단위로 해석하지 않는다.
- CSV 96개의 numeric axis/value 쌍이 유일하며 dx/dy/dz 각 20개, elev/azim/roll 각 12개다. Visual 기록 39개·미기록 57개, baseline 0 행 부재, anomaly dy+2cm 한 개를 직접 확인했다. dy 이상치는 빈 보라 사각형으로 원자료 빨강 표본 위에 표시된다.
- 골반 기준 바디 중심 [17,24.5,8]cm와 위치 후보 [17~23,24.5~34.5,8~10]cm, 중앙 [20,29.5,9]cm는 사용자 설명의 후보다. 현재 환경의 world actor-root 위치나 실제 몸체 mesh로 해석하지 않는다.
- 넥 고도 후보 17~22°·중앙 19.5°와 팀원 기준 22°·기존 별도 수평 후보 0°를 구분한다. 방위 ±2°에는 실제 표본이 없으며 미검증으로 표시한다. Roll의 보고된 자연 후보 두 구간과 −10/−5°의 빨강 표본을 분리한다. 최종 v2는 두 빨강 점 사이를 연속 위험 구간으로 새로 채우지 않는다.
- 각 축의 후보를 곱한 3D box와 구간 막대는 조합·연속 구간·관통/동적 안전 인증이 아니다. 기준 p/q·회전 피벗·단위가 확인되지 않은 접촉 수치로 실제 시뮬레이션 판정을 만들지 않았으며 현재 환경 설정·허용범위·물리/학습을 변경하지 않는다.

## 보존·실제 그림 검수

첫 analysis와 최종 analysis_v2 각각의 입력 4개에 대해 before/after/current SHA가 정확히 일치함을 확인했다. 두 producer와 세부 계획의 source_final 사본도 현재 파일과 일치하고, before의 첫 producer 원문은 그대로다. 보호 목록 30파일의 SHA도 모두 유지됐다. CSV/기존 입력 PNG는 보존된다.

기존 입력 PNG 및 최종 pose_candidates.png/judgment_samples.png를 실제 열람했다. 최종 그림의 제목·범례·축·후보 선분·표본은 구분되며 첫 시도의 제목/범례 중첩이 최종 v2에서 해소됐다. 6축 96표본의 값·색·visual 기호, dy+2 anomaly, azim+15 numeric-only yellow, dz+6/+8 yellow를 CSV와 대조했다. 0 표본을 CSV 검증점으로 추가하지 않고 제안 후보·기준선으로만 표현한다.

그림은 좌표·방향 개념도이며 Isaac Gym native render가 아니다. 두 producer 실행은 원자료 후처리이고 새 물리 실행·학습 update는 0이다. 별도 의미 테스트 없이 문법 검사와 실제 원자료/그림 대조를 사용하는 검증 범위가 이 저영향 시각화에 적절하다.

## 최종 문서·상위 기록 검수

[결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/README.md:1)와 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/FILE_INDEX.md:1)의 후보 좌표·각도·오차와 원자료 판정/visual 기록 차이를 CSV·facts·실제 그림과 대조했다. 상대적 변화량과 사용자 설명의 절대 바디 중심 후보, 팀원 기준과 현재 별도 수평 후보를 구분하며 현재 환경에 적용한 값으로 표시하지 않는다. 첫 그림의 제목/범례 문제와 v2의 빨강 두 표본 분리도 설명한다.

최종 문서의 링크 34개는 모두 절대 경로·존재 파일·유효 줄 번호다. 현존 review/root 보존 검증과 마지막 생성할 inventory의 경로를 구분했으며 아직 없는 inventory를 완료된 감사로 표시하지 않는다.

[main PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:612), [누적 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:550), [누적 시각 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2268)의 추가 내용과 캡션은 이번 후처리/후보·검증 한계와 정합하다. 세 문서의 편집 전 전체 바이트가 현재 파일 prefix로 보존되는 append를 직접 확인했다. 새 PLAN 체크 완료는 그림·검수·기록 완료이며 물리·학습 성공을 추가하지 않는다.

Root가 생성한 changes.patch는 해당 세 기존 문서의 편집 전 사본과 현재 내용에서 재생성한 diff와 정확히 일치한다. 이전 영역의 링크는 이번 변경 대상으로 승계하지 않고 새 문서/추가 영역의 링크를 검수했다.

[root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/final_verification.json:1)의 status pass, 이전 진단 phase 30파일 보존, CSV 96/visual39·57/anomaly1, 입력 SHA 및 문법 종료코드 0은 독립 확인과 일치한다. 최종 변경 patch/산출물 SHA inventory 생성·봉인은 root 담당이며 이 검수가 해당 완료를 대신하지 않는다.
