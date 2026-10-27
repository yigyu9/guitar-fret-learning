# 몸 쪽 접근 다섯 조건 — 실제 실행 검수

요약 판정: **문제없음 — 기록·명령·진단 계산 범위**. Critical 0 / Warning 3 / Suggestion 0. **사용자 목표인 후기 Thorax–상완 두 블록 접촉 회복은 실패했다.** source 다섯 후보 수락과 실제 유지 결과를 구분하며 추가 팔꿈치 시험을 생략하고 이전 waist 기준을 유지하는 결론이 타당하다.

## 실제 결과

| 접근 | 물리 실행 | 종료 바디 중심 변화 | 최대 바디 중심 변화 | 종료/최대 SO3 |
|---|---|---:|---:|---:|
| 3mm | 5초·1,200 step·300 tick 완료 | 12.053817mm | 12.620936mm | 5.816941° / 6.718179° |
| 6mm | 5초·1,200 step·300 tick 완료 | 11.879116mm | 12.180253mm | 5.879922° / 6.671118° |
| 10mm | 5초·1,200 step·300 tick 완료 | 16.070859mm | 17.550223mm | 6.295500° / 8.231304° |
| 20mm | 1.116667초·268 step·67 tick 보호 중단 | 75.384472mm | 75.384472mm | 30.637758° / 30.637758° |
| 30mm | 0.85초·204 step·51 tick 보호 중단 | 101.804566mm | 101.804566mm | 34.354523° / 34.354523° |

raw trace에서 초기 대비 바디 bounding-box 중심 `[0,−0.4,−0.055937985]m`의 변위와 정규화 SO3를 재계산해 [완료 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analysis_static_v2/analysis.json:1) 및 [부분 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/partial_analysis_v2.json:1)과 일치함을 확인했다. 총 다섯 native 실행은 4,072 physics step/1,018 control tick이며, 두 부분 중단을 5초 완료로 세지 않는다.

## 원자료·수식 대조

- 다섯 실행의 입력 불변/금지 호출 없음 및 초기 G39·root/하체·finger42·PD·질량·모델·q_ref·FK·actual pose source audit gate가 모두 통과했다. 최대 native 초기 FK 위치 오차는 3.04e−7m였다. source audit는 cooked 형상 인증이 아니다.
- 완료 세 실행의 3,600개 명령 행에서 점 요청 K/D와 cap, 저장 Jᵀ 토크, 이전 task 감산/교체, 몸통 COM Jacobian 중력보상·PD, 모델 clip, 최종 33 EFFORT/48 POSITION 소유권과 단일 제출 벡터/cadence를 재계산했다. 몸통 요청 오차는 최대 7.11e−15Nm, 저장 J*qdot의 점 속도 오차는 최대 0.000330m/s 이하였다. 이는 저장된 Jacobian 및 최종 합산 벡터 감사이며 왼팔 모든 내부 항이나 native Jacobian 자체를 새로 인증한 것은 아니다. [명령 검사 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:53)
- 완료 세 조건의 실제 Hip contact localPos를 endpoint body pose→world→기타 root frame으로 직접 변환했다. waist presence/positive는 각각 1,198/1,200, 마지막 120개도 모두 해당한다. 후기 Thorax는 세 조건 모두 0, 상완은 모두 120이다. 왼손 손가락 접촉이 계속 있고 전완·오른손·머리 접촉은 0이다. [영역 분류 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:25)
- 20/30mm 최종 root 변위는 200.071323/208.280882mm로 **root 20cm guard**를 넘었다. 회전은 둘 다 35° 미만이다. 바디 중심 변위와 root guard를 혼동하지 않는다. 초기 검사 실패나 qdot guard 실패로 설명하지 않는다. 부분 영상은 각각 35frame/1.166667초 및 27frame/0.9초이며 물리 시간과 다르다. 원본 영상 SHA는 부분 분석 기록과 일치한다.
- 완료 분석의 직접 raw 입력 SHA와 부분 분석 입력 1,723개의 현재 SHA를 대조했다. 새 물리·학습·정책 실행은 없었다. 최종 그림/문서와 과거 전체 inventory·봉인은 이 보고서의 범위 밖이다.

## Warning

1. [완료 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analysis_static_v2/analysis.json:1)의 통과는 명령·기록 검증이다. 후기 Thorax 0, 왼손 middle2/index2/pinky3 접촉이므로 두 블록 지속 지지·무왼손·수동 집게·접촉력/분담률·장기/연주 성공을 주장하지 않는다. 초기 이동과 IK 각도 변경도 함께 있어 접근 하나의 인과효과로 단정할 수 없다.
2. [부분 분석 scope](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analyze_partial_v2.py:43)는 60Hz trace와 중단 endpoint의 진단이며 전체 상완 contact를 근위 영역 인증으로 확대하지 않는다. raw λ>0은 N 단위 힘이 아니고 240Hz 표본은 solver 내부 전 시간 인증이 아니다.
3. 분석기 실패 두 건은 native 실패와 별개다. [baseline SHA 거절](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analysis_3mm_v1_failure.json:1)은 이전 main PLAN의 승인 append 때문이고, [partial V1 실패](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/partial_analysis_v1_failure.json:1)는 `native_*` glob에 로그 파일이 섞인 NotADirectoryError다. 후자는 사전 검토에서 놓쳤으나 V2의 디렉터리 필터·읽은 report5 핀·새 배타 출력으로 해결됐다. 원본 실패 코드/기록은 보존한다. 이전 mesh 핀 누락은 [새 연결 검수의 정확한 map 정정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/review_native_preflight_v1.md:1)을 유지하며 소급 before 인증하지 않는다.

## 확인 SHA-256

- 완료 canonical 분석: `3a6dcae25c57c43a07b50404b47f77dccd22c11d4d9b6385a0119ea59391a6d4`
- 완료 command audit: `bd4f369803fc5848e088dd2efc74404e25f899feb2ca8808f993028b8de5dc24`
- 부분 canonical 분석 V2: `de01cb8b0c1334a3c03f96fe710bcf37cbe8f0158c2633382054bbf1ebd37db1`
- 부분 producer V2: `793d0146f324c6a0afd383bfadbd88c919a4c14a473d2c238631309b16f6a0c5`

소유한 새 리뷰만 작성했고 기존 소비 소스·원자료·리뷰는 변경하지 않았다.
