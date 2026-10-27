# 환경 연결 검수 후보 정정

현재 검수 후보는 [environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/environment_v3.py), [test_environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_environment_v3.py), [run_smoke_v6.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/run_smoke_v6.py)이다. [이전 구현 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/implementation/bridge_v1.md)의 제어 구조는 유지하며 최종 파일 버전만 이 문서로 정정한다.

원 upper81 codec은 수정하지 않았다. 환경이 내보내는 메타데이터 사본에서 기존 고정 하체 관련 설명을 현재의 유한 하체24 foot 유지 제어 범위로 바꿨다. 이 사본이 원 codec 메타데이터를 바꾸지 않는 검사까지 CPU 테스트 총8개가 통과했다. native 실행은 아직 하지 않았다.

원 native runtime·모델 자산은 원 baseline의 expected SHA와 엄격 대조한다. 신규 환경 및 재사용한 music_pipeline_v2/v3 CPU 코드는 원 native 실행에 없던 연결 의존성이므로 별도로 분류하고, 실행 전후 SHA와 CPU 검증을 적용한다. 실제 실행 뒤 가져온 프로젝트 모듈이 사전 SHA 목록에 없으면 보고하고 실패 처리한다. candidate와 support JSON은 직접 포함하며 과거 결과 링크 전체를 재귀 순회하지 않는다.

각 실제 trial의 0초 초기 상태·속성 및 22초 준비 완료 native 상태·기타 좌표계 형상을 별도로 저장한다. 카메라 인코딩 오류가 생겨도 입력 대조와 보고서를 남기며, 원 물리 예외를 인코딩 예외로 대체하지 않는다.

- 환경 SHA: `124f3556ffece4f3416973e50d34b5b6517fb3e17c3261474a125282ff35d4f7`
- 테스트 SHA: `8f10691eb90ea220cebfd48e6738e87e2e0f3de8dbff2ccc1dfedf52778f883e`
- 실행기 SHA: `566e94294a1ac54c5069e7ad5b40913651ffb88fca552e70c337ad4489352090`
