# 왼팔 PD 배율 비교 (v2)

이 단계는 동일 초기 자세와 기타 목표, 절대 strap rest length 1.1018469719600776 m, 제어 목표를 유지하고 왼팔 12축의 kp와 kd만 기준의 1배·1.5배·2배로 함께 바꾼 0.1초 진단이다. 각 조건은 fresh 실행 1회, 24 physics steps다. v2 분석은 여섯 구조 검사를 통과했으며, 기준 조건을 포함한 세 조건의 states/trace/tasks/contacts/controls는 해당 조건의 이전 기록과 정확히 일치한다.

| 왼팔 kp/kd | 최대 기타 위치 오차 (mm) | 최대 기타 회전 오차 (°) | 종료 손 추적점 오차 (mm) | 종료 source 법선 간격 (mm) | 양의 palm raw lambda 관측 |
|---:|---:|---:|---:|---:|---|
| 1× | 5.099186 | 0.972608 | 9.113399 | 9.047539 | step 2, 1행 |
| 1.5× | 5.630569 | 1.038888 | 9.024941 | 9.015126 | steps 1–2, 5행 |
| 2× | 6.145012 | 1.100045 | 9.335708 | 9.271041 | steps 1–2, 5행 |

![왼팔 kp/kd 배율에 따른 기타 오차, source 법선 간격, LH:palm raw lambda](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts/palm_hold_pd.png>)

그림의 세 상단/좌하 패널은 25개 저장 상태(0–0.1초), raw lambda 패널은 완료 physics step의 24개 접촉 기록(0.004167–0.1초)을 보여준다. t=0 lambda 표본을 만들지 않았다. 법선 간격은 source 측정값이며 cooked clearance를 인증하지 않는다. raw lambda는 N으로 환산되지 않았고 지지력 또는 지속 접촉을 뜻하지 않는다.

배율을 높일수록 이 짧은 구간에서 기타 오차가 커졌다. 접촉 기록은 초기 몇 step 뒤 양의 palm raw lambda가 유지되지 않았음을 보여준다. 이 결과로 배율 변경을 채택하지 않으며 안정성·연주 성공을 주장하지 않는다. v1의 setter 반환값 검증 누락은 [검증 기록](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_VERIFICATION.md)에 보존했고, v2에서 해당 검사를 보완했다. v1 원자료와 검증 누락 기록은 그대로 두었다.

v1 전체는 3 init/72 step, v2 전체도 3 init/72 step이며 각 배율 조건은 1 init/24 step이다. v1은 setter boolean 확인이 빠진 이전 기록이고 v2는 이를 보완한 별도 실행이다. v2의 초기 후처리 import 실패는 `analysis_attempt_v1/`에 보존되어 있으며 native 실행은 포함하지 않는다. stderr는 [실행 메모](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/EXECUTION_NOTES.md>)에 기록된 대로 도구 응답에 반환됐고 stdout 파일에 합쳐지지 않았다. 최종 saved-only 분석은 성공했다. 다음 검토는 [강성만 분리 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1)을 따른다.

재생성은 새 출력 디렉터리를 지정한다. 예: `MPLCONFIGDIR=/tmp/stability2_palm_hold_pd_plot MPLBACKEND=Agg python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_pd.py --out-dir /tmp/palm_hold_pd_reproduction`. 플로터는 저장된 analysis/trace/contact 자료만 읽고 native 시뮬레이션을 실행하지 않는다. 생성 당시 command와 종료 코드는 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/plot_execution.json), 입력 및 이미지 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts/plot_manifest.json)에 기록했다.
