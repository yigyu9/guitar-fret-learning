# PC2 H 본 학습·평가 감독 도구 독립 검수

검수일: 2026-11-04 KST. 대상은 새 `도구/pc2_train_eval_v1.py`, 기존 설계·실행 프롬프트·study 명령 생성, 실행 사본의 저장·지표 schema와 실제 메모리 검사 기록이다. 검수자는 코드와 기록을 읽었으며 소스·자산·봉인·설계·실행 중 도구·로그·결과를 수정하지 않았다. GPU·학습·평가를 추가 실행하지 않았고 이 문서만 새로 작성했다.

## 최종 판단과 동결본

**확인한 본 학습·평가 감독 범위에서 미해결 차단 오류는 없다.** 발견한 진행 파일 부분 쓰기 및 timeout 우회 분기는 시작 전에 보완됐다. 검수한 최종 동결 SHA는 `ab324fb852c2d0a61b0cc373c2aaec2dd4accdee216164713cca83016d5150c8`이며 `작업자료/본실험_감독계약.json`의 실행 시작 SHA와 동일하다.

본 도구는 H32→H64→H128의 세 본 학습, 이어 조건별 다섯 시점의 총15개 평가를 수행한다. 분석·성공 집계·모델 선정·6개 영상 생성은 이 도구의 완료 이후 별도 구현·검수 대상이다. 이 문서는 H 비교가 완료됐거나 압현에 성공했다는 판정이 아니다.

## 조건·예산·저장본 연결

- 원래 `study.py`의 fresh commands와 저장 argv 전체 동치를 시작 전에 확인한다. 실행 사본은 nested `작업자료/source_snapshot/`이며 공식 launcher·press_sequence CLI를 별도 자식 프로세스로 실행한다. 공유 활성 코드를 실행 입력으로 바꾸거나 학습 옵션을 추가하는 분기는 없다.
- C1/V5 corrected/large/1024환경/seed7, support 초기std0.15·finger0.35, 골반 미포함과 기존 보상·종료·관측·정책·물리·직접 제어·PPO 설정을 유지한다.
- H32=512업데이트·저장간격128, H64=256·64, H128=128·32다. 각각16,777,216전이, planned_transitions=16,777,216과 full_song_after=4,194,304를 완료 후 검사한다. 메모리1회 예산은 사용하지 않는다.
- 세 조건은 resume 옵션 없이 독립 fresh 학습이다. 실제 settings에서 horizon/updates/checkpoint_every만 제외하고 나머지 설정의 동치를 검사한다. 노출 예산은 updates×H×N이 같으므로 세 조건에서 동일하며 종료 reset에 따른 기존 구절→전곡 전환을 그대로 둔다.
- 완료 후 단일 run의 committed 전이·PPO update·curriculum 예산과5개 checkpoint의 SHA·update 위치를 검사한다. initial, 25/50/75% periodic, final 저장 규칙은 실행 사본의 실제 runner 및 CheckpointRecorder와 맞는다.
- 평가는 원래 명령의 initial/periodic/final 이름과 manifest를 연결하고 저장 update×해당 batch가 지정 평가 전이와 같은지 확인한다. 전곡32환경, 각 환경 첫 episode와 실패 포함 분모, 입력 오류·정리 오류 없음 및 닫힌 scene을 검사한다. 주기 모델을 다른 H의 모델이나 검증되지 않은 checkpoint로 바꾸지 않는다.

## 감독·오류·공유 처리

- 메모리 통과를 먼저 요구하고 같은 local PC2_실행.lock을 비차단 획득한다. 각 자식 시작 전 GPU compute 비점유를 확인한다. SIGINT/SIGTERM은 예외로 전환하며 자식 생성 직후 try/finally에 들어가 자기 process group에 종료·wait, 필요 시 kill·wait를 수행한다.
- Python 최적화 실행을 거부한다. source snapshot/design 및 자기 SHA를 각 작업 전후 검사한다. 단계 오류나 예산·저장본·입력 검증 실패를 숨겨 완료로 만들거나 자동 조건 변경·재시도를 수행하지 않는다.
- checkpoint manifest의 완성된 행만 읽고 기록된 checkpoint SHA를 검사한다. 검증한 파일은 path/SHA/크기/mtime cache로 중복 hashing을 줄이며 완료 후 다시 전체 manifest를 검사한다.
- 약15초마다 PID·조건·PPO update·committed 전이·마지막 checkpoint와 SHA·속도·ETA·자원 최고·native 상태를 갱신한다. 현재 조건 행의 running/update/committed 정보도 반영한다. 다른 두 조건은 대기로 남긴다.
- 완료 후 새 출력과 감독 로그·resource·command·receipt를 공유하고 파일별 SHA를 대조한다. 기존 공유 파일이 다르면 덮어쓰지 않고 중단한다. 공유 검증 영수증은 별도 작업자료에 기록한다. 원본 봉인 payload는 공유 출력 동기화 대상이 아니다.
- 공유 status 일시 쓰기 오류는 로컬에 기록한다. 완료 artifact 전송이 실패하면 후속 단계로 조용히 진행하지 않는다. 원시 실패 자료는 로컬에 남으며 불명확한 장애 복구는 별도 진단·새 attempt와 strict resume가 필요하다.

## 발견한 시작 전 차단 사항과 반영

1. `lastline()`이 첫 metrics 행의 부분 쓰기에서 개행이 없을 때 잘못된 slice를 파싱해 정상 자식을 중단할 수 있었다. 개행이 없으면 None을 반환하고 완성된 마지막 행만 읽도록 정정됐다.
2. 비원자적으로 갱신되는 native status 및 최초 settings 파일을 exists 직후 파싱하면 JSONDecodeError가 날 수 있었다. livejson으로 미완성 파일을 잠시 비어 있는 값으로 보고 다음 반복에서 읽도록 보완했다.
3. 빈 settings에서 `continue`하면 timeout·heartbeat까지 우회했다. `if settings`일 때만 검증하되 빈 경우도 기존 monitor/watchdog/상태 갱신을 통과하도록 정정됐다.

`검증/PC2_진행파일경합검사.json`은 부분 첫 metrics 행, 완성 전행+부분 꼬리, 완성 metrics 행, 부분 status JSON의 실제 임시 파일 검사4개가 통과했다고 기록한다. 검수자는 이 검사 기록과 수정 코드를 읽었고 재실행하지 않았다.

## 실제 시작 상태 확인

동결 후 기존 감독 PID319350의 생존을 읽기 확인했다. 확인 시 H32_seed7이 PPO3업데이트·98,304 committed 전이, error=null로 진행 중이었고 H64/H128은 미시작이었다. H32의 실제 settings는 N1024/H32/updates512/checkpoint128, 계획 전이16,777,216/전곡 문턱4,194,304였다. PPO LR·epoch2·minibatch4096·gamma0.99·lambda0.98도 설정에 유지됐다. 이후 진행·완료 여부는 최신 status와 최종 report를 확인해야 한다.

## 해석·운영 범위

GPU 자원 값은 장치 전체 사용량의 주기 표본이며 정확한 연속 최대나 학습 tensor만의 최대가 아니다. process-tree RSS는 공유 페이지 중복을 포함할 수 있다. committed/elapsed 속도와 ETA는 초기화·관찰 등을 포함한 실행 속도이며 수집 전이/초와 구분한다.

1200초 감지는 metric/native 상태 또는 stdout 크기가 모두 변하지 않는 경우의 감지다. stdout heartbeat만 계속되는 물리 무진척까지 독립적으로 검증하는 기능으로 확대하지 않는다. 단계 전체에는 별도24시간 상한이 있다. 현재 읽은 시작 상태에서는 실제 PPO update와 committed 전이가 증가하고 있었다.

현재 도구는 공식 reader의 완료·무결성 조건까지 확인한다. 압축 episode 복원, P1~P9별 미노출/노출 후 실패 분모, strict 전체 유지와 필요한 해제, legacy 달성과의 구분, 대표 모델 선택 및 영상 재생 검증은 이후 분석·렌더 도구에서 확인해야 한다. 이 판단은 그 후속 구현에 대한 사전 포괄 승인이 아니다.
