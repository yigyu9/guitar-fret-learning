# OM 가슴·상완 초기 자세 최종 독립 검수

판정: **문제없음 — 완료된 세 진단과 보존·보고 범위를 승인한다.** Critical 0건, Warning 2건, Suggestion 0건. **지속되는 겨드랑이 지지 자세로 채택하지 않는 결론이 타당하다.** 리뷰어는 저장 자료·코드·그림을 읽기 전용 대조하고 순수 수치를 재계산했으며 추가 native·학습·원본 수정 없이 이 문서만 생성했다.

확인 범위:

- 새 source 거리·검색의 버전 이력과 위치 구역 정정을 앞선 사전 리뷰와 대조했다. 초기 몸통 추가 world 전경 4.5/11.25/18°는 누적 분절 방향 목표이며 native scalar 변화와 다르다. 근위 capsule subset·양의 source 간격은 실제 geometry 변경이나 cooked clearance 인증이 아니다. 기타 초기 뒤30mm 이동·왼 palm 동반 이동·머리 방향 보정·몸통/팔 변경을 함께 적용한 조합 시험이다.
- 세 actual 실행은 각각 1,200 physics/300 control로 완료됐다. 초기 setter는 각각 rigid-body/dof 두 호출이며 금지 API 0, 수동 strap force API 15,600회다. native39 body/G:body63개 및 물성·캐시·고정 root/하체·자유 기타·기존 단일 PD 제출 경로를 확인했다. 실행 중 손 부착·기타 pose 덮어쓰기·정책·학습을 추가한 증거는 없다. 전체 OFF/ON initial_values JSON은 exact이다.
- [분석 원자료 핀](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/analysis_inputs_before_v1.json:1) 2,791개와 각 native attempt의 입력 SHA(772/772/773개)는 현재 일치한다. 저장 trace에서 자기 초기 actor-root p/q 대비 이동·SO3 및 접촉 raw lambda를 독립 재계산했다.

| 조건 | 종료 이동 mm | 종료 SO3 ° | 최대 이동 mm | 최대 SO3 ° | 상완/Chest/Spine 양의 raw lambda 표본 |
|---|---:|---:|---:|---:|---|
| clear_reference | 113.500746 | 4.395057 | 113.504592 | 18.982564 | 0/0/0 (각300회) |
| lean18_back30 OFF | 114.259337 | 6.512226 | 114.259348 | 9.751527 | 0/1/0 (각300회) |
| 같은 초기값 PI+팔 rate ON | 65.717636 | 21.416177 | 82.446212 | 21.434274 | 0/1/7 (각300회) |

ON의 종료 이동 감소와 회전 증가를 함께 보고해야 한다. 기준/OFF의 후기 정착도 약11.4cm 초기 이동 이후의 상태다. 세 조건 모두 지속되는 상완–바디 접촉 지지를 입증하지 못한다. 60Hz 제어 전 query 표본의 양의 raw lambda는 측정 뉴턴 힘이나 모든 240Hz physics step의 비접촉 증명이 아니다.

- [PI 구현](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:34)의 실제 제어300행을 별도 EnvironmentContract로 재계산했다. 실제 q와 trace[k] 일치, dt=1/60 적분·body±0.05/arm±0.3rad clamp·head/finger 보정0·effective/native clip·요청 action과 다음 trace[k+1] float32 제출 목표가 통과했다. ON의 151개 strap 표본은 현재 계산/직전 physics 명령 시점을 구분하며 둘 다 0N이다. 표본 명령을 전체 적분 시계의 센서 힘이나 세 조건 공통 힘 비교로 확대하지 않는다.
- 최신 PNG3개를 직접 열어 18° 전경과 **기타 뒤30mm**의 단위 정정, 초기/0·2·5초 구도, overlay 없는 실제 측면 카메라와 현/strap 합성 전신 화면을 확인했다. v2 전신9패널의 이미지 영역은 원 native 프레임과 픽셀 exact이다. v1/v2 producer·입력 전후·출력 SHA가 일치하며 영상6개 원본/보관 복사 SHA도 동일하다. 각 영상151frame/30fps/5.033333초와 물리5초를 구분한다. 전체 영상 디코딩·반복 재현성은 인증하지 않았다.
- [초기 위치 정정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/README_CLARIFICATION_V1.md:3)은 원 기준 y=0.1217122748m와 뒤30mm 이동 후 OFF/ON y=0.0917122737m를 정확히 구분한다. 소비된 원 README와 `후방30°` 단위 오류 v1 그림은 보존됐고 [최신 산출물 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/ARTIFACT_INDEX.md:3)은 v2를 권위 정정본으로 안내한다.
- main4 완료 append의 원문 prefix·SHA를 확인했다. [봉인 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/seal_phase_v1.py:15)는 기록된 입력·이전 phase inventory/main 시작 snapshot·append chain·provenance·6영상·독립 리뷰 존재를 확인하고 새 최종 파일을 생성한다. 정적 논리에서 차단 오류는 발견하지 않았다. 실제 전체 보존 봉인 실행과 inventory는 이 리뷰 뒤 root가 확인할 범위다.

Critical: 없음.

Warning 2건:

- [README:55](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/README.md:55): HOLD leaf Markdown은 native 전 SHA 핀이 없다. controller Python/config의 실제 사전 핀과 구분해 현재 MD의 사후 SHA 확인으로만 보고해야 한다. README와 verification은 이 누락을 공개하며 현재 자료로 사전 증거를 복구했다고 주장하지 않는다.
- [README:31](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/README.md:31): ON은 PI와 arm target rate1→3rad/s를 함께 적용했다. 같은 초기값·물성 비교라도 PI 단독 인과 효과는 분리할 수 없다. 보고서는 이를 공개하고 이동 일부 감소를 종합 안정화 성공으로 채택하지 않아 적절하다.

Suggestion: 없음. 연주·왼손 철수·자연스러움의 정식 허용영역·실물 목재 물성·source/cooked 형상의 완전 관통 판정은 이번 검수 범위 밖이다.

검수 SHA256: verification `604904a4440f6b2c5e67b5f5edf9a56b34c92a550894109dc5fb98da988fcf95`; 분석기 `1a6b40084840a20beb00a53c29cc8a993a28a31c7ca0d071163abcf778631b1b`; 미실행 봉인 코드 `e7fb9691eed381c05554520b7f6c9583c55c4069dd5e6b7e38d1ede940c80cc8`.
