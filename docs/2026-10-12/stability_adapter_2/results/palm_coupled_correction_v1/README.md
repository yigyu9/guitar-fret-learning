# Palm–guitar 결합 보정 비교

이 보고서는 기준과 새 quarter/half/full 상수 목표 보정의 저장된 0.1초 native 실행을 비교한다. 세 새 후보는 이전 12축 응답 행렬의 편향 보정량을 각각 0.25, 0.5, 1.0배 적용했다. 초기 자세, 기타의 초기 위치·회전 목표, 절대 strap 길이 1.1018469719600776 m, PD 목표 구조와 물리 설정은 유지했다. 기타 초기 목표값은 모든 조건에서 동일하며 기타 오차를 이용한 feedback은 구현하지 않았다.

|조건|손바닥 추적점 오차 종료 (mm)|기타 위치 오차 최대 (mm)|기타 회전 오차 최대 (°)|양의 raw palm λ step / 행|
|---|---:|---:|---:|---:|
|기준|9.288558|5.341201|1.006166|2 / 2|
|quarter|9.234431|5.269186|0.996954|2 / 2|
|half|9.189884|5.207335|0.988677|2 / 2|
|full|9.113399|5.099186|0.972608|2 / 1|

![기준 및 세 보정의 기타 오차, source 간격, raw 접촉 lambda 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifacts/palm_coupled_correction.png)

그림의 기타 위치 오차는 설정된 초기 기타 위치 목표와 저장 pose의 차이이며, 회전은 (R_actual R_goal^-1)의 world SO(3) 회전벡터 norm을 도 단위로 표시했다. source normal gap은 별도 source-shape 측정값으로 cooked clearance가 아니다. Raw λ는 원시 contact 값으로 힘 단위 N으로 환산하지 않았다. 모든 조건에서 양의 값은 step 2에서만 나타났고 이후 지속되지 않았다. 접촉 행이나 λ만으로 지지력·안정성·연주 성공을 판정하지 않는다.

full 조건은 비교한 네 조건 중 최대 기타 오차와 종료 손바닥 추적점 오차가 가장 작았지만, 차이는 작고 접촉은 일시적이다. 네 조건 어느 것도 안정 자세나 지속 지지로 채택하지 않는다. 12축 목표 편향의 SLSQP 추정은 국소 0.1초 응답 모델을 사용했다. 이번 full 후보의 예측과 실제 차이는 손 위치 0.127097 mm, 손 normal 회전벡터 0.009713°, 기타 위치 0.107389 mm, 기타 회전벡터 0.014706°였으며 통과 기준이 아니다. 이는 world 회전벡터 기반 비교이지 DOF 또는 Euler 각도 차이가 아니다.

기존 fit 산출물은 입력 읽기 시점 보정으로 다시 계산했고, 입력 SHA 목록 이외의 11개 결과 필드가 기존 fit과 정확히 일치함을 확인했다. 이 후처리에는 native 초기화나 physics step이 없었다. 새 native 실행은 quarter/half/full 각각 24 step이며 기준은 이전 결과의 저장 자료다. 재현 가능한 fit 및 조건 계획은 [결합 보정 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1)에 있다.

그림 재생성 명령은 새 출력 폴더를 사용한다. 기존 출력이 있으면 producer가 덮어쓰기를 거부한다.

```bash
cd /home/ajou/yigyu/3
MPLBACKEND=Agg python stability_adapter_2/plot_palm_coupled_correction.py \
  --out-dir /tmp/stability2_coupled_correction_replot_01
```

원 분석은 5개 검사를 통과했고 3회 native 초기화 및 총 72 physics step을 기록했다. 그림 producer는 Python 문법 검사와 실제 렌더링을 통과했다. 이 비교는 국소 보정 진단이며 controller 성능이나 장기 안정성 인증이 아니다.

다음에는 [관절 유지 관측](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_OBSERVATION_PLAN.md:1)으로 native 질량·drive property·total DOF force를 읽는다. gain을 바꾸거나 drive 포화를 단정하지 않는다. [원자료 관측 근거](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/hold_observation_seed.json:1)에 contact pair와 관절 좌표 차이를 기록했다.
