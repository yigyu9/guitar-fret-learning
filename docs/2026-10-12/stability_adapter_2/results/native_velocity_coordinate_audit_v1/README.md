# Native 관절 속도 좌표 읽기 감사

저장된 geometry PI EFFORT trial의151개 상태만 읽었다. 동일 snapshot에서 native scalar v는 `ω_child,W−ω_parent,W ≈ R_child,W B v`와 가깝게 맞는다. v를 scalar q의 시간미분으로 자동 사용하지 않는다. 저장 pose 중앙차분은 native 각속도와도 큰 오차가 있어 실제 시간미분·Jacobian·torque 좌표 등가성은 검증하지 않았다.

## 입력과 범위

- [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data/trace.json):0~5초,151개,8physics-step 간격,30Hz.
- [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data/initial_values.json):native81DOF/66body 이름으로 index를 찾는다.
- [XML](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:113):8개3DOF그룹의 부모 body와 각 joint axis. L/R Thorax→Chest, Shoulder→Thorax, Elbow→Shoulder, Wrist→Elbow.
- A 코드·자산·native physics·source 모델·clock·force를 수정하거나 실행하지 않았다. 새 D의 지정3파일만 생성했다. 모든 입력의 실행 전후 SHA 일치를 확인했다.

## 비교식

`q=(q_x,q_y,q_z)`와 `v=(native_vel_x,native_vel_y,native_vel_z)`를 별도로 읽는다. 이름 suffix를 world축으로 해석하지 않는다. XML axis를 열로 쌓은 `B=[[1,0,0],[0,0,1],[0,1,0]]`가 이8그룹에 적용된다. `R_p,R_c`는 각각 부모·자식 body의 world rotation이다.

기준 `Ω_W = ω_c,W − ω_p,W`는 같은 snapshot의 `human_body_states[*].vel.angular` 차이다. 비교 후보는 다음과 같다.

- 부모 tangent 가정: `R_p Bv`.
- scalar v=qdot 가정의 chart 미분: `R_p J_left(Bq) Bv`.
- 자식 tangent 가정: `R_c Bv`.
- 추가로 `R_p v`, `R_p J_left(Bq)v`, `R_c v`, `R_p Exp(Bq)Bv`, `R_p Exp(Bq)v`, `Bv`, `v`도 평가했다.

`J_left(φ)=I+(1−cosθ)/θ²[φ]×+(θ−sinθ)/θ³[φ]×²`, `θ=||φ||`. RMS는 `sqrt(mean(||prediction−Ω_W||²))`, max는 벡터 오차 norm의 최댓값이다. 모두rad/s. 비자명 표본은`||v||>.01rad/s`; 별도로`||Ω_W||>.01`mask 결과도 JSON에 저장했다.

## 같은 snapshot 결과

8그룹 합친1188표본:

| 표현 | 벡터 RMS rad/s | max rad/s |
|---|---:|---:|
| `R_parent,W @ B @ v_native` | 0.169846191 | 1.1348891 |
| `R_parent,W @ J_left(Bq) @ B @ v_native` | 0.087251503 | 0.578557838 |
| `R_child,W @ B @ v_native` | 0.000365238153 | 0.00320077132 |
| `R_parent,W @ Exp(Bq) @ B @ v_native` | 0.000365239031 | 0.00320078323 |
| `R_child,W @ v_native` | 0.264458011 | 1.45511189 |

`R_c Bv`와`R_p Exp(Bq)Bv`의 결과는 거의 같다. 이는 이 raw에서 확인된 수치 관계이며 일반 asset의 rest-frame 변환을 생략해도 된다는 계약이 아니다.

| 그룹 | 표본 | 부모 Bv RMS | 부모 J_left Bv RMS | 자식 Bv RMS | 자식 Bv max |
|---|---:|---:|---:|---:|---:|
| L_Thorax | 150 | 0.0096544136 | 0.0048245445 | 1.5735018e-05 | 7.5951016e-05 |
| L_Shoulder | 150 | 0.13734 | 0.07001422 | 2.1599447e-05 | 0.00019704052 |
| L_Elbow | 150 | 0.082715169 | 0.042663463 | 2.3674162e-05 | 0.00014942983 |
| L_Wrist | 147 | 0.076137376 | 0.038578931 | 2.6561508e-05 | 9.4132416e-05 |
| R_Thorax | 150 | 0.028138685 | 0.014087671 | 4.8213553e-05 | 0.00017814285 |
| R_Shoulder | 150 | 0.22161607 | 0.11489714 | 0.00048826392 | 0.0018202818 |
| R_Elbow | 150 | 0.36517402 | 0.18765296 | 0.00080106692 | 0.0032007713 |
| R_Wrist | 141 | 0.12089309 | 0.06081118 | 0.00042790802 | 0.0015575571 |

가장 큰 자식 Bv 오차는R_Elbow3.666667초 `.00320077rad/s`이다. 따라서 exact라고 부르지 않는다. 좌·우8그룹 모두 자식 Bv 표현이 다른 주요 후보보다 훨씬 가깝다.

## 독립 pose 중앙차분과 한계

`R_rel,i=R_p,i⁻¹R_c,i`, `Ω_FD,W=R_p,i log(R_rel,i+1 R_rel,i−1⁻¹)/(t_i+1−t_i−1)`를 내부149표본에서 계산했다. q 중앙차분도 같은 구간이다. 양옆 구간은16physics-step=.066667초다.

참고용 chart 변환은 `qdot_implied=B⁻¹ J_left(Bq)⁻¹ R_rel Bv`이다. 이는 자식 tangent와 pose chart를 연결한 수학적 도출량이며 actual dq/dt 또는 force contract 인증이 아니다.

| 그룹 | v 대 q중앙차분 RMS | chart변환 대 q중앙차분 RMS | pose회전중앙차분 대 snapshotΩ RMS |
|---|---:|---:|---:|
| L_Thorax | 0.053412603 | 0.052773401 | 0.052745145 |
| L_Shoulder | 0.080269029 | 0.035123468 | 0.0343382 |
| L_Elbow | 0.055340049 | 0.041331936 | 0.03941833 |
| L_Wrist | 0.083612179 | 0.085515667 | 0.082515872 |
| R_Thorax | 0.10466271 | 0.10246771 | 0.10234315 |
| R_Shoulder | 0.4370608 | 0.41001412 | 0.40721067 |
| R_Elbow | 0.63035276 | 0.56992184 | 0.52917635 |
| R_Wrist | 0.2670399 | 0.23427321 | 0.22975251 |

R_Shoulder/R_Elbow의native v RMS는각각 `.260309/.330375rad/s`인데 pose-FD와snapshotΩ 오차는 `.407211/.529176rad/s`로크다. 이 독립FD는이번동작에서 실제시간미분을확증하는검사가되지못한다. 접촉급변·고주파운동·solver의위치보정·저장시점등은가능한설명이며분리측정하지않았다.

결론은동일snapshot의native v가자식좌표에서표현된상대각속도tangent와아주가깝다는것이다. qdot가정의`R_p J_left(Bq)Bv`는이snapshot기준과잘맞지않는다. torque설계에필요한power/virtual-work/effort duality, Jacobian곱, 다른asset/run/driveMode로의일반화는보류한다.

## 재현과 산출물

다음 명령은 JSON/XML을 읽는 오프라인 수학만 수행한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_velocity_coordinate_audit_v1/analysis.py
```

- [analysis.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_velocity_coordinate_audit_v1/analysis.py:1):입력/수식/표본/오차계산.
- [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_velocity_coordinate_audit_v1/summary.json):SHA·모든후보RMS/max·독립mask·FD·최대오차실제snapshot.
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_velocity_coordinate_audit_v1/README.md):이번읽기감사의해석범위와표.

analysis SHA256: `6faea466c1a7ed710f397a00321bd0800f5c28f9992bff12daba41c532c28e0a`.
