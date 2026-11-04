# 저장 공간 정리 결과 — 2026-11-04

사용자가 승인한 Git 임시파일·검증 사본 및 두 실험 폴더의 비대표 영상·원시 로그를 정리했다. 실제 관측 확보량은 **약 22.39GiB**이며, 디스크 여유 공간은 약18GiB에서 약40GiB로 늘었다. 용량은 정리 중 다른 작업의 쓰기에 따라 조금 달라질 수 있다.

## 실행 결과

| 항목 | 결과 |
| --- | --- |
| Git 임시파일 | Git이 garbage로 판정한 정확히17개 제거, 약12.82GiB. 정상 객체·pack·refs·index·이력은 수정하지 않음 |
| 검증 사본 | `.runtime/pushed_verification_20261101/` 제거. 고유 실행 결과64개 약97MiB를 먼저 이동하고 전후 SHA 일치 확인 |
| 두 실험 폴더 영상 | 비대표·중복149개 제거, 대표127개 보존. 하드링크를 고려한 예상 확보량은 약49MiB |
| 두 실험 폴더 로그 | 완료 실행의 원시 로그5,784개, 약7.61GiB 제거 |
| 모델과 요약 | 두 폴더의 모델662개, 학습 집계276개, checkpoint manifest272개와 최종 보고서·설정·소스/입력 봉인 보존 |
| LFS | 원격 존재 점검에서37개 객체 약0.59GiB가 없다고 응답. **LFS는 하나도 삭제하지 않음** |

## 보존한 고유 검증 결과

기존 `.runtime/pushed_verification_20261101/project/runs/pushed_only_smoke/`의 전체64파일을 [preserved_smoke_outputs](preserved_smoke_outputs/)로 이동했다. 초기·최종·재개 모델과 평가·실행 기록을 포함한다. 과거 JSON 안의 실행 경로는 당시 근거이므로 다시 쓰지 않았으며, [이동 대응표](execution.json.gz)의 preservation 항목으로 현재 위치를 확인한다.

## 보존·삭제 기준

- [대표 영상 전체 목록](REPRESENTATIVE_VIDEOS.md)과 [영상 선정 이유·SHA](video_audit.json)를 따른다. 문서의 중복 소지 영상 참조는 동일 SHA의 보존 영상으로 바꾸고, 구현 smoke 영상 두 링크는 제거 사실을 명시했다.
- 원시 episodes/transitions/decisions/자원/추적 스트림과 불필요한 완료 실행 콘솔 로그를 제거했다. 최종 평가·진단 요약, learning_metrics 및 checkpoint_manifest는 보존했다.
- 진행 상태가 불확실한5개 실행 경로와 관련 콘솔 로그는 보존했다. 후보의 크기·수정시간·inode를 삭제 직전에 대조했고 변경·사용 중 후보는 없었다.
- 외장 링크와 그 원본, 두 실험 폴더 밖의 연구 로그·모델은 제거하지 않았다.
- 호스트 프로세스 확인에서 Git 작업이나 후보 파일·사본의 열린 핸들은 발견하지 못했다. 접근 제한된 시스템·SSH 보조 프로세스는 [확인 기록](open_file_check.json)에 별도로 남겼다.

## 검증과 한계

- 보호 대상41,394파일의 누락은0이며, 계획한 문서4개 수정 외 파일 식별자·크기·수정시각 변경은0이다. 대표 영상127개와 이동한64파일의 SHA가 일치했다.
- Git 연결성 검사가 종료코드0으로 통과했고, Git garbage가17개에서0개로 줄었다. LFS의 원격 누락 판정은 사용자 요청의 점검 결과이며 업로드·삭제를 실행하지 않았다.
- 정리 대상이 아닌 코드3개가 다른 동시 작업 중 변경된 것을 감지했다. 해당 코드는 정리 작업에서 수정하거나 되돌리지 않았고, 나머지10,023개 소스 SHA는 유지됐다. [검증 기록](validation.json)의 concurrent_source_changes에 전후 SHA를 남겼다.
- 원시 로그를 제거했으므로 해당 실행의 전체 프레임/전이 단위 재분석은 기존 별도 보관본이 있어야 가능하다. 보존한 집계·최종 결과를 원시 로그 전체와 동일하다고 보지 않는다.

## 세부 기록

[요약](summary.json) · [삭제 전 목록과 보호 목록](manifest.json.gz) · [실제 삭제·이동 내역](execution.json.gz) · [로그 선정](log_audit.json.gz) · [임시자료 감사](temporary_audit.json.gz) · [LFS 원격 점검](lfs_remote_check.json) · [보존 검증](validation.json) · [Git 검증](git_validation.json)

[독립 최종 검수](REVIEW.md) · [문서 링크 검증](document_validation.json).
