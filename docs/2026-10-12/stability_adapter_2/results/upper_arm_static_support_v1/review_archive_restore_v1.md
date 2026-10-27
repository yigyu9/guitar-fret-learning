# 누락 보관 영상 복구 보완 검수

요약 판정: **문제없음 — 기존 영상 한 개의 바이트 복구 범위.** [복구 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/archive_restore_and_seal_retry_v2.json:1)의 원본과 목적지를 직접 읽어 비교했습니다. 현재 [원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/eval_noise_4_v1/native/episode_0001/media/whole_body.mp4) 및 [복구 보관본](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/noise4_whole_body.mp4)은 모두824,424바이트이며 전체 바이트와 SHA256 `7035bc6cd848b4ab3d74f54e5defaba664b3271efb3c5aa18905d21a9d485bb2`가 일치합니다. 재인코딩·새 물리 실행의 결과가 아닙니다.

기록에는 첫 봉인이 이전 보관본 누락으로 snapshot/inventory 생성 전에 실패했고 누락 목적지에만 복구했으며 기존 파일 덮어쓰기0이라고 명시되어 있습니다. 봉인 소스의 이전 inventory 검사 위치가 최초 출력 쓰기보다 앞인 점과 현재 소스 SHA `8c57bb3bdd4c05f8c8fcd537c09086c0b7f5cae934ed99c4a384b1a2ea0f6242`의 정합성을 확인했습니다. 누락 발생 원인과 복구 전 파일시스템 이력은 독립적으로 확정하지 않습니다. 재시도 봉인 성공 여부는 root의 별도 결과 대상입니다.

[기존 최종 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/review_final_v2.md:1)의 현재 SHA는 `a1f35f017b670ee66a809901ab4f6a3169eda5e482a11913c2d8159b6d935bdc`로 저장 완료 때와 동일합니다. 복구 기록 SHA는 `cbed3c9829238a7d5f650abb04973b757a95ff0888d1122d8fb254eb7f2a90c8`입니다. 검수자는 이 새 문서만 작성했으며 복구·봉인·native·학습을 실행하지 않았습니다.
