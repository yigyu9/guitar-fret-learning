# 실험 분석·산출물 작업 합의

## 목적과 작업 단위

이 문서는 `stability_adapter_2`에서 raw 실험 결과를 해석하고 산출물을 정리하는 역할 경계를 정한다. 메인 실험 목표와 물리 조건은 [README.md](README.md), 세부 계획과 사용자 합의를 따른다.

### 이번 문서 작업 체크리스트

- [x] 1단계 — 역할 합의와 작업 절차를 이 문서에 기록한다.
- [x] 2단계 — 별도 change-reviewer 검수 완료 — Critical/Warning/Suggestion 없음

## 역할 분담

### GPT-6.1 Sol (`gpt-6.1-sol`): 물리 해석과 후보 결정

GPT-6.1 Sol (`gpt-6.1-sol`)은 raw 실험 로그·측정 결과를 분석하고 후보의 품질을 평가한다. 다음 trial의 관절각과 절대 스트랩 rest length, 변경 방향을 구체적으로 결정하고 근거·제약·중단 조건·제어 결정을 제시한다. 구현의 물리적·수치적 정확성도 확인한다.

2026-10-07 사용자 변경 지침: 실험 목표 달성에 필요하다고 판단한 결정은 별도 승인 요청 없이 진행한다. 탐색 범위·제어권·gate·목표·모델·gain 변경은 적용 근거와 조건을 계획/로그에 먼저 기록하고 작은 단위로 검증한다. 기타 고정·강제 부착·지속 상태 덮어쓰기 금지와 원본 보존 원칙은 유지한다. Luna는 물리 후보 결정을 대신하거나 결과만 보고 다음 방향을 추론하지 않는다.

추가 사용자 조건: 오른발을 포함한 하체를 완전히 고정한다. 이후 실험은
`SelfCollisionEnvironment`(FixedLowerEnvironment 기반)와 별도 fixed-lower 자산을 사용한다.
현재 양손/팔–몸통 내부 충돌은 활성화하며 연결부/같은 손의 importer 제외는 유지한다.
기존 FixedLowerEnvironment 단독 경로는 self-collision OFF 재현용이다. 동적 하체 환경은 과거
재현용으로 보존한다. 자세를 매 step 덮어쓰거나 기타를 고정하는 구현으로 대체하지 않는다.
현재 하체 초기 모양은 이전 선택 실행의 H0를 유지하며, 하체 shape/ground 겹침 제거나
초기 발 모양 교정은 아직 수행하지 않았다. 자세/strap 비교마다 하체 조건을 명시한다.

### GPT-6 Luna (`gpt-6-luna`): 증거 기반 산출물

GPT-6 Luna (`gpt-6-luna`)는 raw 결과 파일과 GPT-6.1 Sol이 승인한 짧은 분석 brief를 읽는다. 실제 입력에서 표와 데이터 기반 그래프를 만들고, 출처가 확인되는 이미지·영상을 정리하며, 캡션과 누적 [VISUAL_REPORT.md](../docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md) 기록을 작성한다. 새 산출물은 [결과 디렉토리](../docs/2026-10-12/stability_adapter_2/) 아래 run별 새 경로에 저장하고, 파일 인덱스와 경로·줄 참조를 남긴다.

측정이 없는 값은 만들지 않는다. CPU 소스 형상 배치나 정적 proxy 그림을 실제 Isaac Gym/PhysX 렌더, 접촉 검증 또는 clearance 인증으로 설명하지 않는다. H0에서 측정한 값과 가상 설명점을 분명히 구별한다. 원자료와 그래프가 충돌하거나 brief에 없는 물리 해석이 필요하면 결론을 보류하고 GPT-6.1 Sol에게 되돌린다.

Luna는 가설·탐색 범위·보상·gate·controller·모델 자산·실험 설정을 수정하지 않는다. 산출물 생성은 설정 변경이나 새 물리 trial 실행을 뜻하지 않는다.

## 입력 brief

Sol은 각 산출물 작업에 다음 항목을 짧은 brief로 제공한다.

- trial ID와 비교 기준
- raw 입력 및 결과의 절대 경로
- 변경 불가한 기타 목표 p/q, 좌표계, frame, 단위
- 승인된 측정 결론과 다음 후보에 관한 해석 범위
- 요청 산출물 목록과 각 항목의 기대 캡션·용도
- 미검증 사항, 측정 한계, 알려진 실패 또는 충돌 증거
- Luna가 편집할 수 있는 파일 경로 목록

그림 brief에는 선/막대/음영별 **원자료 field → 표시 단위·좌표계** 대응도 명시한다.
캡션의 행렬 크기와 측정/도출값 구분은 실제 producer와 JSON으로 대조한다.
필요 변위 `p_goal-p_current`와 선형 예측항 `A(q_play-q_actual)`을 서로 바꿔 설명하지 않는다.
범위 안/밖 같은 관측 결과를 그림 생성의 통과 조건으로 삼아 결과를 숨기지 않는다.

그림 축 범위는 모든 실제 입력값을 포함해야 한다. 작은 비영 차이를 0으로 반올림해
표시하지 않으며 exact 일치 문구는 원자료 대조로 결정한다. 선이 겹쳐 보이는 것만으로
exact 일치를 주장하지 않는다. 변경 파일 인덱스는 실제 존재하는 파일과 현재 함수/제목의
줄 번호를 확인해 작성한다. 없는 analyzer나 이전 작업의 줄 번호를 복사하지 않는다.

필수 정보가 누락되거나 수치 출처가 확인되지 않으면 임의로 보충하지 않고 해당 항목을 보고서에 미확인으로 표시하거나 Sol에게 질문한다.

## 결과 흐름

1. 설정과 불변 조건을 run 기록에 명시한다.
2. 실험자는 로컬에서 trial을 실행하고 원시 로그·측정 결과를 새 run 디렉토리에 보존한다.
3. GPT-6.1 Sol이 결과를 분석하고 다음 후보의 방향·수치·제약을 정해 GPT-6 Luna brief를 승인한다.
4. GPT-6 Luna가 지정된 입력으로 표·그래프·이미지/영상·캡션과 누적 보고서·파일 인덱스를 만든다.
5. GPT-6.1 Sol이 물리·수치 내용을 확인한 뒤 별도 change-reviewer가 변경 파일을 검수한다.
6. 필요한 결정은 사용자 새 지침에 따라 자율적으로 진행하고 근거·변경 조건·검증 결과를 보고한다. 별도 승인 대기로 반복을 멈추지 않는다.

설정별 trial 실행 자체는 코드 변경이 없으면 매번 변경 파일 검수 대상으로 취급하지 않는다.

로컬 Python은 반복 trial 실행에 사용한다. trial마다 LLM 호출을 끼우지 않는다. GPT-6 Luna의 저비용 모델은 산출물 정리에 쓰며 물리 검증을 대신하지 않는다. 모델 호출·산출물 작업도 사용량을 소비하며 일정 비율의 절감은 보장하지 않는다. 하위 작업에 GPT-6 Luna를 지정하면 `gpt-6-luna`를 해당 하위 작업에만 override하고 간결한 승인 brief를 사용한다. 현재 parent 채팅 모델은 유지한다.

run별 관절각·절대 rest length 입력, local batch 실행과 hash 검증 중단·재개는 구현되어 있다. 자동 후보 탐색과 모델 자동 라우팅은 구현되어 있지 않다. 실행별 설정과 출력은 기존 고유 run 디렉토리·로그 체계에 보존한다.

## 보존할 물리·비교 조건

- 모든 후보에서 기타의 공용 목표 p/q, 좌표계와 단위를 동일하게 유지한다.
- humanoid root/Pelvis를 고정하고, 기타는 자유롭게 두며 중력과 실제 접촉으로 움직이게 한다.
- Torso/Spine/Chest 9관절은 초기 목표를 유지한다. 양쪽 Thorax부터 손가락까지 66관절 제어 연결을 유지한다.
- 기타 고정, 손과 기타의 강제 부착, 매 프레임 pose 덮어쓰기, 기타를 목표로 끌어당기는 인위적 힘을 사용하지 않는다.
- 기존 run·실패·로그를 덮어쓰거나 지우지 않는다. 각 실행과 파생 산출물은 새 run 경로에 둔다.
- CPU 원본 형상 query는 정적 source-shape proxy 진단이다. PhysX cooked 형상과 실제 접촉 대조 전에는 clearance 인증으로 표현하지 않는다.
- H0 결과값은 측정치로, 설명 목적의 virtual point는 가상점으로 명시한다.

## 다음 실무 단위

관절 초기각과 **절대** 스트랩 rest length를 run 입력으로 지정해 반복 trial에 전달하는 기능은 구현했다. 다음에는 측정 기준을 합의하고 초기 상태의 물리적 타당성·기타 유지 성능을 검증한다. 현재 구현을 물리적 성공이나 자동 탐색으로 해석하지 않으며 Luna 산출물 작업은 설정을 변경하지 않는다.

## 지속 반복 운영

사용자가 중단을 요청하거나 방향을 바꾸기 전까지, 승인된 탐색 범위와 조건 안에서 매 batch를 이어간다. 각 반복은 local runner 실행 → GPT-6.1 Sol의 raw 결과 분석과 다음 관절각·절대 스트랩 길이 방향 결정 → GPT-6 Luna의 산출물 생성 → Sol 확인 순서로 진행한다. 코드·설정·계획/매뉴얼·누적 보고서 등 변경 파일은 배치 단위로 별도 change-reviewer가 검수한다. 파일 변경 없는 trial 실행 자체마다 새로운 코드 검수를 요구하지는 않는다.
사용자의 중단 요청과 방향 변경은 즉시 반영한다. 필요한 중요한 결정도 별도 승인 요청 없이 진행하며 변경 근거와 검증 결과를 남긴다.
성공을 선언하려면 수치 기준, 반복 재현성, 물리 제약을 함께 검증해야 한다. 현재 거리·회전·유지 시간·PhysX 관통 허용 기준은 정식 검증 기준으로 확정되지 않았으므로 성공을 임의로 선언하지 않는다. 좋은 후보가 나오면 필요한 다음 검증/탐색을 자율적으로 판단하고 근거와 결과를 보고한다.
기존 도구의 고유 run 디렉토리·로그 보존과 run별 관절각/절대 길이 입력, 순차 batch runner 및 hash 검증 checkpoint 재개는 구현되어 있다. 팔24 PI/RATE_PI/PALM_RATE 목표 보정은 구현되어 있다. 자동 후보 탐색/선택, 모델 자동 라우팅, PhysX gate와 기타 p/q를 직접 유지하는 feedback은 아직 구현되지 않았다. 성공 판정 전 거리·회전·유지 시간·관통 기준과 반복 재현성을 합의·검증한다.
실행이 멈춰도 마지막 완료 run과 다음에 사용할 후보 설정을 기록해 그 지점부터 이어간다. 서로 다른 trial 사이의 측정 오차를 연속된 한 번의 실행처럼 연결하지 않는다.
이 운영 규칙은 반복 실행 절차를 정한다. 무기한 백그라운드 서비스가 이미 실행 중이라는 뜻은 아니다.

## 저장 자료·산출물 입력 봉인

분석·그림 producer는 직접 읽는 원자료뿐 아니라 재사용 helper와 보존 판정에 읽는
inventory도 실행 시작 전에 입력 SHA 목록에 포함한다. 실행 후 같은 목록을 다시
대조한다. 표시 시점의 last_applied 값이 직전 step 적용값이면 캡션에 그 시점을
명시한다. 후처리 환경의 MUJOCO_GL 등 실제 import 조건도 재현 명령에 기록한다.
producer 보완 후 재생성할 때는 직전 producer·결과·manifest를 보존하고, native
재실행 없이 저장 자료에서 수정한 단계와 물리 실행 집계를 구분한다.

## 2026-10-08 사용자 변경: 각 실험의 초기 값과5초 실제 영상

앞으로 실험별 초기 값과 그 값으로 시작한 실제 Isaac Gym 환경의0~5초 경과를 저장한다.
새 상수 목표 비교의 기본 진입점은 `python -m stability_adapter_2.run_recorded_trial`이다.
초기 설정/실제81관절각/기타 world p·xyzw q/속도/PD/절대 strap rest length와
전신·손 근접30fps 영상을 각각 저장한다. t0와5초 끝 장면을 포함해 영상은 약5.033초다.
새 feedback runner에도 gym_trial_recording helper를 연결해 같은 기록을 남긴다.
기존 frozen runner/batch와 과거 산출물은 수정하지 않는다. 짧은 별도 진단을 사용할 때도
동일 실험 조건의5초 녹화를 함께 남긴다. 진단과 녹화가 별도 실행이면 각각 집계한다.
제약 위반·자세 붕괴를 기록하고 실제 경과를 숨기지 않는다. 물리/API 오류·사용자 중단은
partial 기록과 확보된 영상으로 남기고 정상5초 완료로 표시하지 않는다.
[구현·검증 계획](FIVE_SECOND_RECORDING_PLAN.md)을 따른다.

산출물 producer를 수정하기 전 보존본을 복사한 즉시 해당 실행 manifest의
producer SHA와 대조한다. exact 검증이 통과하기 전에는 원 producer를 편집하지 않는다.
수정 후 작업본과 실제 실행 원문은 구분해 기록하며, 원문이 없으면 복원 전까지
당시 실행 소스라고 설명하지 않는다.


## 2026-10-08 사용자 변경: 영상에 실제 스트랩 경로 필수 표시

앞으로 새 trial 결과영상의 기본녹화는 StrapTrialRecording이다. 매프레임 실제13route world지점을 camera view/projection으로투영하고 native depth로 실선/가려진옅은점선을구분한다. 화면에는절대LA를표시한다. 원nativePNG와표시PNG를각각보존하고route/camera행렬/SHA를capture.json에남긴다. 천너비·처짐·충돌mesh가추가된모델로설명하지않는다. 기타/인체 상태·제어목표·힘·gain은그대로다.

새상수trial 진입점은 `python -m stability_adapter_2.run_strap_recorded_trial --trial <입력절대경로> --out <새출력절대경로>`이다. Source/FK근접진단은run_strap_recorded_diagnostic에봉인proposal을전달한다. 새feedback/목표비교runner는 `from .strap_trial_recording import StrapTrialRecording`으로같은녹화helper를연결한다. 기존frozen run_recorded_trial/gym_trial_recording/camera/과거영상은재현용으로수정없이보존한다.

[표시구현계획](/home/ajou/yigyu/3/stability_adapter_2/STRAP_VIDEO_VISUALIZATION_PLAN.md:1)과 [실제5초/초기값·이미지설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/README.md:1)을따른다. 같은입력 actual1회/1200step·두151frame영상과원자료5배열/rawPNG302개exact를관측했다. 일반상수새entry는문법/loop AST검사이며이번actual은근접진단entry에서sharedhelper를검증한것이다. 이것은기타안정화성공이아니며뒤실험을계속한다.
