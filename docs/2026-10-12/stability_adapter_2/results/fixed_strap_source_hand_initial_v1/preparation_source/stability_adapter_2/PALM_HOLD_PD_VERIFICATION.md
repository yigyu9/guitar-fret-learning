# PD setter 성공 반환값의 보완 검증

첫 palm_hold_pd_v1의 3init/72step은 모두 exit0이며 실제 property readback과
초기 state/target 보존 검사가 통과했다. 그러나 독립 검수는 PD setter의 bool 반환값을
누락한 점을 지적했다. 특히 배율1에서는 setter가 실패해도 기존 property와 같아
readback만으로 성공을 증명할 수 없다. 첫 producer·자료는 그대로 보존한다.

run_palm_hold_pd_verified.py는 SDK setter가 false이면 즉시 중단하고 기존 실패 저장/
scene close 경로를 사용한다. 같은 세 trial을 각각24step 새로 실행하며 새 출력은
palm_hold_pd_v2다. 계획·초기각·목표각·LA·PD 배율·solver는 첫 비교와 같다.
검증된 각 원자료5배열과 첫 비교의 같은 배율을 대조해 보완 부작용도 검사한다.
최종 PD 비교 분석은 새 v2를 사용하고 첫 v1은 반환값 미확인 실행으로 명시한다.
물리 실행 집계는 v1 3init/72step + v2 3init/72step으로 구분한다.
