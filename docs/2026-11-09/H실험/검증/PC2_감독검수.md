# PC2 준비·H128 메모리 감독 도구 독립 검수

검수일: 2026-11-04 KST. 별도 change-reviewer가 실행 프롬프트, README, 설계, 기존 `도구/study.py`, 추가 `pc2_prepare_v1.py`/`pc2_prepare_v2.py`와 최종 `pc2_memory_v1.py`를 읽었다. GPU·물리·학습을 새로 실행하지 않았고, 소스·자산·봉인·설계·기존 도구는 수정하지 않았다. 검수자가 작성한 파일은 이 문서뿐이다.

## 최종 판단

**현재 준비·메모리 검사 범위에서 미해결 필수 수정 사항은 없다.** 지적 사항을 반영한 메모리 감독 도구를 실행 전에 재검수했고, 이후 기존 실행의 완료 로그·보고서를 읽어 후조건을 확인했다. 이 판단은 메모리 구동 적합성에 관한 것이며 H32/H64/H128 성과 비교나 최적 H의 판단이 아니다. 이후 추가할 본 학습·15평가·영상 감독 도구는 이 검수 범위에 포함하지 않는다.

## 조건과 실행 입력 보존

- 실행 입력은 로컬 `작업자료/source_snapshot/`이며 공유 활성 프로젝트로 대체하는 분기가 없다. 루트 mirror는 독립 로컬 복사이고 실제 argv는 nested snapshot의 공식 launcher·press_sequence CLI를 사용한다.
- 준비 완료 기록에서 snapshot_valid/design_valid/active_matches가 모두 true, 입력 9,338개, 봉인 `743caaacf661c5b32c0072fb9c132149b4bf35949db4baf45e2d838affe6ce49`를 확인했다. 공식 CPU C1 check도 completed=true이며 20개 목표·15개 event·47.25초/2,835 control tick 및 source clock SHA를 기록한다. 독립 검수자는 이 CPU check를 다시 실행하지 않았다.
- 초기 rsync가 상대 링크17개를 누락해 검사에 실패한 기록은 보존된다. 기존 link 텍스트를 복원하고 재봉인하지 않았다는 작업 기록과 이후 봉인 통과를 확인했다. `pc2_prepare_v2`는 완료된 v1을 보존하고 로컬 mirror의 재복사를 허용하는 dirs_exist_ok 및 자기 파일명 참조만 변경했다.
- 본 비교는 C1/corrected/large/1024환경/seed7, support std0.15·finger std0.35, 골반 미포함이다. 조건별 16,777,216전이와 4,194,304전이 노출 문턱·저장/평가 간격을 유지한다. 기존 study.py와 설계를 수정하지 않는다.
- 실제 메모리 argv는 fresh `study.commands()`와 동치인 저장 명령의 H128을 사용한다. baseline 대비 바뀐 값이 `--updates 1`, `--checkpoint-every 1`, 별도 `--out` 세 곳뿐인지 명시 검사한다. 실제 명령 파일에서도 N1024/H128 및 나머지 공통 조건을 확인했다.
- 메모리 검사의 planned exposure는 1업데이트 예산에 따른 별도 일정이다. 이를 본 조건의 전체 예산·구절→전곡 노출 일정이나 학습 성과에 합산하지 않는다.

## 지적과 반영 확인

|지적|최종 반영|
|---|---|
|Popen 후 첫 공유 status 쓰기가 try 밖이어서 실패 시 자식 잔류 가능|자식 생성 직후 try에 진입하고 첫 update·모니터링을 포함, finally에서 자기 process group 종료·wait|
|종료 신호 시 정리·중복 감독 실행 보호 부재|로컬 PC2_실행.lock의 비차단 flock, SIGTERM/SIGINT를 예외로 전환|
|중복 실행의 lock 실패가 기존 실행 status를 stopped_error로 덮어쓸 수 있음|BlockingIOError 전용 except에서 기존 status를 갱신하지 않음|
|최적화된 Python에서 assert 검증이 제거될 수 있음|도구 시작 시 `not __debug__` 명시 거부|
|저장 명령의 나머지 조건 변경을 N/H 검사만으로 잡지 못함|fresh 전체 명령 동치 및 정확히 세 argv 값만 변경됨을 검사|
|메모리 검사라는 후조건이 명확하지 않음|단계 완료·lifecycle·오류 목록 외에 updates_in_run=1, transitions=131072, initial/final manifest 존재와 SHA 검사|
|공유 출력의 부모 경로 누락 및 전달 무결성 근거 부재|부모 생성, out 미생성 실패 분기, 새 출력/metadata 전달 후 파일별 SHA 대조|

메모리 도구의 실행 시작 기록 SHA와 검수 시 파일 SHA는 모두 `345091904bbdf2bca0ba554f76967be82bd47a58e0b5af90e2165e362a4ae6dd`였다. 시작 이후 동결된 파일을 편집하지 않았다.

## 완료된 메모리 검사 기록 확인

검수자가 기존 감독 PID318423 및 자식 실행 기록을 읽었다. 최종 감독 프로세스는 종료됐고 로컬·공유 상태 모두 H128_memory_passed, running_pid=null이다.

|항목|보고서 값|
|---|---:|
|passed / returncode|true / 0|
|업데이트 / 전이|1 / 131,072|
|stage completed / lifecycle_verified|true / true|
|changed_inputs / missing_import_pins / cleanup_errors|모두 빈 목록|
|저장본 종류|initial, final 2개|
|종료 후 snapshot/design 검사|모두 true, 같은 9,338항목·봉인|
|검사 end-to-end 시간|93.781초|
|end-to-end 전이/초|약1,397.63|
|샘플링된 GPU 전체 사용량 최고|4,950MiB|
|샘플링된 자식 process-tree RSS 최고|4,341,555,200bytes|
|샘플링된 system total−available 최고|11,474,980,864bytes|

GPU 사용량은 약1초 간격 nvidia-smi의 장치 전체 값이며 표시·다른 비compute 사용량도 포함할 수 있다. 정확한 연속 최대나 학습 tensor만의 최대가 아니다. RSS는 process tree의 RSS 합계여서 공유 페이지 중복을 포함할 수 있다. end-to-end 속도에는 초기화·컴파일·검증 등이 들어가므로 정상 상태의 수집/최적화 속도와 구분한다. 본 학습 ETA는 실제 업데이트 로그의 속도로 갱신해야 한다.

## 공유 확인과 범위

현재 공유 위치는 이 H 실험의 명시적 전달 경로 `/home/yigyu/cgl-lab/docs/2026-11-09/H실험/`이다. 다른 PC의 대응 경로는 `/home/ajou/yigyu/3/docs/2026-11-09/H실험/`이다. 원본 활성 학습 소스·자산이나 과거 확정 결과를 덮어쓰는 공유는 검수 범위에 없다.

`검증/H128_메모리검사.json`의 로컬/공유 SHA를 독립적으로 읽어 대조했고 모두 `996d0a42530089b27b50d88c43959ae33447dc3704953c02901328af18e0432c`로 일치했다. 전체 출력과 metadata의 개별 SHA 대조는 최종 감독 도구가 완료 단계에 진입하기 전에 수행한다. 이 문서의 공유 복사와 SHA 기록은 상위 작업자가 후속 전달한다.

완료된 준비 도구의 향후 재사용 시에는 CPU 검사 실패 stderr를 별도 파일로 보존하고, 환경 probe의 returncode도 명시하면 진단이 더 명확하다. 현재 공식 C1 check와 환경 probe가 성공한 기록을 무효화하거나 이미 종료된 도구를 수정해야 하는 사항은 아니다.

이 결과를 근거로 H128만 환경 수를 줄이거나 H 외의 학습 조건을 변경할 이유는 없다. 본 H 비교의 strict 유지·필요한 해제·노출 분모와 정책 선택·영상 검증은 이후 실제 평가 자료와 별도 감독 구현 검수를 통해 확인해야 한다.
