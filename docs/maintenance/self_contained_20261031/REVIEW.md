# 독립 변경 검수 — 2026-10-31

요약 판정: **문제없음**. 변경 코드·전달 자료와 최종 GPU7단계 전체 흐름을 확인했다.

Critical: 없음.

Warning: 없음. 아래 v2 실패·렌더 진행 기록은 검수 당시 중간 상태이며 최종 v4 재검증에서 해결됐다.

Suggestion: `docs/PORTABILITY.md`의 예제에서도 내부 실행은 `--cache-root .runtime/cache`를 명시하면 설치 환경과 학습 입력·캐시 범위를 구분하기 쉽다.

## 확인한 변경과 근거

- `.gitignore`는 확장자·디렉토리 기준이며 필수 `guitar_learning/assets/**` 아래 archive 입력을 포함한다. 후속 로그·모델·캐시·비밀파일 제외 규칙은 유지된다. `.githooks/check-staged-files.py:42`도 같은 assets 예외를 쓰며 외부 링크·대형 보고서 검사는 유지한다.
- `guitar_learning/native/paths.py:44`는 읽기 전에 실제 경로가 현재 프로젝트 안인지 확인한다. 현재 ROOT 안 경로를 historical root보다 먼저 취급해 중첩 복사본 경로를 이중 rebasing하지 않는다. CAS의 index/object 읽기와 pin 생성에도 동일 검사가 추가됐다.
- `guitar_learning/tool/validation/portable_inputs.py:23`은 자산·곡 트리의 외부 심볼릭 링크를 provenance와 로더 읽기 전에 거부한다. 원본 역사 식별자·SHA와 현재 입력 경로를 구분한다.
- 테스트가 삭제된 외장 archive manifest를 읽는 대신 내부 CAS에 봉인된 모든 관련 legacy 버전을 검증하도록 바뀌었다. 현재 바이트를 원 SHA와 비교하며 변조 실패 검사를 유지한다.
- provenance before/current 비교에서 바뀐 것은 files/generated_files의 `guitar_learning/native/paths.py` internal_sha256 두 레코드뿐이다. 원본 식별자와 original_sha256은 그대로다.
- 팀원 묶음 manifest의 trace·metadata·scene·body order·support candidate 총 5개 파일 크기와 SHA를 독립 확인했다. 원 trace 및 보조 JSON과 전달용 파일이 바이트 단위로 같다.
- joint 105개와 body 106개 순서를 SHA가 봉인된 내부 initial_values의 human 66개 + guitar 논리 39개 + chair 순서와 독립 대조해 일치했다. 전달 안내는 native 사람 몸체 관측과 재구성 기타 마커를 구분하고, 과거 정책 기록이라는 한계를 명시한다.

## 독립 실행

- `python3 -B -m unittest guitar_learning.tests.test_portable_native_inputs guitar_learning.tests.test_historical_inputs`: **13개 통과**.
- `python3 -B .githooks/test_file_policy.py`: **5개 통과**.
- 전달 manifest 및 원본 바이트·관절/몸체 순서 검증: **통과**.

검수자는 production 코드·테스트·원자료를 수정하지 않았다. 외장 저장소 자료 내용도 읽지 않았다. 이 문서만 검수 산출물로 작성했다.

## 추가 변경 최종 검수

추가 코드 판정: **문제없음**. `scripts/smoke_portability.py`는 복사 후 내부 출력 디렉토리 생성, 목표 프로젝트 외부 출력 거부, 단계별 timeout과 오류 문구를600초로 일치시킨 변경이다. 별도 임시 트리·subprocess 모킹으로 복사 시점에 출력이 아직 없고 이후 정상 생성되는 조건, 외부 출력 거부 시 디렉토리가 생성되지 않는 조건을 독립 확인했다. 이는 실행 순서 검사이며 GPU 검증으로 계산하지 않는다.

`guitar_learning/train.py`는 진입점 뒤 잘못 추가된 `f` 한 글자만 제거했으며 현재 바이트가 `git show HEAD:guitar_learning/train.py`와 정확히 같다. 두 파일 AST 구문 검사도 통과했다. 기존 학습 연산을 수정하지 않았다.

실제 v4 검수 시점 `.runtime/relocated project v4/runs/smoke/report.json`에서 runtime 준비·입력 감사·GPU probe·최소 학습·strict재개·전곡 평가가 모두 종료 코드0임을 확인했다. 전곡 평가는259.42초였다. 렌더는 진행 중이므로 최종 전체 완료 및 영상 결과는 이어지는 최종 GPU 보고서를 확인한다. v1~v3 실패 기록을 보존하고 현재 검증과 구분한 보고 방식도 적절하다.

`sharing_validation.json`은 필수214입력·전달6파일 중 ignore0이며, 내부 입력 SHA 일치와 코드 해설33파일·561정의 갱신을 명시한다. 문서가 설치된 Python/CUDA/드라이버와 프로젝트 입력 자료를 구분하고 내부 캐시·출력 예제를 제공하는 것을 확인했다. 다른 실제 PC나 SSHFS 검증을 이번 로컬 복사본 실행으로 대신했다고 주장하지 않는다.

## 최종 완료 확인

최종 판정: **문제없음**. `gpu_smoke_v4/report.json`에서7단계 모두 passed/종료 코드0 및 completed=true를 확인했다. 전곡 평가2에피소드259.42초, 렌더272.35초이며 렌더 report도 completed/scene_closed=true다. 두 MP4의 현재 SHA와 ffprobe를 검수자가 직접 재실행해 기록과 동일함을 확인했다. 각각1280×720·984프레임·32.8초다. 핵심 실행33파일은 복사본과 현재 파일의 SHA를 독립 계산해 모두 일치했다. 현재 원본의 추가 GPU학습·strict재개도 정상 종료·optimizer누계2회·누계8전이로 별도 기록돼 있다.

추가 테스트 변경의 검증 강도도 유지된다. internal_native는 변조 임시 파일 위치만 ROOT 안으로 옮겼고 원래 SHA 불일치 검사는 그대로다. portable_checkpoints는 설정·계보를 프로젝트 안에서 저장한 다음 원본 checkout 전체와 이동본의 설정/계보 두 파일을 모두 삭제한 뒤 strict 복원을 검사한다. 저장된 설정 snapshot과 계보 SHA만으로 복원하는 조건을 약화하지 않았다. 설정·snapshot·소스·제어·legacy 음성 검사를 보존하고, 외부 설정은 checkpoint를 저장하기 전에 거부하는 신규 검사를 추가했다.

검수자가 현행 소스에서 `test_portable_checkpoints`, `test_internal_native`, `test_local_runtime`17개를 독립 재실행해 전부 통과했다(15.66초). 기존 독립18개와 별도 두 조건 모킹 검사, 실제 GPU 증거를 구분해 기록한다. 새 학습 성능·FK 정확도·접촉 압력·음향 성공을 이번 이식성 검사로 입증했다는 주장은 없다.
