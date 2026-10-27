# GPU 학습 저장·로그 정리 결과

2026-10-24. 사용자가 제안된 저장 개선과 이전 버전의 큰 로그 삭제를 승인하여 적용했다. 보상v17·물리·제어·관측·PPO·성공 판정은 유지했다.

## 적용 사항

- `guitar_learning.train`의 추가 체크포인트 기본 간격을5→250회로 변경했다. 초기·최종은 별도 저장하므로2,000회 학습은21개(이전100회 간격) 대신9개다. 명시한 간격이 우선하며 재개에 필요한 두 optimizer·난수·curriculum을 보존한다.
- GPU는 업데이트별 JSON을 중복 생성하지 않고 `learning_metrics.jsonl`만 기록한다. 상세 에피소드 정본은 `episodes.jsonl`이고 지표·전이는 ID로 참조한다. 중복 `musical_quality.song`과 공통 이름·계약·설명은 제거/분리하고 공통 메타데이터는 한 번만 저장한다.
- 전이 배열과 gzip CRC·sampled/logged/durable/committed/discarded 회계는 유지했다. 정본을 참조하는 전이 member와 PPO commit 이전에 정본을 동기화한다. 자동60행 저장·수집 중단·동기화 실패를 CPU 통합 검사로 확인했다.
- 초기·중간·최종·유효 실패복구 모델의 저장 시간·바이트·SHA를 `checkpoint_manifest.jsonl` 및 보고서에 기록한다. 모델 복사 없이 이미 저장한 경로를 평가 결과의 최고 모델로 지정한다.
- 새 공통 독자는 이전 에피소드 구조를 스트리밍으로 복원하며 과거 형식도 읽는다. 현행 검사 명령은 `python -m guitar_learning.tool.inspect_gpu_training_log --run RUN`이다. 기존 날짜별 결과의 스크립트는 당시 동결 형식 전용으로 보존했다.

## 추가 진단

종료 에피소드에 손가락별 B 적용 시간·겹칠 수 있는 제외 이유·품질·원시/실제 보상, 대기/압현 구간별 MCP/PIP/DIP 실제 각도 평균·범위·유효 시간, 손목 영역 체류율·Gx/Gy/Gz 초과량을 남긴다. 손가락·손목은240Hz 끝점이다.

엄지는 기존 thumb2/3 source 표면 샘플과 실제 넥 source rear 삼각형4개 사이 유한 거리와 뒷면 쪽3/10mm 근접 비율을60Hz 끝점에서 기록한다. 뒷면 쪽 판정은 최대1mm의 plane penetration을 허용한다. 표면 법선이 없는 표본이므로 엄지 facing cosine은 만들지 않았다. 실제 접촉·압력·음향이나 PhysX cooked 형상 인증이 아니다. 정확한 면 방향에는 표본 법선 정의가 추가로 필요하다.

고정 누적 상태는1024환경에서 약1.27MiB다. 모든 환경의 원시 자세나 매 물리 tick CPU 복사를 추가하지 않았다. 진단 계약은 에피소드 메타데이터에 두고 정책의 strict resume 계약은 유지했다.

## 이전 로그 삭제

`docs/2026-10-20..23/guitar_learning*`의64MiB 이상 로그 묶음12개에서 일반 파일 **9,591개, 합계17,970,584,807bytes(16.74GiB)**를 삭제했다. 대상은 `update_*.json`, `learning_metrics.jsonl`, `episodes.jsonl`, `transitions.jsonl[.gz]`다. 처음 집계에 포함된 심볼릭 링크는 제외했다. 이 합계는 삭제 파일 길이 합이며 하드링크·파일시스템을 고려한 실측 디스크 여유 증가량은 아니다.

체크포인트·영상·평가 캡처·분석 보고서·계약·소스·보관본·스냅샷과 최신v17 실행은 보존했다. 같은 실행 폴더의 보존 대상1,668개에 대해 존재/크기를 확인했다. [정확한 삭제 경로·크기·SHA](cleanup_manifest.json) · [실행별 집계](cleanup_summary.json). 과거 보고서는 당시 검증 결과이며 삭제한 원시 로그의 재분석·독립 재검증은 더 이상 가능하지 않다.

## 검증

- 관련 CPU 검사322개: GPU 관련274개와 학습 기록/PPO/시작48개. [GPU 관련 검사](cpu_gpu_tests.log) · [기록/PPO 검사](cpu_training_tests.log).
- 새 실제 GPU 실행: small/16환경/H32,65회·33,280전이·종료16개. 전체 CRC/EOF·ID 참조·원시 평균·회계·파일 해시 검사 통과. 중간32/64회와 초기·최종4개 저장, 중복 업데이트 JSON0개, 입력 변경/누락/종료 오류0. [검사](gpu_smoke_inspection.json) · [원 보고서](gpu_smoke_retry1/report.json).
- 기존v17 최종 모델: large/1024환경/H32로 실제1회 strict resume. 초기 저장본의 metadata 이외 모델·두 optimizer·난수·3331값 curriculum을 포함한 모든 상태가 정확히 복원됐고2000→2001회로 갱신됐다. [정확 복원 검사](legacy_resume_verification.json) · [재개 로그 검사](gpu_legacy_resume_inspection.json).
- 최신 기존v17의65,536,000전이·36,087에피소드 전체를 새 독자/검사기로 읽고 전체 gzip CRC/EOF·원시/업데이트 대응 검사를 통과했다. [구형 전체 로그 호환 검사](legacy_v17_inspection.json).
- 실제v17 에피소드128개를 정본/메타데이터로 분리 후 정확 복원했다. 표본6,235,774bytes는 정본4,699,354+공통11,305bytes로 줄었다. 이는 에피소드 표본의 결과이며 전체 학습의 일정 압축률 보장은 아니다. 중복 로그 사본 제거 효과는 별도다.
- 실제 실행에서 새 검사기가 정상 곡 종료도 true MDP terminal임을 반영하도록 수정했다. 테스트 fixture도 실제 GPU API에 맞췄다. 전체 구형/새 기록 검사를 다시 통과했다.
- [독립 변경 검수](independent_review.json): 최종 문제없음. [현재456개 Python 원문 SHA](source_manifest.json). 변경 전454개 원문은 `guitar_learning/archive/20261024_before_compact_logging_v1/manifest.json`에 보관했다.

첫 GPU 시도는 빌드 도구 PATH 누락으로 학습 시작 전에 종료했다. 실행 환경을 보완한 `gpu_smoke_retry1`을 검증 정본으로 사용하며 최초 실패 기록도 보존했다. 위 짧은 실행은 저장·진단·호환 검증이고 연주 성능 개선이나 장기 수렴을 뜻하지 않는다.
