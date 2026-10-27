# 자연 오른팔 초기 자세 — 최종 독립 검수

요약 판정: **문제없음.** Critical 0 / Warning 0 / Suggestion 0. 기록·명령·자료 정리의 검수 승인이며 **자유 기타 유지 성공 또는 최종 연주 자세 채택의 승인이 아니다.** 새 물리 실행·학습·기존 파일 수정은 하지 않았다.

## 완료 결과와 해석

저장 trace에서 초기 대비 이동·SO3 회전을 재계산하고 240Hz endpoint 접촉을 직접 집계해 [analysis_v1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v1/verification.json:1) 및 [analysis_v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v2/verification.json:1)와 일치함을 확인했다.

| 완료 조건 | 바디 BB 중심 / actor-root 이동 | 초기 대비 SO3 | 전완 / Head / left 접촉 존재 |
|---|---:|---:|---:|
| native_v2 | 163.447 / 287.455mm | 62.320° | 1077 / 0 / 0 of 1200 |
| native_v3, 전완 world 목표 +12mm | 194.398 / 264.687mm | 76.809° | 179 / 812 / 0 of 1200 |

두 조건 모두 물리1200step·제어300회·5초를 완료했고 초기값 전체 JSON은 exact였다. 목표 world 점은 각 조건 안에서 고정, 목표 속도는0이었다. native_v3 Head 존재812표본 중 양의 raw lambda는795표본이며, 둘 다 힘 N이나 지지 기여를 뜻하지 않는다. body BB 중심은 source 외곽 bbox 기준이며 actor-root·질량중심과 구분한다. native_v3의 작은 2→5초 변화는 이미 이탈해 머리에 접촉한 뒤 정착한 결과다.

완료 검증의 `passed`는 기록·명령 검사 통과다. [결과 README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/README.md:15)는 두 조건 모두 기타 유지 실패로 구분한다. 초기 팔은 이전 교차 팔과 다른 외측 배치의 정성 참고로만 남기며, 단일 사진의 정확한 3D 복원·해부학적 자연스러움·연주 능력은 미인증이다. 높은 gain의 native_v1은 Jacobian 속도 gate로 약0.125초 뒤 중단한 실패 자료이며 전체5초 조건으로 취급하지 않는다.

## 코드·그림·보존

[runner V7](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v7.py:73)과 [V8](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v8.py:80)의 사전 검수에 이어 저장 결과를 대조했다. right12 human EFFORT와 other69 POSITION 목표, 토크 cap/owner window, 상태 불변/69 readback/Jacobian gate를 유지한다. 기타 직접 외력·부착·런타임 pose 덮어쓰기를 추가하지 않는다. 고정 world 점은 인간 actuator 목표이며 기타를 고정하지 않는다. 이탈 플래그는 토크 차단이 아닌 관측 래치다. 분석기는 저장 gravity 항을 사용하므로 전체 중력보상·Jacobian·힘/모멘트 기여의 독립 인증은 아니다.

실제 `initial_pose_pair.png`와 `native2_native3_timeline_comparison.png`를 열어 비교했다. 초기 비교의 다른 카메라/배치는 정성 참고로 한정하며, 2·5초 프레임의 큰 기타 회전과 실패 설명은 일치한다. 최신 [README_V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/README_V3.md:3)는 +12mm가 **전완** 목표임을 정정했고, [소문자 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/README_v1.md:1)가 최신본으로 연결된다. 이전 문서는 보존한다.

분석/native 입력 SHA는 [navigation_update_v1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/navigation_update_v1.json:1)의 세 before_snapshot 예외를 적용해 불일치0이었다. 세 append의 before/after SHA·원문 prefix 유지도 직접 확인했다. snapshot 이름 충돌과 별도 경로 복구 기록을 확인했다. artifact provenance V1/V2/V3의 입력·출력 SHA 및 완료 영상4개의 source/copy SHA가 일치했다. 현재 설명·색인의 로컬 파일/행 링크를 대조했다.

[seal_outputs_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/seal_outputs_v2.py:34)의 dict/list provenance 처리, 제한된 append 예외, 리뷰 존재/SHA, 배타적 최종 파일 생성 논리를 검토했고 Python 3.8 구문은 정상이다. schema 오류로 중단한 v1은 보존한다. **v2 봉인 실행과 이전7255개/이전 아카이브 전체 재검사는 root 후속 작업**이며, 예정 source_final/inventory/final_verification을 완료된 감사로 주장하지 않는다.

## 검수 SHA256

- 결과 README: `51c1dd7e54f2d3b9f5c23de63236c990e6aa6596895d48dd6684537c2fbeaa2c`
- artifact README_V3: `f21c315a4b55bbbae2ab762f23414b906163bf9d01f18c9c998492b7f249f208`
- analysis_v1 verification: `ca78948fac5fda4f2b782cbdcad4031c83870edd8f0cb2d6492b5c8f32b52eab`
- analysis_v2 verification: `f90c94fad79540fdb9f3beb8c910e445db08db7b51920b32f176fdaaef6166b7`
- seal v2: `38f6267409c666f9f9620e69dc9a50077c18f6deb4814f1827f7eff7cac7788b`

이 리뷰 파일만 새로 작성했다.
