# 실시간 Fret 진단 v1 — 두 번의 카메라 중단

기존 무스트랩 초기값·제어에 현재 기타 기준 관측과 표시만 추가했다. 첫 시험은 마지막 완전 frame 27개/step208/0.866667초, 동일 재시험은 26개/step200/0.833333초 뒤 exit139로 중단했다. 두 stack 모두 기존 `gym_trial_recording.py:24`의 native `write_camera_image_to_file`다. 원인은 미확정이며 원본 task done/물리평형이 아니다. 준비2초/정책 연결에 도달하지 못했으므로 연주 결과와 full live 검증은 미완료다.

각 실행의 모든 보존 입력을 종료 직후 재대조하여 변경0을 확인했다. Python finally가 실행되지 않았으므로 wrapper의 inputs_after/report는 생성되지 않았다. 대신 root crash 감사와 부분영상을 별도 경로에 저장했고 원본은 유지했다. 다음 v2도 image 조회 중 중단되어 writer만의 문제로 확정할 수 없다.

- [첫 중단·입력 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/native_crash.json)
- [재시험 중단·입력 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/retry/native_crash.json)
- [독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/review.md)
- [기존 완료 실행의 전체 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md)

![첫 시험 부분 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/partial_recording/whole_body.mp4)

![동일 재시험 부분 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/retry/partial_recording/whole_body.mp4)
