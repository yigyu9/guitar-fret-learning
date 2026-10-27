# H0 native contact/strap 진단 v1

작성일: 2026-10-06. `h0_detailed`의 저장된 240 Hz native PhysX 상태·contact trace를 읽어, 초기 H0에서 관측된 contact field와 큰 기타 pose 변화의 시간 관계를 정리했다. 기존 batch H0의 24-step rollout과 별도의 contact 수집 실행을 비교했다. 부모가 검토 중인 하체 PD/solver 설정 실험의 결과는 여기에 합치지 않았다.

## 그림 11. 기타 오차·왼쪽 엉덩이 각도·native contact field 시계열

![240 Hz H0 기타 오차, 왼쪽 엉덩이 관절 변화, 선택 contact의 raw initialOverlap 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/images/physx_contact_v1_timeline.png)

위 패널은 기타 위치 오차(mm)와 회전 오차(deg), 가운데는 `L_Hip_x/y/z` 실제각에서 초기 PD target을 뺀 값(deg), 아래는 선택 contact의 `initialOverlap` raw signed 값(mm)이다. 아래 패널 점의 x 위치는 contact가 저장된 completed-step timestamp이며, raw `initialOverlap`은 그 physics step이 시작될 때의 field다. 세로 점선은 step 12, 0.05초다. 그림의 contact gap은 교정된 접촉 깊이나 clearance가 아니다.

## 그림 12. 저장된 두 상태에 놓은 원본 source collision geometry

![t=0과 step 11 저장 pose의 source collision geometry CPU 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/images/physx_contact_v1_source_geometry_t0_step11.png)

회색은 humanoid, 파랑은 기타의 원본 source collision geometry다. 빨강 형상과 검은 ×는 각 저장 pose에서 MuJoCo source-shape query가 음수 gap을 반환한 pair와 witness point를 나타낸다. t=0 그림의 1개·step 11 그림의 9개 음수 pair는 PhysX contact 목록이나 calibrated depth가 아니다. 그림은 `states.json`의 기록 pose에 source geometry를 재배치한 CPU 설명 그림으로, Isaac Gym renderer capture도 추가 physics replay도 아니다.

## 주요 관측값

- 24 physics step(0.1초) 동안 strap의 적용 장력 최대값은 0 N이었다. 이는 contact가 없었거나 collision response가 없었다는 뜻이 아니다. step 12의 두 `guitar/guitar × human/L_Knee` contact row는 raw `lambda=0`이지만, lambda 단위도 교정되지 않았다.
- 첫 기록 contact sample은 completed step 1, t=0.00416667초다. `guitar/G:body × human/R_Hip`의 `initialOverlap`은 −1.33114 mm다. 같은 sample에서 우측 ankle은 약 −9.69 mm, toe는 약 −8.89 mm를 기록했다.
- completed step 11, t=0.0458333초의 기타 위치/회전 오차는 5.183 mm/0.690°였다. 다음 step 12, t=0.05초에는 60.272 mm/6.319°로 크게 바뀌었다. step 12에서 `guitar/guitar × human/L_Knee` pair의 raw `initialOverlap` 두 값은 −35.9199 mm와 −34.2896 mm다. `guitar/guitar`는 두 neck mesh를 가진 기타 root body이며 별도 `G:body`와 구분된다. raw body label만으로 두 neck mesh를 개별 특정할 수 없다.
- step 11의 왼쪽 엉덩이 실제각은 초기 target 대비 x −60.09°, y +45.31°, z +45.01°였다. 같은 시점 왼쪽 무릎 world Z는 0.77163m였고 초기 0.48980m에서 달라졌다. step 24의 `L_Hip_y` 편차는 +107.8°다. humanoid root가 고정되어도 하체 관절·몸체가 고정되는 것은 아니다. 이 시간 관계만으로 기타 급변의 인과를 확정하지 않는다.

## Field 해석과 교정 범위

`contacts.json`의 원시 키는 `initialOverlap`, `minDist`, `lambda`다. `initialOverlap`은 native API의 raw signed feature gap이다. `minDist`는 요청한 target distance 값으로 측정 clearance가 아니다. `lambda`는 raw native field이며 force/impulse 단위 변환이나 교정이 없다. `initialOverlap` 음수값을 일반적인 실제 penetration depth로 환산하지 않는다.

최종 `calibration_substeps1.json`은 기타가 없는 네 isolated analytic box pair에서 첫 completed step을 기록했다. 분석 gap +10mm에서는 contact가 없었고, +0.05mm에서는 contact와 양수 raw gap, 0에서는 contact와 0, −1mm에서는 contact와 약 −1mm가 관측됐다. 이 결과는 box test에서 부호 동작을 확인하며 source mesh의 정확한 깊이나 실제 기타 contact를 보증하지 않는다. 최초 native enum API 시도 실패 기록과 기본 substeps 2의 다른 조건 calibration은 보존했으며 기타 결과의 수치 해석에는 사용하지 않았다.

H0 contact run의 초기 기타 목표 p/q, 초기 속도 0, held target과 humanoid root 검사는 통과했다. 보고된 strap 장력은 physics-step 범위 전체의 최대값이다. 별도 replay 비교에서 매 4 physics step마다 추출한 7개 상태가 이전 batch H0의 대응 7개 상태와 정확히 일치했다. 격리된 하체 controller/solver 실험 없이 접촉 변화 원인을 분리할 수 없다. 이번 분석에서 clearance, start gate, runtime feedback, torque, 성공 기준은 검증하지 않았다. 관련 test log에는 15개 검사가 통과한 것으로 기록됐다.

원자료: [detailed report](h0_detailed/report.json), [trace](h0_detailed/trace.json), [contacts](h0_detailed/contacts.json), [states](h0_detailed/states.json), [24-step baseline](h0/report.json), [source pose replay](source_replay.json), [one-substep box calibration](calibration_substeps1.json)·[calibration log](calibration_substeps1.log), [15-test log](tests.log). 보존된 시도: [초기 native enum 실패](native_contacts_failed.py.txt)·[로그](calibration.log), [기본 substeps 설정 calibration](calibration.json)·[retry log](calibration_retry.log), [H0 run log](h0_detailed.log), [source replay log](source_replay.log). 그림은 저장된 입력을 읽어 만들며 raw 파일은 수정하지 않는다.
