# 산출물 이력과 provenance 보존 한계

이 문서는 왼손 분리 초기화 phase의 표시물 생성 이력을 기록한다. native 물리 원자료는 수정하지 않았다. 상세한 현재 SHA 목록은 [emergency snapshot](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/emergency_snapshot_v1.json)에 보존했다.

2026-10-14 약 13:17 KST에 산출물 담당자(GPT-6 Luna)가 `build_artifacts_v1.py`를 작성하고, 해당 producer와 입력 파일들의 SHA를 `preflight_pin_v1.json`에 실행 전에 기록한 뒤 실행했다. V1 이미지 두 장과 전신·손 MP4 사본 두 개를 생성했고 provenance도 기록했다.

같은 날 약 13:18 KST에 같은 담당자가 V1 레이아웃을 고치기 위해 새 경로의 `build_artifacts_v2.py`를 준비하려다 파일 복사/치환 실수로 기존 V1 producer 파일을 일시 수정했다. producer 파일은 사전 pin의 SHA와 일치하도록 byte-exact 복원됐음을 확인했다. V2 producer 실행에서 출력 provenance 경로가 잘못 지정되어 `provenance_v1.json`에 V2 생성 기록을 썼고, 그 과정에서 최초 V1 provenance 파일의 바이트를 덮어썼다. 최초 V1 provenance 원본의 별도 사본이나 SHA 스냅샷은 남아 있지 않다.

약 13:19 KST에 담당자는 pin에 보존된 producer SHA와 입력 SHA를 확인한 후 원래 V1 producer를 다시 실행해 `provenance_v1.json`을 재생성했다. 재실행 전후 V1 이미지 2개와 V1 MP4 사본 2개는 byte-identical임을 확인했다. 다만 현재 V1 provenance는 동일 입력과 동일 producer에서 재생성한 기록이며, 덮어쓰기 전의 최초 provenance 바이트와 같다고 인증할 근거는 없다. 원래 provenance의 정확한 기록 내용·바이트 동일성은 복구할 수 없다.

이후 V3 producer 실행 전 producer와 실제 읽을 입력 SHA를 `preflight_pin_v3.json`에 저장했다. V3 provenance는 해당 입력 및 producer의 전후 SHA를 기록하고, 이미지 V3 두 장과 기존 V2 영상 사본의 SHA/ffprobe를 연결한다. 이 최신 자료는 현재 재생성/검증 범위를 나타내며 최초 V1 provenance를 소급 복원하거나 인증하지 않는다.

현재 확인한 결과 native run의 JSON·PNG·MP4 원자료 SHA는 생성 전후 동일하다. 원자료의 파일 목록과 SHA는 emergency snapshot에도 담았다. 별도 native physics 재실행이나 영상 재인코딩은 하지 않았다.
