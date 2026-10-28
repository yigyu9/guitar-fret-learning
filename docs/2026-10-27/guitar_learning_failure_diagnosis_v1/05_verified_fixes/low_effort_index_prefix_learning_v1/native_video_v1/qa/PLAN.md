# 3음 정책 영상 실제 CPU QA

root session16092의 두 장면 실제종료0 뒤에만 실행한다. 소유는 이 qa/뿐이며 준비1815·renderer·모델·원 평가·영상/NPZ를 변경하지 않는다. GPU/native 재실행은 없다.

- 완료 guard/self-check 뒤 원 selection/학습 actual PASS/준비1815·현재SHA를 검증한다.
- 두 장면의 strict 원본 load 성공 경로/모델·checkpoint 불변/업데이트/128cap·90쌍/종료·alias·encoder·시계를 확인한다. evaluator fingerprint callback 사용은 주장하지 않는다.
- env0 각354끝점의 관절·목표·행동·3음 candidate/wrong·해제·손목·합력을 고정평가와 대조한다. exact 여부와 차이를 그대로 기록하고 합력 허용오차를 새 성공조건으로 만들지 않는다. 원9보상은 env0 원장 성분을 비교하며 미저장 tick별9보상을 재구성했다고 주장하지 않는다. 전128은 작은 sidecar만 원 평가와 비교·기존 helper 검산한다.
- 4MP4 ffprobe와 전체decode, 각4대표PNG(총16), 카메라별비교·모델별sheet4개를 만든다. frame n=control endpoint2(n+1), t0 frame 없음. 직접 이미지를 본 뒤 upright/머리양발/손가림을 별도 VISUAL_QA에 기록한다.
- 자체검사→actual 실행→소스·수치·픽셀 통합 독립검수1회. 선행 acquired/carry 준비검수 뒤 기존 reviewer를 재사용한다. 완료 후 qa 전체동결한다.

best250/latest300은 원 사전순위의 실패 모델이다(all3/release0). env0 두 영상으로 전체128 압력·자연스러움·자유기타/J33 성공을 인증하지 않는다. 몸체합력은 쌍별압력/torque/240Hz 최대가 아니다.
