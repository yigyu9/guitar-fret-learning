# 실시간 Fret 진단 v2 — native 픽셀 저장과 조회 중단

v1의 물리·제어·카메라·관측을 유지하고 native RGBA를 복사하여 PIL로 PNG 저장했다. 처음31frame/step0~240/물리1.0초를 완전히 기록한 뒤 `get_camera_image` 호출에서 exit139로 중단했다. 준비2초/정책 연결에는 도달하지 못했다. writer만의 오류로 확정할 수 없으며 원인 미확정, full live 검증은 미완료다.

공통 v1/v2 prefix 27frame×2view의 실제 RGBA는 모두 같았다. 기존 완료 baseline과의 31frame×2view도 동일 픽셀이다. 이 결과는 같은 초기 장면·저장 방식의 일치 증거이며 전체 live 성공이나 crash 원인 확인이 아니다. 입력은 종료 직후 root SHA 재대조에서 변경0이었고 모든 raw/표시 PNG·로그·부분 영상을 보존했다.

- [중단·입력 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v2/native_crash.json)
- [독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v2/review.md)
- [기존 완료 실행의 전체 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md)

![v2 마지막 완전 구간 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v2/partial_recording/whole_body.mp4)
