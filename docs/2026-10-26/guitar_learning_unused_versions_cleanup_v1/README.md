# guitar_learning 미사용 이전 버전 정리 결과

사용자 요청: “사용되지 않는 버전의 파일들을 모두 정리해줘”.

## 완료한 정리

- 현재 비권장인 과거 비교·실패 재현 설정 `tool/training/configs/long_B_16env_v1.json`을 활성 설정 폴더에서 제거했다. 원문과 변경 전 `docs/PARALLEL_TRAINING.md`는 원래 경로·SHA와 함께 `guitar_learning/archive/20261026_unused_versions_cleanup_v1/`에 보관했다. 현행 안내 링크는 보관본으로 갱신했다.
- 기존 로컬 이전 버전 보관 폴더18개와 이번 정리 보관 폴더1개, 총6,868파일을 외장에 전체 SHA·파일 목록·실행 접근을 검증해 이동했다. 원래19개 경로는 외장 보관본으로 연결된다.
- 현재 사용 중인 Python 소스를 이동·삭제·수정하지 않았다. 기존 실험 결과·모델·CAS와 검증 계약을 유지했다.
- 작업 전후 각각6개 모듈32개 검사가 모두 통과했다. 독립 최종 검수도 통과했다. 임시 staging은 남아 있지 않다.
- 이동 전후 여유 공간 관측 차이는52.31MiB다. 동시에 진행된 다른 개발 작업과 정리 기록 저장이 포함된 시점 간 실제 여유 공간 차이이며, 삭제 파일 크기의 합계와는 다르다.

## 유지한 이전 버전 코드

native Python65개는 현재 출처 검증과 실행 입력 pin 대상이다. 버전명이 붙은45개 중42개는 현행 runtime의 직접·간접 상속·호출 체인이며, 나머지3개는 현재 렌더와 solver가 사용한다. `environment_v4/v5`, `prepared_reset_v1`, skill/imitation V1·V2와 기존 단계별 CLI도 현재 기본·전문 실행 또는 검사의 공용 기반이다. 버전 번호만으로 제거하지 않았다.

동시에 진행된 별도 v24 개발의 새 보관본 `20261026_before_finger_skill_v24`와 활성 소스 변경은 그대로 두었다. 해당 작업의 소스를 되돌리거나 이 정리의 변경으로 처리하지 않았다.

## 보관 위치와 검증 기록

- 외장 보관본: `/media/ajou/새 볼륨1/guitar_project_archives_20261023_v1/guitar_learning/archive/`
- 외장 검증 원자료: `/media/ajou/새 볼륨1/guitar_project_archives_20261023_v1/_unused_versions_cleanup_20261026_v1/`
- 이번 설정·문서 보관 manifest: [manifest.json](/home/ajou/yigyu/3/guitar_learning/archive/20261026_unused_versions_cleanup_v1/manifest.json)
- [최종 결과](final_result.json), [이동 목록](archive_transactions.json), [조사 결과](audit_findings.json)

보관본을 원래 경로에서 읽으려면 외장 볼륨 연결이 필요하다.
