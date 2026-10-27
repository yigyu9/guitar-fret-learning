# 신규 자유 기타 코드 정리

현재 개발 기준을 [free_guitar_learning](/home/ajou/yigyu/3/free_guitar_learning/README.md)으로 분리했다. 환경·기하·압현 측정·제어 규약·실행기·검사를 모으고, import와 프로젝트 루트 및 소스 감사 경로를 새 위치에 맞췄다. 물리 제어와 접촉 기준은 변경하지 않았다.

과거 실험이 소비한 원본은 원래 위치에 보존했다. 새 디렉토리의 archive 링크는 이 원본으로 연결되며, 현행 코드와 이전 실패/버전을 구분한다. 현재 환경에 아직 연결하지 않은 과거 정책/PPO 초안은 개발 코드에 섞지 않았다. native 초기 자세·제어기와 공용 모델 자산은 기존 프로젝트 경로를 참조한다.

- [원본 대응 목록](/home/ajou/yigyu/3/free_guitar_learning/origin_manifest.json)
- [CPU 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_code_organization_v1/cpu_result.json): 40개 검사와 두 실행기의 도움말 확인 통과.
- 새 경로를 source census와 사전 pin 목록에 포함했다. 최상위 패키지의 __init__.py도 수집하고, 원본 native 소스와 새 개발 코드를 구분한다.
- 최초 경로 점검에서는 복사한 제어 검사 3개의 프로젝트 루트가 이전 깊이를 사용해 파일을 찾지 못했다. 새 경로로 수정하고, 최신 제어 검사 한 버전만 남긴 뒤 전체 40개를 통과했다.
- 새 물리 실험/PPO 업데이트는 0이다. 기존 native 성공은 원본 소스의 결과로 보존하며 정리 후 버전의 native 성공으로 소급하지 않는다.

과거 결과 README/소스/원자료는 이번 정리를 이유로 수정하지 않았다. 앞으로 새 코드는 최상위 free_guitar_learning에서 작성한다.
