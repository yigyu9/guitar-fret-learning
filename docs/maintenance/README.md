# 정리·검증 기록

이 디렉토리는 정리 작업의 근거다. 현재 학습 명령이나 새 실험 결과는 [문서 색인](../DOCUMENT_INDEX.md)에서 찾는다.

| 기록 | 확인할 내용 |
| --- | --- |
| [pc_storage_cleanup_20261104](pc_storage_cleanup_20261104/REPORT.md) | 미사용 홈 파일7,293개·Docker 이미지2개 정리, 활성 앱 캐시와 관리자 인증 필요 항목 보류 |
| [pc_storage_audit_20261104](pc_storage_audit_20261104/REPORT.md) | PC 전체 읽기 전용 용량 점검, 캐시·시스템 기록·개발 환경 후보와 별도 데이터 디스크 접근 오류 |
| [storage_cleanup_additional_20261104](storage_cleanup_additional_20261104/REPORT.md) | 완료 원시 로그·미사용 VS Code 설치본·다운로드/생성 캐시 추가 정리, 사용 중 서버와 최종 근거 보존 |
| [storage_cleanup_20261104](storage_cleanup_20261104/REPORT.md) | Git 임시파일·검증 사본·비대표 영상·원시 로그 정리, 대표 영상과 고유 실행 결과 보존, LFS 원격 누락 점검 |
| [organization_20261031](organization_20261031/REPORT.md) | 현재/재현용/폐기 가능 분류, 계획 이동과 링크 검증 |
| [self_contained_20261031](self_contained_20261031/REPORT.md) | Git 정책·내부 입력 제한·팀원 전달 파일·GPU 학습/평가/영상 검증 |
| [project_cleanup_20261031](project_cleanup_20261031/REPORT.md) | 구형 원시 로그42개·캐시717개 삭제, 중복44쌍 통합 |
| [document_cleanup_20261030](document_cleanup_20261030/code_guide_validation.json) | 이전 대표 문서·코드 해설 대조 |
| [storage_cleanup_20261030](storage_cleanup_20261030/result.json) | 이전8시간 학습 원시 로그3개 삭제 |

`before/`는 변경 전 원문, manifest·SHA·validation은 실제 삭제/보존·검증의 근거다. 단순 임시 파일로 분류하지 않는다. 과거 catalog의 경로 목록은 당시 위치를 기록한 것이며, 이후 이동 목록과 함께 읽는다.

검증 과정에서만 만든 독립 프로젝트 복사본·캐시는 역할을 마친 뒤 정리할 수 있다. 단, 현재 native 런타임·빌드 캐시와 실행 중인 프로세스의 파일은 제외한다. 실제 정리한 임시 자료는 각 작업의 manifest에 기록한다.
