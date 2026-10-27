# 최종 5문서 독립 검수

검수일: 2026-10-22. 요약 판정: **문제없음(PASS)**. 최종 문서와 이미 독립 검수한 학습·평가·자세·영상·보존 증거의 대응을 확인했다. 연주 성능·자연스러움 개선을 인증하는 판정은 아니다.

## 검수 범위

새 phase README와 외부 현행 4문서를 읽고, 4문서는 `guitar_learning/archive/20261022_before_long_training_results_v6`의 변경 전 원문과 diff로 대조했다. 이 archive의 4개 원문 SHA와 manifest SHA, 최종 `current_documents.json`의 정확한 4경로 집합·현재 SHA·phase README SHA를 실제 파일과 확인했다. 5문서의 링크 실재, code fence 짝, Bash 예시 구문을 CPU 읽기로 확인했다. 아직 생성 전인 로컬 `result_manifest.json` 링크만 의도적 대기 상태이며 문서도 이를 미완료 봉인으로 구분한다.

학습 raw 전체 CRC나 모든 원장을 다시 실행·검산하지 않고, 앞서 완료한 `independent_final_training_review.md`, `independent_fixed_evaluation_review.md`, `independent_pose_media_review.md`의 확인 결과를 근거로 문구·수치·범위를 대조했다. 도구 main/GPU/GL/native/실제 프로세스 조작은 수행하지 않았고, 소스·원자료·타인 문서를 수정하지 않았다.

## 정합성 확인

- 유효 학습은 저장 prefix1300 + strict resume700 = 2000업데이트/65,536,000전이/64,000행이다. 재개 시 물리 장면·부분 곡은 새로 시작하며 연속 fresh2000이라고 하지 않는다. old prefix만 CRC 완료행을 인증하고 old 전체 EOF/native close는 인증하지 않는 경계와 새700 정상 종료 범위가 맞다.
- 별도13회·old 후속62개 파일·첫 재개5회는 유효 경로에서 제외된다. phase 문서는 합80의 명목 예산과 raw/commit 인증의 차이를 명시하며 원자료 삭제나 공식 discarded 일괄 재분류를 주장하지 않는다. NTFS/FUSE EIO와 Git 임시 저장공간 중단의 기록을 학습 수치 오류·하드웨어 근본 원인 확정으로 바꾸지 않는다.
- 전체 종료34,841/안전27,325/물리7,516, 학습 수집 평균2.8163/안전3.0894 및 고정5평가의 별도 분모가 일치한다. 초기3.8408203125·안전1024, best500의5.4287109375·안전414, latest2000의0.7451171875·안전961과 중간1000/1500 표가 실제 평가와 같다. best는 초기를 제외한 평가한 네 학습 모델의 전체1024 평균→안전수→최신 규칙이며 전체 저장본 최적이나 안전 우선 규칙이 아니다.
- 모든 평가의 단계0/67음 전체 성공0과 최종347환경0음·최대5음, 손가락별 달성 편중이 맞다. 단계0이 손가락 동작 금지라고 하지 않으며 설정 고정과 KL retry에 의한 실제 actor LR 감소를 구분한다. clean은 양끝 후보를 확인한 유효 시간의 누적으로 설명해 연속 유지 시간과 혼동하지 않는다.
- 5모델×사전 지정8캡처는 모두 안전하므로 전체1024 실패 분포를 대표하지 않는다. 실제 full quaternion 기반 각도·유효 끝점·t0 제외·idle fade·native q와 기하 MCP 차이·60Hz 진단과240Hz 보상 차이를 유지한다. 끝관절 편중·대기 문제의 잔존을 명시해 자연스러움 개선으로 과장하지 않는다.
- 실제 두 영상은 best500 env0의4/67음·서로 다른 뷰이며 latest2000 영상이 아니다. 1969프레임/60fps/1280×720/32.816667초, 두 MP4 SHA, 새 적분0, root QA와 실제 독립 검수 링크가 맞다. 선정은 최고 음수가 아닌 사전 최저 안전 ID이다.
- 현재 source436/v6·544상태/8슬롯, CPU/오른손 격리 및 구계약 strict 거부, 실제1300→2000 복구와 미실행2000→2001을 구분한다. 과거 v4/v5 및 다른 소스의 성과·재개 검증을 현재에 상속하지 않는다. 임시 RAM 캐시 해제·두 Git 키 원복과 별도 외부 사본 봉인 범위도 실제 기록과 일치한다.

## 해소한 문서 지적

1. 재검산 예시의 출력이 봉인 phase 안을 가리키던 부분을 별도 `RECHECK_OUT`으로 수정했다. 검증 JSON·분석·평가·두 렌더 출력이 모두 phase/immutable copy 밖이며, 렌더 입력도 새 재평가 combined와 연결된다. 봉인 이후 예시를 실행해 로컬 exact 파일 집합을 깨뜨리는 경로를 제거했다.
2. 현행 기타 README의 현재 최종 저장본 크기를 실제 `final.pt`의 **92,108,796bytes**로 정정했다. 약87.84MiB/저장간격에 따른 대략172GiB 예산 설명과 정합한다.
3. root가 작성한 `media_qa.json`을 독립 QA라고 부르던 라벨을 영상 QA로 바꾸고 실제 `independent_pose_media_review.md` 링크를 추가했다.

## 최종 확인 SHA256

| 문서 | SHA256 |
| --- | --- |
| phase README.md | `421b281fe40f68ae0f1edbd5c1fb835317f1357b0bb6e6d8894bd044675b498c` |
| CURRENT_STATUS.md | `364b556998c2fdf356763c8c7d3c7af9af5b1e3353b6ed0fac4eb510f6acb7da` |
| guitar_learning/README.md | `e468eb84d7c41ffce81c12b80496d9f2e3f3774e66e21f51725fac3f39950316` |
| guitar_learning/AGENTS.md | `a722b05883074d4a221cfacb04ec62591e18f7e94ca0fc8829ed400b7a5bb2bc` |
| learning_flow/README.md | `278aef0a31b303264b5e4ea86da690693fe86b5f9a50fc30d65314db20477a62` |
| current_documents.json | `b2aca606b1cc090d819ffef3e87e4af461a0e1bb4841aa5b68b2ad6cccd869a5` |

Critical/Warning: 최종 후보에 추가 수정이 필요한 정합성 결함은 없다. 로컬 결과 봉인 생성과 봉인 후 파일 집합/SHA 확인은 root의 후속 단계이며, 본 문서가 그 완료를 선행 주장하지 않는다. 허용된 이 MD만 새로 작성했으며 쓰기를 종료한다. 봉인 후 추가 파일을 쓰지 않는다.
