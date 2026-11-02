# push된 파일만으로 학습 가능한가

확인 대상은 2026-11-01 GitHub에서 직접 조회한 원격 main 커밋 `cdca74d921d25142af73caed326a6f19ae1fc27b`다. 현재 작업 폴더를 복사하지 않고 원격에서 새 checkout을 받았다.

**기본 학습은 push된 파일만으로 실제 GPU 학습·체크포인트 저장·strict재개·전곡 평가까지 통과했다.** 2026-11-01 22:47 KST에 새 checkout의 최종 파일·Git identity와 외부 파일 접근 검사도 통과했다. **현재6→8 실험 자체는 필수11개 파일이 미push 상태이므로 이 커밋만으로 재현할 수 없다.**

| 확인 | 결과 | 근거 |
| --- | --- | --- |
| 원격 커밋 직접 조회·별도 clone | 위 SHA와 동일. 기존 Git 객체·LFS 캐시를 차용하지 않음 | GIT_IDENTITY.json |
| 기본 활성 학습 Python | 295개 모두 원격에 있음 | DEPENDENCY_REVIEW.md |
| 기본 곡·초기 자세·물리 입력 | 214개·11,389,398바이트, 누락·외부 입력0 | INPUT_AUDIT.json |
| 대용량 LFS 실체 | 121개·407,829,993바이트, 전부 원격 다운로드·크기·SHA 확인 | LFS_VERIFICATION.json |
| 새 checkout 파일 봉인 | 3,488개 tracked 파일·내부 링크의 실제 SHA 기록 | CHECKOUT_MANIFEST.json |
| 입력 검사 파일 접근 | 성공 접근1,328회, 파일666개. 원래 프로젝트 데이터·미등록 외부 파일 접근0 | CPU_FILE_ACCESS.json |
| native 실행 캐시 준비 | 새 checkout 내부의 독립 캐시에서 준비 완료 | NATIVE_PREPARE.json |
| 실제 GPU 실행 | GPU probe·학습·저장·strict재개·전곡 평가 모두 통과 | GPU_REPORT.json |
| 전체 실행 파일 접근 | 성공 접근32,879회·파일8,520개. 외부 프로젝트·미등록 외부 접근·미해석 성공 접근 모두0 | GPU_REPORT.json의 trace |

## 검증 구성과 설치 전제

별도 checkout은 `.runtime/pushed_verification_20261101/project`다. 기본 실행에 필요한 `guitar_learning/`의 활성 코드·assets, `scripts/`, `isaacgym/python/`, 기본 곡 `05_BN2-131-B_solo`와 루트 안내 파일만 sparse checkout했다. 과거 docs·미추적 실험·상위 archive는 기본 학습에 필요한 파일로 섞지 않았다. assets 내부 archive는 필수 입력이므로 포함했다.

기존 Python3.8 환경·설치 패키지·드라이버·컴파일러는 시스템 실행 환경으로 사용한다. 프로젝트 자산과 기존 native 캐시는 복사하지 않았다. Git LFS를 설치하고 실물을 받아야 하며, 작은 포인터 파일만 받아 놓은 상태는 통과가 아니다.

LFS 전체 검색은 partial clone의 비선택 Git blob까지 가져오므로 중단하고 공식 `git lfs smudge`로 선택한 포인터만 다운로드했다. 비인증 다운로드의 일시적 API 제한은 기존 Git 자격증명을 사용하는 정상 인증으로 해결했다. 이전 시도는 `LFS_VERIFICATION_UNAUTHENTICATED.json`에 보존했다. 필터 확장 후에는 원격 Git에 기록된 실행 비트를 복원하고 LFS 인덱스 상태만 갱신했다. 인덱스 tree SHA는 원격 HEAD와 전후 동일하며, 새 commit·push는 하지 않았다.

## 현재6→8 실험에서 빠진 것

기본 학습과 최신 별도 실험은 구분해야 한다. 정적 의존성 기준으로 **현재6→8 fresh 학습에는 최소11개의 미push 파일**이 추가로 필요하다.

- 실험 `tools/runtime.py` 1개.
- `geometry/initial_catalog.json`, `initial_provenance.json` 2개.
- `data/song_bundles/virtual_middle_s3_f6_f8_AB_v1/` 번들8개.

경로·SHA는 [미push 필수 입력](UNPUSHED_FRESH_TRAINING_INPUTS.json)에 기록했다. 이 파일들을 원격 검증 checkout에 몰래 복사해 통과시키지 않았다. 새 학습에 기존 모델이나 출력 settings는 필요하지 않지만, 과거 모델의 평가·strict재개에는 해당 모델과 동일 입력 계약이 별도로 필요하다.

감독 실행기까지 원격에서 그대로 재현하려면 추가 도구·참조 기하·검증 기록과 감독 source 봉인 범위도 정리해야 한다. 현재 감독 봉인은 실제 모델 입력이 아닌 archive 보관 파일9,770개까지 포함한다. 이것을 필수 학습 파일9,770개가 빠졌다는 뜻으로 해석하지 않으며, 이를 맞추려고 보관 코드를 대량 push하거나 기존 봉인·학습 코드를 수정하지 않았다.

## 실제 GPU 검증과 범위

기존 연구가 GPU를 반환한 뒤 새 checkout에서 `scripts/smoke_portability.py`를 실행했다. GPU probe, small·2환경·H2·1회 학습, 저장 모델의 strict재개1회, 기본67목표 곡의 전곡2episode 평가가 모두 통과했다. 재개 후 누적 업데이트는1→2이며 저장 모델의 lineage SHA와 입력 계약 검증도 확인했다. 평가는2episode 모두 시간축을 끝까지 진행했고 물리·손목 실패는0이었다. 학습1회만 수행한 실행 검사이므로 압현 달성0은 학습 성능을 판정하는 결과로 사용하지 않는다.

캐시와 임시 파일도 새 checkout 내부로 지정했다. 실제 실행 파일 접근32,879회·8,520개 경로를 검사했고 원래 프로젝트·미등록 외부 파일 읽기와 미해석 성공 접근은 모두0이다. 설치된 Python·패키지·시스템 라이브러리 접근은 실행 환경으로 별도 허용했다. 실행 전후에 CPU 감사·증거 SHA·전체 checkout 파일·Git identity를 다시 확인했으며, 입력 변경·누락·외부 자산 복사 없이 통과했다. 실제 결과는 [GPU_REPORT.json](GPU_REPORT.json)에 보존했다. 독립 검수에서도 기록된 Python3.8 환경으로 접근 기록을 재분석해 동일한 통과 결과를 확인했다. `/proc/self` 경로는 재분석 프로세스에 따라 해석이 달라질 수 있으므로, 다른 Python으로 분석할 때의 제한은 [독립 검수](REVIEW.md)에 기록했다.

검증은 기본 구성의 실행 가능성을 확인한다. large·1024환경의 성능·장시간 안정성이나 아직 push되지 않은6→8 실험, 모든 선택적 도구·곡·과거 체크포인트의 재현성을 일괄 보장하지 않는다.

[검증 계획](PLAN.md) · [의존성 검토](DEPENDENCY_REVIEW.md) · [독립 검수](REVIEW.md) · [실제 GPU 자동 보고](GPU_REPORT.md)
