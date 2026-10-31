# 자료 역할별 정리 결과 — 2026-10-31

현재 사용 자료·과거 재현 근거·정리 가능한 임시 자료를 구분했다. 실행 코드·자산·곡·학습 설정은 변경하지 않았다.

## 실제 파일 정리

| 조치 | 결과 |
| --- | --- |
| 참조 없는 완료 계획 이동 | 94개를 `docs/history/plans/YYYY-MM/`로 이동, 본문 바이트·체크 상태·SHA 보존 |
| plans 최상위 Markdown | README 제외354개→260개 |
| 참조 또는 링크 때문에 유지 | 검토한 완료계획 중 실제 참조54개와 상대링크 계획1개 보존; 나머지 원문·미분류·외장 링크도 유지 |
| 검증용 독립 프로젝트 복사본 제거 | 이번 내부 실행 검증용 `.runtime/relocated project v4/`의3,530파일, 0.582GiB |
| 보존 | native/빌드 캐시, 실제 연구 결과·원시 근거, 검증 보고서·두 영상, 현재 소스의 학습·재개 checkpoint |

완료 계획은 내용이 필요 없어서 지운 것이 아니라 현재 작업 목록에서 과거 기록으로 분리한 것이다. `history/`는 공유 가능한 과거 문서다. 일반 archive 제외 Git 정책에 걸리지 않게 했으며 이동94개가 ignore되지 않는지 확인했다. Git index·commit·push는 변경하지 않았다.

[이동표·원래 경로·SHA](moves.json) · [선정·보호 근거](plan_candidates.json) · [354개 전체 계획 분류](plan_catalog.json) · [임시 복사본 삭제](deleted_temporary_copy.json).

## 현재 읽는 입구

- [프로젝트 README](/home/ajou/yigyu/3/README.md): 코드·입력·문서·전처리·논문·로컬 산출물의 디렉토리 역할.
- [docs 안내](/home/ajou/yigyu/3/docs/README.md)와 [목적별 색인](/home/ajou/yigyu/3/docs/DOCUMENT_INDEX.md): 현재 사용→최신 결과/계획→재현/보관→참고 자료 순서.
- [계획 안내](/home/ajou/yigyu/3/docs/plans/README.md): 남은 체크가 곧 진행 중 작업은 아니라는 점과 최근 계획/실제 결과 연결.
- [과거 완료 계획](/home/ajou/yigyu/3/docs/history/plans/README.md): 이동한 계획의 시기별 목록.
- [실험 역할 목록](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/README.md): 최신 전환v2 결과와 이전 구조/탐색/판정 진단 구분.
- [자산 역할](/home/ajou/yigyu/3/guitar_learning/assets/README.md): 필수 실행 입력·CAS 원문·특정 연구 입력 구분. `archive` 이름만으로 삭제하지 않기.
- [maintenance 안내](/home/ajou/yigyu/3/docs/maintenance/README.md): 정리 작업마다 무슨 근거가 있는지 한 곳에서 찾기.

[디렉토리 분류표](directory_roles.json)는 각 위치의 역할과 삭제 기준을 기록한다. `support_candidate.json`은 필수 실행 입력, 팀원 전달용 `trace.npz`는 진단 자료라는 구분도 자산 안내에 명시했다.

## 경로와 원문 보존 기준

로컬 일반 텍스트120,562개를 검사했다. 코드·테스트·source/input SHA·실험 계약·문서에서 실제 참조된 계획은 그대로 두었다. 과거 정리 inventory9종의 경로 목록은 실행 의존과 구분했다. 해당 inventory는 당시 위치이며 새 이동표와 함께 읽는다.

계획 후보95개 중 상대 링크를 가진 `torso_support_diagnosis_20261003.md`는 링크 목적지를 외장 접근 없이 완전히 검증하기 어려워 이동하지 않았다. 나머지94개는 본문을 그대로 옮겼다. 날짜별 실험 전체·소스/입력 봉인 경로·현재 assets와 보존 원문은 재현성 때문에 일괄 재배치하지 않았다.

심볼릭 링크 파일63,536개와 디렉토리 링크709개는 따라가지 않았다. 따라서 외장 문서의 본문과 그 안의 링크까지 검수한 것은 아니다. 나중에 외장에서 복구한 문서가 옛 계획 경로를 가리키면 이동표에서 현재 위치를 찾을 수 있다. 접근 불가를 근거로 외장 원본·링크를 삭제하지 않았다.

## 검증

- 이동94개는 원문 SHA 일치, 원위치 제거·새 위치 존재를 확인했다.
- 실행 입력·핵심 코드·현재 저장 모델247개는 정리 전후 SHA가 같다.
- 내부 입력 감사는214파일·provenance193파일·목표67개·준비 관절105개, 외부/누락0이다.
- 현재 소스의 학습/재개 checkpoint2개의 metadata schema와 엄격한 입력 검증을 다시 통과했다.
- 문서·분류만 변경했으므로 새 학습이나 동일 GPU 장기 실험은 실행하지 않았다. 실제 GPU 실행 근거와 영상은 이전 [내부 실행 검증](/home/ajou/yigyu/3/docs/maintenance/self_contained_20261031/GPU_FINAL.md)에 그대로 남아 있다.

[무결성 검증](validation.json) · [내부 입력 감사](runtime_inputs_after.json) · [현재 checkpoint 검증](checkpoint_validation.json) · [독립 검수](REVIEW.md).

독립 최종 검수에서 이동94개·보호247개 SHA, 현재 checkpoint2개의 엄격 검증, 대표 문서11개의 로컬 링크232개를 다시 확인했고 문제없음으로 판정했다.
