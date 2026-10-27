# seed2_response_locality_v1 독립 검수

검수일: 2026-10-08. 신규 준비·runner·analyzer·산출물과 해당 결과 문서만 검수했다.
코드·원자료·기존 동결 리뷰는 수정하지 않았으며 검수 과정의 native 초기화·physics 실행은 0회다.

## 요약 판정
문제없음. Critical 없음, 미해소 Warning 없음, 추가 Suggestion 없음. 신규 실행은 3초기화/3600step이며 과거 기준·positive probe·full heldout은 저장 참조다. negative Shoulder_y의 소폭 개선은 관측 결과이며 안정성·지지 성공이나 새 제어 채택을 뜻하지 않는다.

## 코드·저장 원자료·수학

- 세 조건의 초기 81q·전체 초기 상태·PD·기타 목표·고정 LA·solver 공통 조건, 실제 float32 제출 목표와 4step 갱신/constant-target 기록을 대조했다. 이전 일반 runner의 중복 축 한계는 신규 exact ordered six-axis guard로 좁혔다.
- 신규 각 1201상태/1200제어·접촉 기록, 두 카메라 각 151프레임과 저장 참조 경계를 확인했다. 분석 8계약과 입력 SHA 7780개가 현재 파일과 일치했다. step 0–24의 기타 상태 exact는 25관측/24physics step의 관측 boolean이다.
- world 위치·SO(3) 오차, actual float32 양/음 delta의 forward/backward/central 6×2 secant 및 비대칭 zero interpolation을 독립 재계산했다. secant는 유한 응답 근사이며 순간 미분이나 runtime Jacobian 인증이 아니다.
- half/full 실제 delta의 alpha=0.500009933989, 축별 비율·비공선 잔차, old-J 예측과 alpha 응답 보간을 대조했다. last-1s 잔차는 각각 0.481436mm/0.084446° 및 0.104851mm/0.014643°다. 회전 잔차는 world rotvec 벡터 차이 norm이다.
- 이전 상태의 route 위치·속도로 재계산한 3600구간 cable law 오차는 0N이다. 이는 적용 법칙 scalar 대조이며 native 힘 센서 인증이 아니다.
- 모든 신규 조건의 R_Hip 양의 raw lambda는 고유 1200step에 기록됐고 RH–기타 행은 없었다. LH:palm 마지막 양의 기록은 118/124/123, 마지막 전체 행은 134/133/134로 구분했다. named body·raw lambda는 면별 접촉·Newton 힘·substep 연속 지지를 증명하지 않는다.

## 최종 미디어·문서와 수정 이력

- canonical 곡선과 실제 Gym 손 카메라 PNG를 직접 확인했다. Wrist_z 대응, 저장 참조와 신규 조건의 구분, 전체 0–5초 축과 단위, 신규 세 조건 step 0/1200 프레임 표시가 맞다. 입력 21개 전후 SHA 및 출력 두 SHA를 대조했다.
- Warning 해소: `make_seed2_locality_artifacts.py:116–120`은 exactness 관측 값의 True를 요구하지 않고 key/bool 형식만 검사해 False도 허용한다. 편집 전 성공 producer·산출물은 v2 archive에 보존됐고 현재 두 PNG는 당시 출력과 byte-identical이다.
- 첫 schema 실패 v1의 producer·로그 SHA와 metadata, 첫 성공이지만 True gate가 있던 v2, 현재 canonical의 순서를 구분했다. 이 후처리에는 추가 native 실행이 없다.
- README:44, IMPLEMENTATION_FILES:17, VISUAL_REPORT:1399의 최종 이력·범위 교정을 확인했다. 표의 positive Wrist_z 값, 두 축 6×2 표현, 25관측과 고유 contact step 구분 및 실제 링크 앵커를 확인했다.
- 다음 `SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md`는 미실행 계획이다. last-1s backward 응답 방향과 임시 0.1m 회전 lever, 잔차 [-0.016,0]rad/속도 0.008rad/s의 단위·부호는 일관되지만 runtime 효능은 아직 검증되지 않았다.

## 검수한 정확한 SHA-256

- prepare: `3376f787ff616e794493e3c301aab7d96239a6d3bd15843d79d2204f80e5c517`
- runner: `bca97f79220933e01d12369ad7061f4438ec005a7b628a76a8111116fb8cdf5d`
- analyzer: `dee62999374881c76adbc1993659c616a5479a2113eb92cd863d68a512da7f62`
- plotter: `a43acd0aabdfe46308c31b0fda24c90280724e6412a8f52b0ce51556f7a9b4f4`
- analysis.json: `ba27a0afed1c520373a836de58a472c5838cc877a58ff8bb01b7b301ac4dea18`
- artifact manifest: `78f8b6ac128350d7b8fe6887d261e6fa44e82b9834d2d9ac69b2c742de0f22b9`

## 남은 한계·동결

scalar DOF 좌표는 whole-joint SO(3) 각도가 아니다. 목표 대조는 저장된 Python 제출 기록 범위이며 이 단계에서 SDK 목표 getter를 새로 조회하지 않았다. 초기 여섯 source 접근 통합 조건은 미달이며 기타 이탈·지지 미성공이 남았다. 향후 feedback은 별도 실행·검증 대상이다.
이 리뷰는 동결 가능하다. 최종 검증·inventory·source manifest 생성과 상태 체크 갱신은 root의 후속 봉인 작업이며 여기서 완료를 인증하지 않는다.
