# 손바닥 옆면 우선 자세의 실제 Isaac Gym 5초 진단

새 초기 자세로 실제1회·1200step(240Hz)·0~5초를 실행했다. 엄지 후면 근처 접촉 기록은 늘었지만 지정한 손바닥 옆면 접촉은 여전히 없고 기타 최대 이동·회전도 조금 증가했다. 따라서 새 자세를 안정화 기준으로 채택하지 않는다. Source 지지 기준 미달을 보존한 근접 진단이다.

## 초기값과 스트랩이 보이는 실제 영상

[81 초기각·기타 p/q·PD·물성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/initial_values.json), [실행 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json), [거절 원본 snapshot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/completed_source_row_snapshot.json)을 보존했다. LA1.1018469719600776m, 초기 경로1.0858332748277348m로 여유16.013697mm다. 왼손33 초기각만 바꾸고 나머지48 초기각·기존 절대81목표·PD gain/solver는 유지했다. Root와 하체는 전용 asset에서 물리 고정, 몸통9 목표는 유지하되 실제 움직임을 측정한다. 양쪽66 주요 제어권·selfcollisionON·자유 기타·수동 strap 조건은 같다.

![초기 전신과 실제 스트랩 경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/frames/whole_body/00000.png)

실제 Gym camera 이미지다. 주황 실선은 depth 기준 보이는 실제 경로, 옅은 점선은 몸/기타에 가려진 구간이다. 13지점/12구간 route를 표시하며 선 두께는 표시용 픽셀이다. 천의 폭·처짐·추가 collision mesh를 뜻하지 않는다. 가려진 경로는 표면 접촉 인증이 아니다.

![초기 왼손·오른손과 넥](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/frames/hands/00000.png)

녹색 왼손·자홍색 오른손·파란 기타의 실제 초기 장면이다. 손바닥 source 유한 패치 거리 상한은0.421670mm이고 엄지는9.150457mm다. 렌더의 외관 또는 source 거리만으로 native 손바닥 접촉을 선언하지 않는다.

![5초 손과 스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/frames/hands/00150.png)

종료 장면이며 손바닥 요청 패치 근접 접촉은 관측되지 않았다. 같은 촬영 시간의 route를 매 프레임 갱신했고 query/render 전후 human/guitar 상태가 유지됨을 검사했다.

![실제 Isaac Gym 전신·스트랩 0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/whole_body.mp4)

![실제 Isaac Gym 손·스트랩 0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/hands.mp4)

두 영상은 각151frame/30fps, 초기0초와 종료5초를 포함하므로 인코딩 길이5.033333초다. Raw camera PNG도 별도 raw 폴더에 보존했다. Native CPU PhysX 실행이며 CUDA/context/visual geometry 경고 로그를 그대로 남겼다. Mujoco 렌더가 아니다.

## 실제 기타 변화와 손바닥 간격

| 조건 | 최대 이동 | 최대 회전 | 종료 이동 | 종료 회전 |
|---|---:|---:|---:|---:|
| 직전 저장 original_targets | 25.779645mm | 7.800837° | 22.034643mm | 7.092339° |
| 새 손바닥 우선 초기 자세 | 26.091583mm | 7.937143° | 22.095629mm | 7.117855° |

![기타 위치·회전 오차와 손바닥 source 간격](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/artifacts/actual_G_and_palm_gap.png)

위 두 패널은 world 기타 p/q 오차이며 파랑은 기존 저장 실행, 주황은 이번 새 실제5초다. 아래는10개 시점의 손바닥 source hull–유한 patch 간격 상한이다. Witness 하한과 상한 차이는 매우 작아 그림에서 겹친다. 점 사이 선은 관측 시점 연결이며 연속 거리 측정이 아니다. 빨간선은 첫 palm body 양λ 기록(step125/0.520833초)이다. Source 간격은 cooked clearance가 아니다.

Native SDK feature4304행을 actual post-step body pose와 대조했다. 양λ와 유한 패치 내부 투영·법선2mm 근접·두 local point 재구성 잔차1µm 이하를 함께 적용했다. 엄지 후면 근접 고유793step/last1200, 중지 전면1052/last1200, 검지34/last116·약지1/last43이다. 손바닥 요청 옆면은0이다. Palm body 자체의 양λ는14개 고유step/last139이며 요청 패치와23.270465~23.724753mm 떨어졌다. Body명/λ/source 근접은 해부학적 pad·실제 cooked 면·힘N·연속 지지 인증이 아니다. 양손 사이 contact 고유step0, palmar 상향 proxy 위반0이다.

## 몸통과 팔 초기 이동 분리

![Chest 자세와 팔 chain의 world XYZ 기여](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/artifacts/early_Chest_arm_vectors.png)

실제 저장 pose에서 손바닥 source anchor의 world 변위를 Chest pose 변화와 Chest 기준 팔 chain 변화로 정확히 분해했다. 축별 두 vector의 합이 실제 점 변위와 같음을 검사했다. Vector norm은 합산할 수 없고, 이것은 gain 변경의 인과 실험이 아니다.

초기 source 간격0.421670mm는 step4(0.016667초)에0.151185mm로 더 가까워졌다가0.1초5.792735mm가 됐다. 그러나 초기 근접 시점의 SDK palm 접촉은 없었다.0.1초 Chest 기여 norm15.019088mm·팔 기여11.579934mm,5초73.186215/41.464612mm로 서로 상쇄하는 성분이 있다. 실제 몸통 최대 좌표 변화4.231250°다. 몸통 목표 유지와 실제 정지는 구분한다. 회전값은 native DOF 좌표 변화이며 bone SO(3) 회전각으로 해석하지 않는다.

Passive strap 법칙 최대 장력23.500679N·종료0.366221N,1200step 재계산 오차0이다. 기타에 별도의 목표 복원 힘이나 pose overwrite를 넣지 않았다.

## 검증·후속 단위

[원자료 재계산6검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/analysis.json), [SDK feature 분석3검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native_feature_analysis.json), [초기 이동10시점/4검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/early_motion_audit.json), [native 실행/녹화 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/report.json)에 기록했다. Python3.8 문법과 원본 SHA/이전 산출물 보존을 최종 감사한다. 이미 성공한 검색/5초를 다시 실행하지 않았다.

[다음 계획](/home/ajou/yigyu/3/stability_adapter_2/TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md:1)은 미실행이다. 먼저 같은 초기값의 native collision camera·shape mapping을 확인하고, 몸통9 stiffness×2/damping×√2 한5초만 기존 저장 gain과 비교한다. 초기q/PD목표·팔/손gain·LA·기타p/q를 유지하며 결과가 개선될 때만 채택한다. 상체 물리고정이나 지속 state overwrite가 아니다. 이후 초기 p/q 복원·유지 제어와 연주권한 결합을 설계한다.

Root가 산출물과 실제 PNG QA를 수행했다. Luna/최종 change-reviewer 호출은 agent thread limit으로 실행 불가하여 독립 검수는 보류했다. [변경 파일 절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/CHANGED_FILES.md:1)을 따른다. 기타 초기복원·세 면 지속지지·연주 안정화의 전체 목표는 계속 진행한다.
