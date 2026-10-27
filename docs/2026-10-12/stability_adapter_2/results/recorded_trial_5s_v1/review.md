# 실제 Gym 5초 기록 독립 검수

검수일: 2026-10-08. 수정 소유는 이 기록뿐이다.
원자료·구현·다른 작업자 파일을 변경하지 않았고 native 실행을 추가하지 않았다.

## 요약 판정

**문제없음.** Critical 없음. 제약 검사 범위, 초기화 집계, verifier 시간 guard, 역사 producer 사본의 Warning 네 건을 해소했다. 남은 actionable finding은 없다.

## 코드·저장 원자료

- target-only 상수 목표 runner와 실제 Gym camera helper를 검토했다. 초기81관절각·기타 world p/xyzw q·속도·PD·목표·절대 LA를 저장하며 JSONL을 매 기록 flush한다. 초기 settings와 float32 startup12 target은 이전 기준과 exact다. 240Hz 1200step, 8step마다30fps capture, t0/endpoint 포함151frame 스케줄이 정합한다.
- 정상 baseline은 생성 시도1/완료 constructor1,1200step·151frame·두1280×720/30fps MP4다. 저장된 ffprobe 메타데이터의151frame/5.033333초와 영상 SHA를 확인했다. 실제 물리 구간은0–5초이며 추가 .033333초 적분이나 과거 영상 반복이 아니다.
- baseline report9checks, 저장 검증8checks/790입력 SHA 및 처음24step의 이전 PD v2 scale1 states/trace/tasks/contacts/controls 5배열 exact를 확인했다. controls/contact1..1200 순서·300회/4step 업데이트·상수 target hold를 독립 대조했다. verifier:29–30에 같은 guard가 추가됐고 후처리 재실행은 native0이다. 이전 verifier·결과는 보존되며 refinement의 checks/counts/summary/videos/scope가 exact다.
- 별도 SIGTERM 검증은 생성 시도1/완료1,28step·4frame·두 partial MP4(.133333초), KeyboardInterrupt와 exit1/completed=false다. 별도8stopchecks 및 frame/video SHA가 정합하며 정상 baseline과 이어진 실행으로 표현하지 않는다.
- palm_up_proxy_passed는 source proxy의 위쪽 반구만 다루고 다른 자세 제약 인증을 배제한다. native_initialization_attempts와 완료 constructor 수를 구분하며 실패 시 실제 create_sim 호출 수를 단정하지 않는다. 기존 두 필드 Warning이 실행 전에 보완됐음을 확인했다.

## 최종 미디어·문서·보존

- 최종 contact sheet를 직접 확인했다. 실제 같은 실행의 전신/손 PNG를0·2.5·5초(step0/600/1200)로 배열하며 MuJoCo replay나 사후 pose 렌더가 아니다. source frame의 시각·SHA·1280×720 검증과9입력의 사전/사후 봉인, current producer/출력 SHA가 일치한다.
- README/CHANGED의 실제 파일·줄 링크와 workflow·메인 README:648/PLAN:1251·dated README·VISUAL §69/그림93을 대조했다. 실제 native/영상 생성/저장 PNG 합성과 제약·성공 범위를 구분한다. 다음 stiffness-only는3조건 각각5초1200step,3init3600step의 미실행 계획이며 첫24step 통계와 전체5초를 분리한다.
- before_verification_update producer·PNG는 당시 manifest와 exact다. before_layout_fix 기존 사본은 수정 후 working copy라는 한계를 남겼고, 별도 producer_before_layout_fix_exact의 실제 SHA `d7408a1c13be55133e4ec95333b2f6f48cbf2d662dc3cff9670d2918a8bff4f2`가 당시 manifest와 exact임을 확인했다. 기존 사본·PNG·manifest는 보존됐다. 복사 직후 manifest SHA 대조 후 편집한다는 workflow 보완도 정합한다.

## 검토한 source SHA

- run_recorded_trial.py: `6eeaf2476aacc68863e79e987b97a45d671abe2a8148c7743af19e28f1042351`
- gym_trial_recording.py: `f60897a175b88d8be620708f11e1fe52d61df73ef31c490fd1fda3cc8c43fb22`
- verify_recorded_trial.py: `1b55db48e6d19c75cac2d589ff8db282e94c98c65ccd2b0777996be06cde30be`
- make_recorded_trial_contact_sheet.py: `5f490b7593eaef597597af9db021ac1e10a33e9b65119930b5d499161f3771d3`

## 한계와 최종 상태

최대 기타 오차82.047438mm/10.831454°, 종료80.435305mm/10.563577°, 종료 추적점100.687667mm가 남았다. 녹화 완료·palm proxy 위반0은 기타 안정화·접촉 지지·전체 자세 제약 성공이 아니다. 그래픽 backend identity도 별도 확인하지 않았다. 이 검수 기록은 최종 동결한다.
