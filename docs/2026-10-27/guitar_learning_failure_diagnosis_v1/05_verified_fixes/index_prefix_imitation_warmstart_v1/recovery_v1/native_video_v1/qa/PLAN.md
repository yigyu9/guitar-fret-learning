# 회복 초기화 모델 실제 영상 CPU QA

소유권은 이 qa/뿐이다. 원 1958준비/모델/영상/raw/원평가를 수정하거나 재렌더하지 않는다. root가 01_launcher completed/returncode0을 통보한 뒤에만 실행한다.

- [ ] 원 launcher/봉인/review/체크포인트 SHA·실제 원본 full native strict load와 metadata(PPO0, supervised1000), scene/encoder/alias/reference0 검증.
- [ ] 두 MP4 전체 CPU decode/ffprobe, 8대표 PNG 및 기존250/300 이미지 재사용 비교 sheet. 직접 upright/머리양발/가림 확인.
- [ ] 원128평가와 env0 354끝점 공통 raw·9항 episode원장·전128 guard scalar 비교. 미세/실질 차이를 모두 보존하고 재실행하지 않음.
- [ ] 소스+수치+픽셀 통합 독립검수 1회. env0 실패사례와 전체91/128을 구분하고 고정기타/F4/finite wrist/NN-only 초기화 범위를 명시.

새 시각 QA는 압력/자연스러움/해제 성공/자유기타J33/RL-only 증명이 아니다. evaluator fingerprint callback은 renderer에서 사용하지 않는다. 원본 CUDA strict load는 root의 실제 완료 경로로 검증하며 CPU에서 재수행하지 않는다.
