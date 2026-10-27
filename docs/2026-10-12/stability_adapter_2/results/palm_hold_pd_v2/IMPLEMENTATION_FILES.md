# 이번 소단계 구현·계획 파일

표의 링크는 현재 파일의 실제 함수·제목 줄을 가리킨다. 관측과 첫 PD 실행,
반환값 검사를 보완한 PD 실행을 구분한다. 결과 미디어 인덱스는 CHANGED_FILES.md에 있다.

| 파일 | 변경 내용 |
| --- | --- |
| [관측 runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_hold_observation.py:16) | 계측만 추가한 두 실행, 질량/PD/총 DOF force 관측과 원자료 exact 검사 |
| [관측 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_hold_observation.py:14) | 두 조건 좌표·속도·총 힘과 입력 봉인 검증 |
| [관측 그래프](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_observation.py:165) | 기존 .45 bias와 전체 목표 보정 비교, t0 힘 없음 |
| [첫 PD runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_hold_pd.py:16) | 왼팔12 kp/kd 배율 비교; setter bool 미확인 이력으로 보존 |
| [검증 PD runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_hold_pd_verified.py:16) | setter 성공 반환값까지 검사한 별도 재실행 |
| [PD 그래프](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_pd.py:129) | 저장 자료의 기타 p/q·source gap·raw lambda 그래프 |
| [PD 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_hold_pd.py:15) | v2 세 조건과 v1 같은 배율 원자료5배열 exact 검증 |
| [관측 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_OBSERVATION_PLAN.md:1) | 계측 소단계의 봉인된 계획 |
| [PD 비교 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_PLAN.md:1) | 동일 초기 상태의 kp/kd 1/1.5/2배 |
| [보완 검증 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_VERIFICATION.md:1) | 첫 실행의 누락 범위와 보완 재실행 |
| [다음 강성 분리 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1) | kd 유지, kp만 비교하는 미실행 계획 |
| [기준 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_hold_pd_v1/scale_1.json:1) | 동일 full candidate, 배율1 |
| [1.5배 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_hold_pd_v1/scale_1p5.json:1) | 동일 full candidate, 배율1.5 |
| [2배 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_hold_pd_v1/scale_2.json:1) | 동일 full candidate, 배율2 |
| [메인 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:632) | 측정 결과·다음 방향 |
| [메인 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1233) | 구현·실행·검수 진행 체크 |
| [산출물 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:389) | 관측/PD 비교의 누적 결과 |
| [시각 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1212) | 그림91 관측, 그림92 PD 비교와 해석 범위 |
