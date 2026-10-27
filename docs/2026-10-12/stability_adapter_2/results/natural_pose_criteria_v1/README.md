# 자연스러운 연주 자세 기준 초안

이번 phase는 설계 기준을 정리한 문서 작업이다. 새 controller/reward 구현, native 물리 실행, actor 추론, 학습은 하지 않았다.

초기 기타 world 자세는 명목 초기 위치에서 **30 mm**, quaternion 최단 상대 회전에서 **5°** 안을 임시 검토 구역으로 둔다. 이후에는 연속 **1초** 동안 구간 시작 자세 대비 이동 **5 mm**, 회전 **1°**를 유지성 검토 기준으로 삼는다. 모두 영상 검토를 위한 잠정값이며 검증된 성공·생체역학 기준은 아니다. 구역 안에서는 초기 기타 자세로 복귀시키는 비용을 0으로 둘 수 있지만, 연주 오차와 잔여 drift·속도 및 자세 선호 평가는 계속 필요하다.

손가락은 8월 19일 자료의 관절별 p01–p99 분포를 부드러운 자세 선호로만 사용한다. hard limit나 분포 밖 실패 판정으로 바꾸지 않는다. 영상과 fret/strike 작업 기능을 함께 확인해야 하며 모든 손가락 또는 손바닥의 동시 접촉을 요구하지 않는다. 연주 prior, 접촉면, 관절 여유를 확인하기 전에는 자연스러움이나 연주 성공을 결론내리지 않는다.

현재 확인된 실험 기준은 `joint_only_fixed_strap_v1`의 절대 rest length **1.1018469719600776 m**다. 사용자가 말한 다른 환경의 원본/기준값은 아직 확인되지 않았으므로 이 값이 공통이라고 가정하지 않는다. 출처를 대조하기 전에는 새 자세마다 길이를 다시 계산하지 않는다.

아래는 **이전** `joint_only_fixed_strap_v1` native 실행에서 재사용한 손 카메라 자료다. 이번 기준 정리에서 새로 평가하거나 성공을 확인한 영상이 아니다.

![이전 joint-only 고정 스트랩 실행의 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/hands.mp4)

![이전 실행의 마지막 저장 손 프레임, frame 00150](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png)

기준 설계와 후속 확인 항목은 [자연스러운 연주 허용 범위 설계](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:9), [보정 설계](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:27), [단계별 실행 순서](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:35)에 기록했다. Root의 누적 기록은 [프로젝트 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1040)와 [계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1838)을 참조한다.
