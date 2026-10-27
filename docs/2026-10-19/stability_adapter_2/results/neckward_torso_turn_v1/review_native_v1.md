# 넥 방향 회전·전경 감소 native 검수

판정: **문제없음 — 한 초기값의 정지·±5° 팔꿈치 한 주기 진단 범위.** Critical 0 / Warning 2 / Suggestion 0. 저장 원자료/코드의 CPU 수식·해시를 독립 대조했으며 신규 native·학습은 실행하지 않았다. 최종 그림·문서·전체 보존 봉인은 후속 범위다.

## 기록·제어와 진입 조건

두 완료 시험은 각각5초/1200 physics/300 control·151프레임이다. 1200개씩 목표 sinusoid·해석적 속도·상완 task+기록 gravity+posture 합산/모델 clip을 재계산했다. 합산 최대 차이8.89e−16Nm/float32 제출 exact, 전완 요청힘0, 실제 상완 J child 열0, other69 POSITION readback·상태 guard/물리당 단일 actor 노력 제출이 맞다. 입력888/889개 현재 SHA 불일치0, native 영상4개 SHA 일치. 전체 gravity/Jacobian의 독립 물리 인증은 하지 않았다.

[정지 진입 코드:11](/home/ajou/yigyu/3/stability_adapter_2/prepare_neckward_torso_motion_v1.py:11)의 조건을 raw trace/endpoint와 실제 방향 자료로 재계산하여 true를 확인했다. 정지 BB 중심3.944391mm/SO3 1.472679°, 2→2.5초0.081890mm/0.045313°, 마지막0.5초 상완120/120 및 Head/왼팔·손/오른 원위팔·손0 조건을 통과했다. 이전 대비 heading 증가≥5°/전경 감소≥3°도 통과한다. motion config는 같은 후보 path/SHA에 ±5° 진폭·정지/자세 근거 경로/SHA만 추가했다.

## 실제 몸통 방향

[자세 producer:14](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/measure_torso_posture_v2.py:14)는 원 Chest→Neck 참고축과 직교 frontal 축을 실제 Chest 회전으로 운반한다. 이전 및 새 두 조건 모든 행의 world 기준 경사·heading을 재계산해 최대1.5e−14° 차이로 맞았다.

| 5초 조건 | +Y 방향 전경 | +Y→−X heading | 전체 수직 대비 경사 | world+X 측경 |
|---|---:|---:|---:|---:|
| 이전 안정 정지 | 53.575657° | 12.643226° | 53.590252° | +2.534570° |
| 새 정지 | 48.347770° | 22.198890° | 48.762687° | −10.951170° |
| 새 ±5° 운동 | 48.350001° | 22.198030° | 48.764074° | −10.941012° |

새 정지의 전경5.227887° 감소·heading9.555664° 증가를 지지한다. 실제 전경이2°/heading이12°라는 뜻은 아니다. source에서 yaw 전에 적용한 바디 쪽6° 목표 성분도 실제 절대 world 측경6° 유지와 다르다. 이전/새 자세는 초기 상태·오른팔·기타 위치가 달라서 개별 변경의 인과 효과를 분리한 비교는 아니다.

## ±5° 같은 초기값 비교와 실제 접촉

[동시점 비교:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/compare_elbow_motion_v1.py:15)의 전체 native 초기 state·2.5초까지 trace exact를 직접 확인했다. 실제 moving scalar 왕복 약10.083668°와 moving−static 증분 왕복10.099138°를 구분한다. 증분 응답 상관0.999948434/RMSE0.048544°, absolute q−target RMSE0.131056°이다. 같은 시각 정지 대비 기타 BB 중심 최대0.099629mm/SO3 0.053043°를 원자료로 재현했다. 운동 최종 초기 대비 BB 중심3.876188mm/SO3 1.454971°는 별도 지표다.

두 시험 모두 상완1169/오른 Hip1193/Head·왼팔·손·오른 원위팔·손0 표본이다. [공간 판정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/contact_region_v1.json:1)을 raw localPos+offset/world/G 좌표와 캡슐 투영으로 재계산했다. strict 근위35%·위 볼록 영역 접촉은 두 조건0/1200이며 근위30%도0이다. 축 fraction 최소 정지0.353796/운동0.353853, feature pair 최대약1.24e−7m/반지름 차이최대0.364039mm와 일치한다. 이전 조건의35% 지정영역1171표본은 새 조건에서 유지되지 않았다.

Warning 1 — [지역·제어 해석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/contact_region_v1.json:1): 상완 전체 접촉·Hip 접촉으로 유지되는 짧은 진단과 strict 근위 구간/해부학적 겨드랑이 성공을 구분한다. 요청힘·raw lambda는 측정 접촉힘/하중 비중이 아니며240Hz endpoint는 연속 solver 모든 접촉 인증이 아니다. 새 접촉 위치로 이동한 변화까지 공개해야 한다.

Warning 2 — [비교 범위:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/compare_elbow_motion_v1.py:19): R_Elbow_y scalar 한 DOF·0.5Hz 한 주기·동일 초기값에서 작은 영향이 관측됐다. world축 운동/전체 팔 움직임·반복/장시간·fret/strike 성능으로 일반화하지 않는다. 증분/절대 추종 및 초기 대비/같은 시각 정지 대비 변화는 다르다. 모델 참고축의 절대 경사와 추가 source 목표각도 구분한다.

핵심 SHA256: comparison `ca6b9ec6276433956c0e36c7a3142db0583fa28f9bd9693f1a8c5929c3524e3c`; posture_v2 `1e7a7afd4a53a68e3d10c71acba0102ec08d23b38ef4a1a608837b3724803ebc`; contact_region `2120ca1975e6cc79561d12d0d39a89026ecb3c74e46b538df89d5207ad2d779e`.
