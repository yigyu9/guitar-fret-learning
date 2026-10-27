# 원본 대비 strap −4 mm: body-9 비교

세 조건은 동일한 초기 humanoid/G 상태, 몸통 9관절 설정, 작은 손목 목표와 1200-step 실행을 사용하고 절대 strap rest length를 원본·−2·−4 mm로 비교한다. 새 −4 mm 실행은 5초 동안 1200 physics step을 완료했고 실제 native 영상은 151 frame(5.033333초)이다. 이 비교는 그립 완료, 초기 기타 위치·회전 복원, 학습 또는 연주 성공을 뜻하지 않는다.

![원본, −2 mm, −4 mm 조건의 기타 위치 오차·회전 오차·저장 strap 장력 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/artifacts/body9_strap_minus4mm_comparison.png)

그림의 세 패널은 저장 trace의 `time_s`(s), `position_error_m × 1000`(mm), `rotation_error_deg`(°), `last_applied_tension_n`(N)을 사용한다. 장력은 저장 상태 기준 직전 step에 적용된 법칙 장력이다. 연속 force 센서 측정으로 해석하지 않는다.

| 결과 | 원본 LA | −2 mm | −4 mm |
|---|---:|---:|---:|
| 초기 5초 최대 위치 오차 (mm) | 14.132607728 | 14.010555659 | 14.023528655 |
| 초기 5초 최대 회전 오차 (°) | 2.894327801 | 2.607664763 | 2.335921328 |
| 2초 이후 최대 위치 변화 (mm) | 0.481766500 | 0.363488152 | 0.404326254 |
| 2초 이후 최대 회전 변화 (°) | 0.091929111 | 0.070088885 | 0.079347132 |
| peak strap-law tension (N) | 24.129230476 | 28.152161370 | 28.097309320 |
| actual wrist scalar fit 진폭 (°) | 0.146929176 | 0.147836216 | 0.149522803 |

−4 mm는 −2 mm보다 최대 위치 오차가 14.010556에서 14.023529 mm로 조금 증가하고, 최대 회전 오차는 2.607665에서 2.335921°로 감소했다. 2초 이후 위치/회전 변화는 각각 0.363488/0.070089에서 0.404326/0.079347로 늘었다. peak strap-law 장력은 28.152161에서 28.097309 N으로 소폭 낮아졌다. wrist fit은 2–5초의 scalar q에서 원래 정적 baseline, 상수, trend, 1 Hz 성분을 분리한 값이며 bone rotation과 같다고 볼 수 없다.

−4 mm 실행에서 palm의 positive raw lambda와 human self-contact step은 각각 0이다. index3은 1200 step까지, 오른 허벅지 `R_Hip`도 1200 step까지 positive raw lambda가 기록됐다. thumb3은 163 step(마지막 1060), middle3은 28 step(마지막 59)이다. 이는 표본 기반 contact signal이며 연속적인 지지나 성공을 보증하지 않는다. 초기 LA는 1.0978469719600776 m로 원본보다 4 mm 짧고, 원본 대비 −2 mm 실행과 공통 11개 초기 필드·81개 관절 이름·1200개 제출 command가 일치한다.

실제 native hands 영상:

![−4 mm 조건의 실제 native hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/native/hands.mp4)

실제 native whole-body 영상:

![−4 mm 조건의 실제 native whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/native/whole_body.mp4)

실행의 초기 설정과 실제 81관절 값은 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/native/initial_values.json)에 있다. 13개 분석 check와 세 조건 요약은 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/analysis.json), 초기화·step·영상 보존 기록은 [native_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/native_execution.json)에 있다. 별도 ABI 조사에서 checkpoint audit null 표기 문제를 바로잡은 다섯 check는 [contract_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/contract_correction/contract_audit.json)에 기록되어 있다. 해당 조사는 illustrative ABI inspection이며 source admission이나 학습 실행이 아니다.

CPU PhysX와 기존 CUDA/visual 경고는 실행 기록에 보존되어 있다. source admission은 cooked penetration 인증이 아니며, 이 단계에서 추가 물리 실행이나 학습은 하지 않았다. 후속 결정은 별도 기록 예정이다. 이 phase의 독립 검수 기록은 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/review.md) 예정 경로다.

## 재현 산출물

그림 producer는 [make_body9_strap_minus4mm_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_body9_strap_minus4mm_artifacts.py)이며, 세 저장 trace와 analysis/input closure의 SHA를 생성 전후 비교한다. 결과 PNG와 입력·출력 manifest는 [artifacts 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/artifacts/)에 저장한다.
