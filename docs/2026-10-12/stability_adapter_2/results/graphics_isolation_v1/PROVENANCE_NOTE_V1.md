# 보존 예외와 정정 기록

초기 진단 v1은 60회 초기화 후 reference JSON을 learning ABI에 추가한 잘못으로 이행 단계에서 거절됐다. 물리 진행과 학습은0회였고 원본 소스/로그/report를 보존했다. 새 결과 디렉토리의 진단 v2에서 학습 입력과 감사 입력을 분리하여60회 초기화와전체trace/controls exact비교를통과했다.

그림 v2의 한글 글리프 누락과 README의 render0/probe순서 표현은 원문을 수정하지 않고 별도 README_V3 및 한글폰트 그림 artifacts_v3로 정정했다. 최신 설명은 [artifacts_v3/README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/README.md:1)이다.

artifacts_v3 producer는 v2의 보관 절차도 포함하여 video/archive_v4/manifest.json을 동일 내용으로 다시 썼다. 기존 파일을 쓰지 않기로 한 작업 소유권 조건의 예외였으며, 이를 숨기지 않는다. 영상들은 이미 존재하면복사하지않는분기였고 원본/보관영상SHA는일치한다. v2 provenance가기록한 manifest SHA와현재값은둘다 `2f1ef5aa65d8bc0b248cdc69bd755e3e6d0800a14bcac4c256d6d9637e7ef741`로바이트단위동일하다. 내용 변경이나 삭제는 없지만 파일 재기록이 있었으므로 '전혀 쓰지 않았다'고 설명하지 않는다. 이 producer는 보존용이며재실행하지않는다. 후속그림은영상보관절차와분리한새producer로만든다.

이 결과 기록은 물리·학습 재실행을 뜻하지 않는다. 기존 stability_adapter/와공용모델/이전실험소스는수정·삭제하지않았다. main4는 native 종료 후 기존prefix 보존 검사를하고append했으며 장기 재개 이후 다시동결했다.
