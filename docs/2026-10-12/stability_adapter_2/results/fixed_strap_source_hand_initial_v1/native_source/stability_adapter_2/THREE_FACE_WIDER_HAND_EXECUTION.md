# 왼팔·모든 손가락33 초기각 검색 실행 계약

[기본 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_WIDER_HAND_INITIAL_PLAN.md:1)을 따른다. 이전 sliding source SHA7f2c51f8…를 실행 metadata와 대조하고 새 phase에 exact복사했다. 실제모델/기타목표/스트랩/PD/solver를 바꾸지 않고 초기기하 후보만 만든다.

- 원래 half actual81q를기준으로 왼팔12±.15rad/손가락21±.30rad를 native/Aug19/C02팔±.30/old81T 차이±.30rad와교차하고float32제출가능범위로제한한다. 다른48 초기각과기존절대81목표를유지한다. 최종양팔·양손66제어권은같다.
- 엄지1462·clearance0.3mm와palm GY45mm/GZ4.5mm 목표를 유지한다. 전면source지점4개는 각평가시 현재GXY를유한전면(X끝3mm/Y끝5mm 안쪽)으로제한해높이11.230006mm+.3mm로접근한다. 이동영역 안에서는XY위치를고정하지않는다.
- 기존4 source분리쌍에약지/소지를포함한4 distal finger–guitar/fret3/fret4를더해12쌍으로확대한다. 원래 분리항이point오차와교환되어작은source교차를남긴6실패자료를근거로, source SAT분리항계수를5,000→50,000/m로높인다. Thumb/palm–root guitar의clearance선호도같은계수다. 이는 초기검색의잔차계수이며물리contactstiffness/외력/gain을변경하지않는다. 최종LP/패치여유/거리구간/up hemisphere/rear witness gate는완화하지않는다. Multi-change탐색이며단일항인과효과로해석하지않는다.
- Seed20261012로기준3개,sliding최저max(th,palm)결과주변±.05rad perturb4개,범위내uniform5개를총12개기록한다. 내부추정값clip은optimizerstartingguess에만사용한다. 실제native 초기각은최종float32기하검사를통과해야하며겹침있는seed를그대로실행하지않는다.
- 12 source검색은각150 nfev상한으로처리한다. 최종q의max좌표차가1e-4rad미만인accepted중복은native선택에서제외하고거절사유에명시한다. 서로다른source통과2개면남은seed검색을중단한다. 실제처리수와요청12개를구분한다.
- 통과후보 최대2개는 personalized proposal을 기존run_seed2_support_warmstart에전달한다. Fresh actual81q/FK/전체source초기검사 후 자유기타5초/1200step·초기값/전신·손0~5초151frame을남긴다. 다른목표48/root하체exact/몸통9목표 및 actualdrift도기록한다. 초기배치와PD목표차이를줄인새제어는별도조건에서후속검토한다.

독립검수 재시도는이번작업시작에서도agent thread limit 오류로실패했다. Root가문법/unchanged거리helper/33bounds/새frontprojection/seed재현성/기존입력보존을검증한다. 완료했다고주장하지않고다음단계에서독립검수를재시도한다. 기타고정·손부착·반복pose덮어쓰기·기타목표외력은없다.
