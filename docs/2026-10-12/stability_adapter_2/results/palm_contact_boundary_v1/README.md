# 고정 palm 목표 보정의 접촉 경계 관측

이번 분석은 같은 startup bias에 기존 fit delta의 배율 α를 곱해 더한 상수 목표를 0.1초 유지한 여섯 조건을 비교한다. α=.25와 .50은 앞선 phase에서 저장된 기준 run이고, 이번 phase에서 새로 초기화한 run은 .30/.35/.40/.45 네 개다. 나머지 초기 자세·기타 설정 목표 p/q·절대 strap 길이·PD·root·하체·self-collision 조건은 유지했다.

| α | 초기화 출처 | 종료 point 오차 (mm) | 종료 source normal gap (mm) | 기타 최대 위치 오차 (mm) | 기타 최대 회전 오차 (°) | palm 접촉 기록 step | 양의 raw λ step / 행 |
|---:|---|---:|---:|---:|---:|---|---|
| .25 | 이전 quarter 기준 | 11.093705 | 10.937180 | 5.093169 | 0.968542 | 1–4 | 없음 / 0 |
| .30 | 새 run | 10.470949 | 10.342860 | 5.084351 | 0.968301 | 1–4 | 없음 / 0 |
| .35 | 새 run | 9.846613 | 9.748404 | 5.066143 | 0.967622 | 1–5 | 없음 / 0 |
| .40 | 새 run | 9.222524 | 9.152198 | 5.047986 | 0.967032 | 1–6 | 없음 / 0 |
| .45 | 새 run | 9.288558 | 9.296482 | 5.341201 | 1.006166 | 1–5 | 2 / 2 |
| .50 | 이전 half 기준 | 8.997563 | 9.028552 | 5.526571 | 1.025444 | 1–5 | 1–2 / 4 |

![여섯 α 조건의 0.1초 저장 응답: 기타 오차, source normal gap, raw palm lambda](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/palm_contact_boundary.png)

위쪽 기타 곡선의 실선은 설정한 초기 목표와의 world 위치·회전 오차이고, 점선은 native 초기 자세를 기준으로 한 별도 드리프트다. t=0에서 설정 목표와 native 초기 readback 사이의 작은 수치 차이는 위치 약 1.026e−8 m, 회전 약 1.449e−5°로 남아 있으며, 두 기준을 하나의 오차로 합치지 않았다. 회전은 world SO(3) rotvec norm을 도 단위로 바꿨다.

양의 raw palm λ는 이 표본에서 α=.40과 .45 사이에 처음 관측됐다. .45의 양의 값은 step 2의 두 행뿐이고, .40은 palm 접촉 기록이 step 1–6에 있어도 양의 λ가 없다. 이는 이 샘플 구간의 관측이며 정밀 임계값, 지속 지지, 실제 힘(N) 또는 연주 성공을 뜻하지 않는다. Source normal gap도 cooked clearance 인증값이 아니다. 모든 run은 0.1초여서 장기 유지 여부는 확인하지 않았다.

다음 분석 방향은 .45 접촉 조건 주변에서 12축의 작은 응답을 측정해 손과 기타 응답을 함께 살피는 것이다. 이 결과만으로 α를 새 feedback으로 바꾸거나 후보를 최종 채택하지 않는다.

## 재생성 및 검증

이 그림은 저장 analysis/trace/contact 자료만 읽는다. 재생성에는 존재하지 않는 새 출력 폴더를 지정한다. 아래 예시 경로가 이미 있으면 다른 새 경로로 바꾼다.

```bash
MUJOCO_GL=disable MPLBACKEND=Agg MPLCONFIGDIR=/tmp/stability2_palm_contact_boundary_plot \
  python3 stability_adapter_2/plot_palm_contact_boundary.py \
  --out-dir /tmp/stability2_boundary_replot_01
```

[분석 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/analysis.json:1)는 7개 검사를 모두 통과했으며, 새 실행은 4회 초기화/96 physics step이다. 그중 `alpha_bias_and_all_float32_targets_exact`는 각 저장 목표가 baseline bias + α×fit delta와 일치하는지 검증한다. [입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/plot_manifest.json:1)는 analysis, producer 및 여섯 run의 trace/contact 파일을 읽기 전후 대조한다. [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/plot_execution.json:1)와 [plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_contact_boundary.py:1)도 보관한다. 이전 analyzer guard 기준으로 만든 `artifacts/`, `artifacts_attempt_v1/`, `artifacts_validated_attempt_v1/`은 과거 출력으로 보존했고, 이 문서와 canonical 그림은 최종 7-check analysis를 읽은 `artifacts_validated/`를 가리킨다.

과거 출력 보존 한계: `artifacts_attempt_v1`의 PNG와 입력·출력 manifest는 남았지만 당시 producer 원문1버전은 보관되지 않아 정확히 복원하지 못했다. 두 단계의 다른3버전은 SHA가 일치하는 원문을 보관했다. 최종 canonical producer·입력·출력은 모두 검증했다. [보존 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/archive_recovery.json:1)에 기록한다.
