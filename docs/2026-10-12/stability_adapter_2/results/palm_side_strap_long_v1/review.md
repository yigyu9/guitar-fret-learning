# palm_side_strap_long_v1 독립 검수

검수일: 2026-10-07. 새 runner/analyzer/plotter와 이번0.5초 원자료·문서·영상만 검수했다.
수정은 이 기록뿐이며 다른 작업자 파일·이전 동결 리뷰·원자료는 유지했다.
검수 중 native 초기화·physics 실행·source replay는0회다. 영상 codec 읽기와 저장값 수학 대조만 수행했다.

## 요약 판정

문제없음. Critical / Warning / Suggestion의 남은 항목은 없다. 이 기록을 동결한다.

## 구현·원자료

- 짧은 runner와 diff를 확인했다. 기간120step·새 출력 경로·이전short6배열 prefix·매4step camera 저장만 추가됐고 task/bias/PI/목표 cap·rate/초기 q·기타목표/PD·절대 LA/root·하체 고정은 유지된다. 연속 state 덮어쓰기나 강제 손 부착은 없다.
- 5init/600steps, 각121상태·120제어/접촉·30update, 동일 초기 fullstate·네 short6prefix·camera/headless6raw exact를 확인했다. 62개 camera PNG는0/4/…/120step의31시점×2view이며 보고서 SHA와 일치한다.
- 저장5run의150update를 독립 대조했다. task 차이≤1.12e-16, PI/적분 rollback/최종 clipping 차이≤8.75e-16, float32 target 차이≤7.38e-8rad로2e-7rad 허용치 안이다. 잔차±.15rad·1rad/s와 최종 initial±.3∩native box를 유지한다.
- 모든 pre-step route/속도에서 수동 장력 law를 재계산해 다음 trace last_applied와 차이0을 확인했다. 생성 목표 기준 기타 p오차 차이는6.94e-18m 이하, 회전오차 cos 차이는2.23e-16 이하다. 종료 actual−target 좌표 차이와 요약값도 맞다.
- analyzer12계약/242개 입력 SHA는 현재 파일과 일치한다. 세 이전 inventory를 시작 전에 봉인하고 보존 검사를 수행한다. 출력 부재를 live analyzer 완료 전 읽은 기록은 별도이며 실제 분석은 같은 실행의exit0/0native/0physics다.

## 매체·문서·지적 해소

소비 입력을 읽은 뒤 SHA를 계산하던 Warning을 해소했다. 최종 plotter는84개 고정 경로를 데이터 읽기·helper import 전에 봉인하고 실제 소비 집합과 같음을 검사한 뒤 전부 다시 SHA 대조한다. 이전 producer·그림·영상·manifest는 보존됐고 최종4출력은 보존본과 byte-identical이다.
곡선·영상 첫/중간/마지막을 직접 확인했다. 실제 decode 시점은step0/60/120(t0/.25/.5)이며 native front/side와 같은 시점 source 표식을 사용한다. ffprobe 독립 확인은 두 영상 모두H264/1280×1440/31frames,60fps0.516667s 및6fps5.166667s다. 물리 구간0–0.5초와 끝 프레임 표시시간을 포함한 파일 길이를 구별한다. 새 simulation/render 없이 저장PNG를 인코딩한다.
84개 plot 입력·producer·4출력 SHA와 실제 경로/줄 링크가 맞다. 장력의 직전 step 시점·source 표식의 비cooked 의미·current가 이번 네 조건의 진단 기준이라는 제한이 명확하다. README:27의7.029°는 종료 actual−초기 actual 좌표 차이로 교정됐고24.218°도 native DOF 성분차이로 한정한다. SDK URDF 구면관절 예제를 이번MJCF 3hinge drive 인증으로 확대하지 않는 계획 설명이 맞다.

## 검수한 현재 소스 SHA256

| 파일 (`/home/ajou/yigyu/3/stability_adapter_2/`) | SHA256 |
|---|---|
| run_palm_side_strap_long.py | 21499334b1700365da1ab7c69aaff849ba7f1809b6ad119cf3c61bcad4015394 |
| analyze_palm_side_strap_long.py | 27ed5ac5a98aad1a763681a77ec8c5d8b2b3e602e261a66c33da6575e1408db9 |
| plot_palm_side_strap_long.py | 5014d8bf213e4de66680ff467c55528b7ecc28dcfd7c31f301a5431ad69fe110 |

## 최종 결과와 한계

최대 기타p/q는current53.538626mm/6.994315°,taut60.944152mm/9.231735°,5N60.592216mm/9.327781°,10N60.019756mm/9.534431°다. 짧은 길이의0.1초 개선은0.5초 개선으로 이어지지 않았다.
손바닥 접촉은마지막step2/2/3/4 이후 없고10N 양의 raw lambda도step1단1행뿐이다. 종료 속도·손이탈·관절 목표편차가 남으므로 안정성·지속 지지·연주 성공·원인의 단독 확정을 인증하지 않는다. 새 길이는 채택하지 않고current를 이번 비교의 진단 기준으로 남긴다. 역사 전체의 최적 조건 선정과는 다르다.
