# V5 실제 마지막300 영상 독립 검수

**요약 판정: 문제없음 — PASS(실제 영상 무결성 범위).** 미해결 Critical / Warning / Suggestion 없음.

실제 replay의 완료·장면 close·alias 복구·입력 변경0과558개 봉인/실행 입력 SHA 일치를 확인했다. 원128명 전체 episode 원장은 선택한 마지막300 고정 평가와 exact다. env0의354개 q/target/body/candidate/정규화·decoded NN 목표도 exact이며, native_capture의 q/target/body가 같은 trace와 일치한다. force 차이는 최대3.814697265625e-6N으로 별도 보고하며 bitwise 동일을 주장하지 않는다. 모델/optimizer/update/checkpoint freeze도 유지됐다.

capture의354개 연속 control·240Hz 끝점과9보상 합·30fps frame cadence를 독립 검사했다. hand/fullbody MP4 모두 ffprobe상1280×720·177frame·30fps·5.9초이며 전체 frame 디코딩에 오류가 없다. 각 영상의1fps6개 시점 contact sheet를 직접 확인했고 손/넥이 보이며 fullbody는 정방향의 앉은 신체·기타를 보여준다. 영상은 사전 선택된 env0 첫 시도이며128개 환경을 모두 촬영한 것은 아니다.

이는 실패 모델의 정직한 마지막 영상이다. 최종 A달성/all3/joint는0/128이고 A해제105/128을 음악 성공으로 해석하지 않는다. 실제 현 압력·접촉쌍·음향이나 전체 원목표 해결도 인증하지 않는다. 검수에서는 CPU 분석과 영상 디코딩만 수행했고 추가 GPU/NN/물리 실행은 없다.
