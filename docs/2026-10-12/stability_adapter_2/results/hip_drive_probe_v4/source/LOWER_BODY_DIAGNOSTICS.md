# 하체 초기 목표 유지 중 PD·solver 비교

2026-10-06. 사용자가 “하체 초기각 유지, PD·solver 안정성부터 진단”을 승인했다. 초기 기타 p/q·humanoid root·모든 초기 관절각·절대 L_A는 동일하게 유지한다. 하체 PD는 초기 목표를 유지하며 새로운 하체 action이나 state 덮어쓰기를 추가하지 않는다. 상지66·몸통9의 gain·목표는 바꾸지 않는다. 공용 XML/gain 원본은 보존한다.

## 짧은 비교와 근거

H0의 기존 조건은 0.046초에 왼쪽 hip의 큰 목표 이탈과 무릎 상승이 나타나고, 0.05초에 기타 넥–무릎 native 관통과 기타 이탈 급증이 함께 기록됐다. 초기 R_Hip–G:body와 발–ground 관통도 남아 있다. 이 근거만으로 PD 또는 solver를 단독 원인으로 확정하지 않는다.

240Hz·substeps1과 0.1초 길이를 유지하며 아래 다섯 진단 preset을 비교한다. 하체는 양쪽 Hip/Knee/Ankle/Toe의 기존 native PD gain만 조정하고 effort cap은 유지한다.

| preset | position/velocity solver 반복 | 하체 kp 배수 | 하체 kd 배수 |
|---|---:|---:|---:|
| baseline | 4/2 | 1 | 1 |
| solver16 | 16/8 | 1 | 1 |
| leg_pd01 | 4/2 | 0.1 | 0.1 |
| leg_kd01 | 4/2 | 1 | 0.1 |
| solver16_leg_kd01 | 16/8 | 1 | 0.1 |

이는 사용자가 승인한 진단·조정 안의 국소 비교이며 최종 채택이나 안정성 성공이 아니다. 기타 오차·속도, 몸통/하체 실제각 변화, 모델 limit 초과 측정, native 접촉과 전체 step 장력을 함께 비교한다. 초기 관통이 같은 후보를 손 지지 준비 완료로 판단하지 않는다.

## 계획 → 검증

- [x] preset 입력 및 native solver/하체 PD 연결 → 기본 preset baseline의 기존 240Hz trace exact 재현, 상지/몸통 gain·모든 초기 상태 동일 확인
- [x] 다섯 조건과 추가 아홉 조건 24 physics steps 실행 → 실제 하체 목표 이탈·모델 limit·무릎/넥 접촉·기타 오차·속도·장력 원시 기록
- [x] Sol 결과 분석 → 모든 후보에 자세/관통 문제가 남아 최종 채택하지 않음. 추가 유지 시간 대신 사용자 제안 초기 기타 Z 정적 비교로 진행
- [x] Luna 그림·누적 설명과 별도 change-reviewer 검수 — 두 PNG 독립 재생성 및 raw 수치 대조, 남은 Critical/Warning/Suggestion 없음

다섯 조건에서도 하체의 큰 목표 이탈이 남아, 추가로 gravity/ground/chair/guitar가 없는 별도 humanoid-only 교정 장면에서 같은 초기 상태·PD 목표를 확인한다. 외부 접촉 없이도 움직이면 native PD/관절 표현·모델 import를 우선 대조한다. 이 교정 장면은 최종 환경의 접촉·중력 제거를 허용하거나 안정성 후보로 채택하는 것이 아니다.

isolated drive hold/off 대조 뒤, 같은 240Hz 외부 업데이트에서 solver 내부 substeps=4/8을 추가 비교한다. 모든 PD gain/target·질량·armature·source 자산은 baseline과 동일하다. 작은 내부 dt로 수치 안정성이 개선되는지 확인한다. contact buffer는 `CC_LAST_SUBSTEP`이므로 substeps>1에서는 전체 4.167ms 구간의 모든 내부 접촉이나 t=0 gap을 수집한 것으로 해석하지 않는다.

substep 증가로도 큰 하체 목표 이탈이 남아, 하체만 EFFORT mode에서 동일한 초기 목표와 kp/kd/effort cap으로 `tau=clip(kp*(target-q)-kd*qdot)`를 매 physics step 적용하는 `leg_effort_pd`를 추가 대조한다. native POS와 분리해 실제 joint torque를 제출하며 상지/몸통은 기존 native POS를 유지한다. `leg_passive`는 하체 drive를 끈 원인 진단용 비교이며 최종 자세 유지 후보로 채택하지 않는다. 기타 복원 힘이나 강제 관절 상태 제출은 아니다.

기존 10m/s depenetration 속도 cap도 0.1m/s로 줄여 baseline/solver16/leg-effort 조건에 대조한다. 이는 solver의 관통 교정 속도 제한이며 초기 관통의 허용·정상화나 기타 pose 고정이 아니다. 같은 초기 배치가 여전히 관통으로 시작하면 안정성 후보로 승인하지 않는다.

마지막으로 동일한 gain/iteration/dt에서 native solver_type=0(PGS)를 baseline의1(TGS)과 대조한다. runtime getter로 실제 solver 설정을 확인한다. 기존 baseline은 변경하지 않는다.

PGS의 4/2 반복에서 하체 목표 이탈이 줄어, PGS의 16/8 반복도 추가 대조한다. 최저 기타 오차만으로 선택하지 않으며 하체 실제 자세·limit 초과·초기 관통을 함께 검토한다.

구현/설정은 `stability_adapter_2/`, 결과·로그·source snapshot은 고유 `docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/`에 저장한다. 이전 PhysX 진단과 batch 결과는 보존한다.

14조건 비교에서는 PGS4/2가 baseline보다 이탈을 줄였지만 0.1초 기타 최대 오차는
27.685mm/3.945°, 하체 raw 목표 편차는 17.744°이고 native scalar limit 초과가 남았다.
PGS16은 기타 약 17.582m·최종 속도 약 410.61m/s로 폭주했다. 유한값·입력 검사는
물리 안정성 검사와 다르다. isolated baseline hold/off의 접촉 없는 비교에서도 PD hold만
약 6.772° raw 이탈을 보였으므로 외부 접촉만을 단독 원인으로 확정하지 않는다.
현재 native 기본 solver와 하체 gain은 baseline 그대로이며 PGS를 최종 채택하지 않았다.

기타 Z 변경 확인 대기 중, [독립 hip fixture 진단](HIP_DRIVE_PROBE.md)을 수행한다.
3 hinge/nonzero 초기각에서 drive 종류에 따른 이탈이 재현돼, 승인된 PD 진단 범위에서
하체 native damping만 0으로 둔 TGS/PGS4/2를 두 조건으로 추가 비교한다. 상지66·몸통9
gain/목표·하체 stiffness/effort cap·실제 초기각·기타 p/q·L_A는 유지한다. 이는 damping을
최종 제거하는 결정이 아니며 기본 preset은 그대로다. 결과는 기존 14조건과 분리해 보존한다.
