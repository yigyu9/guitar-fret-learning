# 중단 원자료 복사본의 프로젝트 밖 이동 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 아래 읽기 검수 범위.** 실측 자료와 코드에 삭제·핀 변경 등의 blocker는 없다. 사소한 RAM manifest 설명 불일치는 아래에 구분했다.

## 이동·원자료 보존

원 `recovery_copy_manifest.json` SHA256 `ee6473509d2c1aaaee250ee59fe8b9930e21ac80d13112ab99c77c6217f3a48a`는 그대로다. 새 `recovery_copy_relocated_manifest.json` SHA256은 `f543902c7b267271d6b22bc0f4ed84b3629f66bfd6c595c693c6af6138ba3306`다.

두 JSON을 직접 대조했다. 새 destination·각 row.copy와 parent manifest/alias/이동 설명 외에는 원 source·전체 파일 집합1387개·각 SHA/bytes·총4,499,049,842bytes·completed/errors가 모두 같다. 새 parent SHA도 원 manifest와 정확히 일치한다.

실제 durable 경로는 `/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1`이다. 실제1387개 파일 집합과 모든 크기를 확인했고, directory inode1997825가 이동 전 기록과 같다. 프로젝트 안의 원 경로는 해당 outside 디렉토리로 향하는 symlink다. root가 이동 직후 전량 SHA를 검산했으므로 이 검수에서는4.5GB 전체 재해시를 반복하지 않았다. root의 전체 검산 기록과 별도로, 현재 active resume의 원 checkpoint 별칭을 통해 실제 파일 SHA를 직접 재계산했다.

- 별칭과 actual 파일은 `samefile=True`다.
- actual1300 SHA는 `b32870dbb9ba09dd9e762be3efa73d335493399239fba9174c10706acc2c32de`다.
- `train_resume700_restart1/inputs_before.json`의 기존 별칭 키에 저장된 SHA와 같다.

`relocate_copied_run.py`는 새 목적지 부재·같은 filesystem·사전 기록을 검사한 뒤 os.rename을 사용한다. 별칭 생성 실패 시 원위치 rename 분기가 있고, 같은 inode와 모든 파일 크기·SHA 검산 후 파생 manifest/완료 기록을 쓴다. lsof로 oldcopy reader가 없음을 확인한 것은 root의 별도 선행 운영 점검이며 이 도구 안의 검사라고 설명하지 않는다. 진행 중 native나 active run 디렉토리를 옮기는 코드는 없다.

## Git 및 RAM 캐시

`.gitignore`는 해당 oldcopy 패턴의 마지막 slash를 제거해 디렉토리뿐 아니라 새 symlink 별칭도 제외한다. 다른 두 phase 내부 train_resume*/evaluation 패턴은 유지한다. 기존에 저장된 Git 객체나 모든 자동 snapshot/pack 작업이 이 변경으로 사라진다고 보증하지 않는다.

`backup_git_temporary_snapshot2.py`는 앞서 검수한 닫힌 도구에서 RAM 경로·명시적 대상 이름·manifest 이름만 바뀌었다. 대상은 `tmp_pack_TPNfCE` 한 개이며 source/backup SHA·크기·lsof·메모리 guard·사전 기록 뒤 unlink 경계는 같다. 결과 파일의 실제 목록은1개·3,644,790,537bytes이고 RAM 휘발성도 명시돼 있다.

**표시 참고:** snapshot2 결과의 scope 문자열은 복사 전 문구인 `Only two unopened tmp_pack files`를 유지해 실제1개 목록과 맞지 않는다. 대상 배열·총bytes는 명확하므로 실행 범위 blocker는 아니다. 이미 실행한 도구/원 manifest를 보존하고 후속 운영 기록에서1개임을 명시하면 된다. 새 fsck 실행 결과나 RAM 전체 SHA를 이번에 독립 재검산하지 않았으며, root가 진행한 결과를 성공으로 선인증하지 않는다.

## 후속 검증 경계

원 proof/분석은 이전 경로·manifest SHA의 역사 자료로 보존한다. 이동 후에는 outside old-run과 새 파생 manifest를 명시해 새로운 검증 출력을 만들고 분석·평가의 `--verification`에 전달해야 한다. 이전 기본 proof를 자동 재사용하면 경로/SHA identity 검사에서 거부되는 것이 맞다. 원 실행의62회·첫13회·첫 resume5회 제외와 새1300+700 경로도 계속 구분한다. 이동이나 별칭은 물리 상태·곡 진행을 복원하지 않는다.

검수 기준 도구 SHA256:

- relocate_copied_run.py: `2b547d0f9da8020649ac653a1c7355ee7fff55fa5039b18508a99e2bc8232825`
- backup_git_temporary_snapshot2.py: `763d284408a4fec724d00e152c441c1d7070750add31fb5685ed156f138689ae`

두 도구의 Python3.8 AST가 통과했다. 이 기록 파일 외 소스·도구·원자료·Git 파일은 수정하지 않았고, 실제 이동·RAM 복사/삭제·Git fsck·프로세스/신호·GPU·native·GL은 실행하지 않았다.
