# HUMAN EFFORT damping 독립 최종 검수

요약 판정: 문제없음 — 최종 검수 PASS. Critical 없음 / 미해소 Warning 없음 / Suggestion 없음. 현재 네 조건의 구현·저장 원자료·분석·native 영상·최종 문서 검수를 완료했다.

- d0_off/d0_on/d1_off/d1_on 각각 1,200 physics steps, 155 raw state 표본(step0,1–4,8…1200), 300 commands, 151 camera frames, 9개 계약을 확인했다. 네 초기 native 상태·original PD는 exact다. 처음 오른팔12만 EFFORT/stiffness0/damping0 또는 retained이며 native properties readback과 다른69항 보존을 대조했다.
- 첫 ON 명령의 nonzero 요소는 R_Shoulder_z 하나(10.000001907348633Nm)이며 다른80요소는0이다. OFF 및 step4 이후 모든 명령은0이다. 첫 네 physics steps에 같은 command를 제출하고, step4 기록 후 original POSITION properties를 복원하는 코드/readback 계약을 확인했다. 복원 후 목표의 +0.05rad는 유지되며 초기 목표 복원 실험은 아니다.
- `analyze_human_effort_damping_probe.py:40–49`의 16개 차이 행을 전체81 q/velocity 및 shoulder3 좌표에서 독립 계산했다. Step4 Shoulder_z ON−OFF는 d0 0.0392422676086rad/3.84698648750782rad/s, d1 0.00228708982468rad/0.04414859227836rad/s다. 이는 scalar DOF 좌표/SDK 속도 차이며 body-relative 회전 벡터나 고립된 damping 계수 측정이 아니다. d0 OFF/ON은 기존 activation_v2의152개 full native state 표본을 각각 exact 재현했다.
- Native 입력 1,074/1,075/1,075/1,075개를 조건별 당시 목록으로 검수했다. 현재 1,071/1,072/1,073/1,073개와 source_before의 exact archived 3/3/2/2개로 모두 해결했으며 unresolved0이다. 분석 입력27개 before/after·현재 SHA와 분석기 AST Python3.8을 확인했다.
- 실제 영상8개의 SHA·ffprobe는 모두1280×720,151frames,30fps,5.033333초다. d1_on 종료 손 PNG를 직접 확인하고 README/CHANGED의 절대 링크·scalar 표·복원 목표·후속 별도 phase 범위를 대조했다.

해소된 Warning: README:3의 ‘12축10Nm’를 EFFORT12축 중 nonzero R_Shoulder_z 한 축으로 정정했고, ‘float32 readback’은 저장된 요청 command로 정정했다. 수정 전 README는 `doc_before_torque_wording_fix/README.md`에 보존됐다. 이번 raw에는 force getter 센서 측정이 없으며, 요청 command를 total force나 측정 drive torque라고 부르지 않는다.

확인 SHA256: runner `f10418e4f8c47ebec4c9e48f7fe60eac6cc91ddd5c5be4c4441e2afe6b3bfd2a`, wrapper `76c69cf9103c242efa46c253d9180f0a1be5e9ee0cf1ab7294b51d5efda06f44`, 분석기 `37ff5c2e77205d21774f5940f6565196f912efb23dc94ecd2139cd3364fc7bc0`, summary `1022a95a00c2fcb592dfc6dd7ab3c887c797d132d2f8511d9411d9d29944de43`.

읽기 전용 소스·저장 원자료·순수 NumPy 계산·AST·SHA·ffprobe·이미지 검수이며 native 초기화/physics 추가0회다. 초기 mass matrix는 read-only 참고이며 torque 계산에는 사용하지 않았다. 모든 관절의 damping 모델·source hybrid 동등성·지속 지지·연주/학습 성공·후속 Strike 결과 및 root의 최종 보존 감사는 이 판정에 포함하지 않는다. 이 review는 동결한다.
