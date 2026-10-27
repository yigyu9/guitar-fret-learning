# Palm support-weight 저장 trace 비교

검증된 분석은 6개 구조 검사를 통과했고 세 native initialization에서 총 72 physics step을 기록했다. 이 보고서는 `scale_0p08`, `scale_0p02`, `scale_0`의 저장 자료를 비교한다. scale은 normal-task orientation 항의 길이 단위 정규화값(m/rad)이며 물리 하중이나 힘 가중치가 아니다.

| normal scale (m/rad) | 손 추적점 최대 오차 (mm) | source 법선각 최대 (°) | 종료 signed source gap (mm) | 종료 접선 거리 (mm) | 기타 최대 위치/회전 오차 (mm / °) | palm contact 기록 |
|---:|---:|---:|---:|---:|---:|---|
| 0.08 | 12.186877 | 1.280689 | 11.864499 | 2.989581 | 5.107730 / 0.969008 | step 1–2, 7행 |
| 0.02 | 12.447904 | 1.281836 | 12.093581 | 3.146820 | 5.107730 / 0.969008 | step 1–2, 7행 |
| 0 | 17.168120 | 6.954837 | 15.271071 | 7.941241 | 5.107730 / 0.969008 | step 1–3, 10행 |

세 조건의 palm-contact 행은 모두 raw `lambda=0`이며 해당 기록 이후에는 palm contact 행이 없다. scale 0에서 contact 행이 한 step 더 기록됐지만 이는 하중이나 지지의 증거가 아니며 개선 판정으로 사용하지 않는다. 모든 조건의 전체 기타 body states는 이전 비교와 정확히 같고 기타 최대오차도 동일하다. 따라서 orientation weighting을 줄인 결과 기타 위치·회전 개선은 관측되지 않았다.

곡선은 각 저장 `normal_tasks.json`에서 첫 세 성분의 norm을 mm로 표시한다. 뒤 세 성분은 orientation scale이 0인 실행도 포함해 모두 `/ 0.08`로 환산한 법선 대향각(°)이다. 이 값은 전체 SO(3) 각도나 해부학적으로 보정된 palm 방향이 아니다. Signed gap, 접선 거리와 palm-up 값도 source geometry 측정이며 PhysX cooked clearance, 접촉력 또는 지속 지지를 인증하지 않는다.

![세 scale 조건의 손 추적점·법선각·기타 오차 저장 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/palm_support_weight.png)

Bias와 feedback의 orientation weighting을 함께 바꾼 비교라 단일 항목의 효과로 분리하지 않는다. 0.08은 별도 finite-horizon/strap 진단에서 기존 기준으로 남긴다. 이는 최종 weight 선정이나 안정화·연주 성공 판정이 아니다.

phase 로그에는 초기 후처리 import가 `MUJOCO_GL` 미설정으로 중단된 기록이 남아 있다. `MUJOCO_GL=disable` 환경으로 후처리를 다시 수행했으며, 어느 시도도 native initialization이나 physics step을 실행하지 않았다. 이는 물리 실행 실패가 아니다.

실행 명령·환경·SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/plot_manifest.json), [plot 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/plot_execution.json), [변경 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/CHANGED_FILES.md)에 기록했다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/review.md:7)는 완료됐고 남은 지적은 없다.
