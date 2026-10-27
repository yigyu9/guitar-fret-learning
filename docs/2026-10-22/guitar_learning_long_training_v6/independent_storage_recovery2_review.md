# 고아 Git 임시 pack의 RAM 보관 사전 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 실행 전 코드·변경 범위 검수.** 실제 복사·삭제·프로세스 조회·Git fsck는 실행하지 않았다.

## 코드 및 경로 범위

`backup_git_temporaries_to_ram.py`는 이름을 명시한 `tmp_pack_LiHwdn`, `tmp_pack_lcis9h` 두 파일만 대상으로 한다. named pack/idx/keep·refs·index·실제 학습 자료를 삭제하는 경로가 없다. regular file/no symlink/nlink1 검사와 두 번의 lsof 검사를 통과해야 하며, lsof 오류·불명확한 결과도 거부한다. 파일 inode/크기/mtime가 복사 전후 같고 복사 중 SHA·원본 재독 SHA·RAM 복사본 SHA가 모두 같아야 한다. 복사본 flush/fsync 및 SSD의 개별 사전 기록 뒤 원래 임시 파일만 unlink한다. 기존 RAM 디렉토리는 덮어쓰지 않는다.

사전 공간 검사는 host MemAvailable이 두 파일 합계보다8GiB 이상 크고 `/dev/shm` 여유가 합계보다1GiB 이상 커야 통과한다. root가 제시한 두 파일 합계는6,833,319,766bytes이며 RAM 보관은 휘발성 캐시 보관이다. fsync가 재부팅 후 보존을 보장하지 않으며 유효 Git 객체나 실제 학습 자료의 영구 백업으로 설명하면 안 된다. 백업 후 실제 MemAvailable·shm 여유를 다시 확인하고 기존 학습 host4GiB floor를 유지해야 한다.

이 코드는 안정된 고아 파일이라는 운영 전제와 검사 시점의 상태를 검증한다. lsof 검사와 unlink 사이에 새 Git writer가 생기지 않는 운영 조건까지 자동으로 잠그는 도구는 아니다. root의 Git 작업 비활성 확인을 전제로 한 좁은 정리이며, 모든 임시 pack에 일반 적용하는 삭제 도구가 아니다.

## .gitignore

보관한 `gitignore_before_local_run_exclusions`와 현재 파일을 직접 대조했다. 기존 내용은 그대로이고 다음 phase 내부의 세 패턴과 주석만 추가됐다.

- `recovered_train2000_restart1/`
- `train_resume*/`
- `evaluation_*_1024/`

학습 결과를 삭제하지 않고 Git의 향후 추적 대상에서 제외하는 변경이다. 이미 추적된 파일이나 다른 Git 작업 전체의 pack 증가를 이 규칙만으로 방지한다고 보증하지 않는다.

## 후속 운영 판단

원래 중단된 `train_resume700`의5회/모델1305는 보존하고, 검증한1300부터 새 경로에서700회를 다시 수집하는 방식은 기존1300+700 계약과 맞는다. 첫5회는 새 유효2000회에 합산하지 않으며 도구의 `--run`/`--resumed`에는 새 경로를 명시해야 한다.

원tmp 제거 후 `git fsck --connectivity-only` 결과를 보존하는 것은 적절한 추가 점검이다. 이는 도달 가능한 객체 연결성 범위이며 전체 객체 내용 SHA·모든 Git 상태 검증이라고 확대하지 않는다. 최종 RAM 정리는 대상이 계속 고아 캐시 두 파일임을 확인하고 SHA·조치·연결성 결과를 남긴 뒤 수행하는 범위로 이해한다. 실제 조치나 검증의 성공은 이 사전 코드 검수에서 인증하지 않았다.

## 검수 기준 SHA256

| 파일 | SHA256 |
|---|---|
| backup_git_temporaries_to_ram.py | `cd07ec685b215984df3907a2ed76dd59f485936e337891d86c0d847ccd49d182` |
| 현재 .gitignore | `7b158a0c9c200fe657f2ff041a40d1e6a2ded73694d3bf5bced9079b27c6287a` |
| 보관 .gitignore | `244b25ca310d54a2df7d9fa6e947e79292eda357f1c2524ab04939028bfd62c1` |

Python3.8 AST와 세 ignore 추가의 정확한 범위 검사가 PASS했다. 이 기록 파일 외 활성 소스·도구·원자료·Git 파일을 수정하지 않았고, 도구 main·GPU·native·GL·실제 신호는 실행하지 않았다.
