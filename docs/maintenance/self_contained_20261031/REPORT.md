# Git 정책·프로젝트 내부 실행·팀원 전달 정리 — 2026-10-31

## 변경 내용

- `.gitignore`를1343행·1289규칙에서107행·89규칙으로 정리했다. 개별 실험 파일명 나열을 제거하고 확장자·디렉토리로 분류한다. 코드·JSON/CSV 요약·그림·PDF는 공유하고, 모델·동영상·캐시·개인 환경·docs 원시 스트림/NPZ·일반 archive는 로컬에 둔다.
- `guitar_learning/assets/**`의 archive 경로는 실제 실행 입력이므로 예외로 포함하고 staged 검사도 일치시켰다. 개인 에이전트 지침은 계속 제외한다. `.gitignore`는 이미 추적 중인 파일을 자동 제거하지 않으며 이번 작업은 Git 인덱스·commit·push를 변경하지 않았다.
- 현재 실행 입력은 파일을 열기 전에 프로젝트 내부 경로인지 검사한다. 등록된 역사 식별자→내부 복사본 매핑과 원래 SHA는 유지하고, 미등록 외부 절대 경로·상위 경로 탈출·외부 링크는 거부한다. native provenance 자체와 CAS index/객체에도 같은 경계를 적용한다.
- 프로젝트를 기존 루트 아래 공백 포함 하위 경로로 옮길 때 현재 경로가 역사 경로로 다시 해석되는 버그를 고쳤다. 검증 도구도 복사 이후 내부 출력 디렉토리를 만들도록 수정했다.
- 실제 GPU 학습 완료 후 `train.py` 마지막의 불필요한 문자 `f`로 종료 코드가 실패하는 문제를 발견해 그 문자만 제거했다. 수정 전 파일은 before/에 보존했다. 학습 연산·보상·성공 기준은 변경하지 않았다.

## Git 공유 검사

[전체 정책 대조](gitignore_audit.json)는 외장 심볼릭 링크를 따라가지 않고231,819개 경로를 비교했다. 오래된 개별 파일 제외가 사라져10MiB를 넘는 구형 JSON5개가 ignore에서 풀렸으나, staged 검사가10MiB 초과 생성 보고서를 계속 거부한다. Gitignore는 파일 크기 조건을 표현할 수 없다.

[필수 파일 공유 검사](sharing_validation.json)에서 실행 필수214파일과 진단 전달6파일 중 ignore되는 경로는0이다. NPZ는 기존 `.gitattributes`의 LFS 규칙을 따른다. clone 뒤 `git lfs pull`로 실제 바이트를 받아야 한다. 로컬 원시 로그나 학습 checkpoint를 자동 업로드한 작업은 아니다.

## 팀원에게 전달할 자료

[전달 안내](/home/ajou/yigyu/3/docs/TEAM_HANDOFF.md)와 [진단 묶음](/home/ajou/yigyu/3/data/diagnostic_inputs/finger_fk_native_v1/README.md)을 사용한다.

- `trace.npz`: 실제 남아 있는 과거 기준 기록 `baseline/trace_initial/trace_env0000.npz`와 바이트 동일. q1969×105, body_state1969×106×13, env0·60Hz·전곡1회다. 새 실험이나 현행 v9 정책의 성공 기록이 아니다.
- 원래 metadata와 body/joint 순서·xyzw quaternion·좌표계·SHA를 함께 제공한다. 순서의 근거인 내부 initial_values.json SHA가 수집 당시 입력 봉인과 일치한다. 인간66몸체는 native 관측이며 기타39논리 마커는 단일 강체에서 재구성한 값이다.
- `support_candidate.json`은 기존 `guitar_learning/assets/runtime_inputs/paper/initial_pose/archive/experiment_records/lower_body_release_v1/front_facing_pose_v1/source_v9/support_candidate.json`에4,959바이트의 실제 로컬 파일로 존재한다. SHA256은 `15ae33e4b96a760c83cfad1dd12f7525ea007af526619d9c7e400a6a9ad67b65`다.
- 과거 failure_diagnosis README/status는 역사 기록으로 표시하고 기존 next를 historical_next에 보존했다. 현행 다음 단계는 CURRENT_STATUS로 연결한다. 원래 진단 전체가 완료됐거나 FK 정확도가 입증됐다는 뜻은 아니다.

## 검증

- 경로·재배치·CAS·준비 입력 관련22검사와 확장17검사, Git정책5검사로 총44검사를 통과했다. 외부 archive fixture에 의존하던 검사는 같은 로컬 CAS의 원래 식별자/SHA 전체 버전을 검증하도록 바꿨고 원문은 보존했다.
- Git 정책5검사 통과: 필수 archive 입력 포함, 일반 archive/환경/산출물 제외, 강제 추가·외부 링크·대용량 보고서 거부.
- [현재 입력 감사](inputs_final.json):214파일·193provenance·67목표·105준비 관절, 외부/누락0. 현재 바이트 SHA도 [공유 검사](sharing_validation.json)와 일치한다.
- 코드 해설33연결 파일·561정의의 SHA·정의 위치를 갱신했다. 활성 Python 수는295개다. [정적 검증](code_guide_validation.json).
- 실제 GPU 최소 학습·strict재개·전곡 평가·영상 검증은 아래 최종 결과를 따른다. 설치된 Python/PyTorch·운영체제 라이브러리·NVIDIA 드라이버·ffmpeg는 실행 환경이며 외장 프로젝트 데이터와 구분한다.

### 실패 시도와 재검증

1. [v1](gpu_smoke/report.json): 중첩 복사 경로의 이중 재배치로 입력 감사 실패. GPU probe는 성공했고 학습 이후 단계는 생략했다.
2. [v2](gpu_smoke_v2/report.json): 입력·GPU probe 성공, 출력이 복사본 밖에 있어 학습 설정 입력을 찾지 못했다. 외부 입력 경계를 완화하지 않고 출력 위치를 내부로 바꿨다.
3. [v3](gpu_smoke_v3/report.json): 입력·GPU probe 성공, 학습4전이는 저장 완료했지만 진입 파일의 `f` 때문에 프로세스 종료가 실패했다. 후속은 생략했다.
4. [v4 최종 검증](GPU_FINAL.md): 별도 독립 복사본에서 입력·GPU probe·학습·strict재개·전곡2평가·손/전신 렌더까지 전부 정상 종료했다. 전곡 평가는259.42초, 렌더는272.35초였다. 이후 테스트 fixture2개와 검증 스크립트의 단계 제한600초를 정비했으며, 핵심 실행33파일은 검증 복사본과 현재본이 SHA일치한다. 최종 현재 소스에서도 GPU새학습·strict재개를 다시 통과했다.

실패한 임시 복사본3개(약1.46GiB)는 단계 report/log와 수정 전 소스를 남긴 뒤 삭제했다. 원래 코드·자산·진단 원본은 삭제하지 않았다. [정리 목록](temporary_copy_cleanup.json). 최종 복사본·native 캐시·출력은 모두 `/3/.runtime/` 아래이며 Git 공유 대상이 아니다. 실행기는 일반 기본 캐시를 유지하므로 프로젝트 내부 실행에는 `--cache-root .runtime/cache`를 명시한다.

## 재현과 호환 범위

[PORTABILITY](/home/ajou/yigyu/3/docs/PORTABILITY.md)의 내부 캐시·내부 출력 예제를 사용한다. GPU검증은 small·2환경·H2·새 학습1회+재개1회이며 학습 성능 향상의 검사가 아니다. 프로젝트를 /3의 공백 포함 별도 루트로 복사하고 원래 대량 docs/논문/보관 코드 없이 실행한다. 다른 실제 PC 또는 SSHFS 전체 검증을 대신하지 않는다. SSHFS일 때는 native 빌드/캐시를 각 PC 로컬 디스크에 둔다.

이번 입력 경계 소스와 provenance SHA가 바뀌었으므로 이전 source에 봉인된 checkpoint가 현재 코드에서 strict 검증을 거부할 수 있다. 기존 checkpoint·과거실험 input pin을 새 값으로 덮어쓰지 않았다. 이전 결과는 당시 source/계약으로 읽고 새 학습·재개·평가는 같은 현행 소스를 사용한다.

## 독립 검수

[독립 변경 검수](REVIEW.md)에서 입력 경계·Git정책·진단 배열 원본동일성·관절/몸체순서·출처 원본SHA 보존을 확인했다. 최종 GPU 결과는 [GPU_FINAL.md](GPU_FINAL.md)와 실제 단계 report를 따른다.


## 후속 정리 기록

역할별 정리에서 완료된 독립 검증 복사본 `.runtime/relocated project v4/`를 제거했다. 이 문서가 가리키는 report/log·영상은 `gpu_smoke_v4/`에, 현재 소스의 모델은 `current_train/`·`current_resume/`에 보존했다. native 캐시도 유지한다. 당시 명령·수치·입력 SHA는 변경하지 않았다. [이동·삭제 검증](/home/ajou/yigyu/3/docs/maintenance/organization_20261031/REPORT.md).
