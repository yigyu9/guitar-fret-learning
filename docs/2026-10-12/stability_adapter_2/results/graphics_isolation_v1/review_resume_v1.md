# 검증 체크포인트 재개·영상 보관 supervisor 사전 검수

요약 판정: **문제없음(보관 수정 반영 후)**. 검수 대상은 [launch_recorded_learning_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:1)와 재개 입력 식별 근거다. 추가 native·학습 실행 없이 읽기 전용으로 확인했으며, 새 장기 실행의 완료를 인증하지 않는다.

## Critical

없음. [58행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:58)은 verification passed와 모든 입력 SHA를 확인하고, 검증된 CP242에서 같은 runner9의 strict load로 CUDA·스트랩 ON·30분 공식 평가·11:40 cutoff를 유지한다. [verification_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json:1)의 모든 checks가 true이며 현재 입력 39개의 SHA도 직접 대조해 일치했다. 기록상 probe v2의 60회 reset·전체 궤적 exact, 실제 CUDA 1갱신·최종 KL 0.0199047048·RMS 고정·양쪽 3,928 물리/982 제어 단계가 확인된다. 이것은 유한한 검증 범위이며 보편적 무충돌·음악 성공 보장은 아니다.

## Warning

미해결 항목 없음. 최초 후보는 manifest 파일이 존재하기만 하면 완료로 건너뛰어 부분 JSON을 놓칠 수 있었다. 최종 [save:10](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:10)은 임시 파일 flush/fsync 후 os.link로 완전한 JSON을 배타적으로 게시한다. [28행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:28)은 기존 manifest를 파싱하고 native report·원본 영상·보관 영상 SHA를 확인한 뒤 재사용한다. manifest 없는 재시도에서도 기존 README는 [49행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:49)의 예상 문구 exact 검사 후에만 재사용한다. 이 수정으로 앞선 경고는 해결됐다.

[18행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:18)의 보관은 evaluation_records가 가리키는 실제 native report에 MP4 두 개가 있을 때만 진행한다. 원본 SHA 확인→배타적 복사→사본·원본 SHA 재확인 순서를 유지하며, 정상 완주와 부분 종료의 사유·길이·음악 판정을 한국어 README에 구분한다. [67행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:67)의 약 20초 순회와 종료 직후 보관은 학습을 변경하지 않고, 보관 예외를 별도 exit record에 남긴다. 저장·평가·cutoff가 실제 실시간 간격이나 네이티브 호출 강제 선점을 보장한다는 의미는 아니다.

## 검수 SHA·범위

최종 supervisor SHA256은 `de7b1d69547f16655f34d2d38260dc6793927effb30686d17ef9346d2cd09b0a`, verification SHA256은 `a764665c6f14c61407611fe24776e80a826069dcd7703d8e61fae5dd8c0ea9dd`다. 이번 검수에서는 새 보관 폴더의 실제 생성·영상 추가·장기 학습 갱신이나 최종 결과를 판정하지 않았다. 소유한 이 새 리뷰 외 파일을 수정하지 않았다.
