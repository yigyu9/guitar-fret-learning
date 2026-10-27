# seed17 최종 정책: 실제 손·전신 영상

원래 incremental seed17/300회 저장본을 수정 전 봉인 소스에서 실제128환경으로 재생했다. 사전 지정한 env0의 첫 시도를 촬영했으며, 이 시도는 압현 달성·clean100%·wrong0%였다. 별도128평가도 최종128/128이지만 연속 두 저장본 통과 기준에는 미달했다.

- [손 영상](incremental_final_300/hand.mp4)
- [전신 영상](incremental_final_300/fullbody.mp4)
- [입력·장면·인코더 검증](verification.json)
- [프로세스 종료0 근거](incremental_final_300_launcher.json)

두 영상은1280×720/30fps/109frame/3.634초다. 위아래 방향·전신 머리/발 포함을 실제 QA 프레임으로 확인했다.677입력 핀·장면 종료·launcher 종료0을 검증했다. 영상은 기타 고정·유한 손목 teacher·중지 한 음의 조건이며 자유 기타 전곡 성과가 아니다.

압현 성공과 부드러운 저부하 동작은 별개다. 같은 정책의 저장 env0 audible 중지 말단 합력 p95는69.83N이고 목표-실제 관절 오차도 컸다. [하중·관절 감사](../../04_ablation/policy_contact_load_audit/RESULTS.md)와 함께 해석한다. 몸체 합력은 접촉 상대가 분리된 현 압력 인증이 아니다.
