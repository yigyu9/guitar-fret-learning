# 정적 기타 자연스러움 범위 비교 검수

## 실행 전 1차 검수 — 2026-10-08

요약 판정: 수정 권장. Critical: 없음. 아래 Warning 2건의 작은 보완을 root에 전달했다. 검수자는 이 문서만 생성/append하며 소스·봉인 결과를 수정하지 않고 native/물리/이미지 생성을 실행하지 않았다.

Warning:
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:113` — inputs_unchanged=false여도 최종 JSON 저장 뒤 exit0로 끝난다. 최종 checks 저장 후 all(checks.values())를 확인하고 실패 종료해야 입력 보존 gate 실패와 terminal 성공을 혼동하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:63` — custom --cases도25개까지 허용하지만 계획7행의 추가 조합 상한은5개다. 기본25단독 배치와 별도 입력1~5개 상한을 구별하는 것이 계획과 맞다.

Suggestion: 없음.

정확성 검산:
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:15` — baseline1+world XYZ 각각4개+회전 semantic3축 각각4개로25고유cases다. 회전 delta는 Euler 절대각이 아니다.
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:37` — horizontal neck과 up의 cross 축을 좌곱하므로 양의 elevation이 넥을 올린다. yaw 음의worldZ 회전은 atan2(neckY,-neckX) 방위각을 양으로 증가시킨다. recline은 변경된 neck축의 음의 회전이며 기준 근방에서 앞판 법선의 up 성분을 증가시킨다.
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:44` — 원 바디 중심에 world translation을 더하고 최종 회전된 local pivot을 빼서 root 위치를 보정한다. source guitar_asset.xml124행의 G:body local[0,-.4,-.0217]m와 일치한다. 회전시 actor-root pivot 대신 바디 중심을 유지한다.
- 순수 함수만 AST로 분리해 native import 없이25개 수치 검산했다. 실제 baseline native quaternion 기준 elev22.000006848161476°/yaw4.999987562984339°, body center [0.16958455647776322,0.06501234368976472,0.6759729904591529]m다. 단독 elev/yaw 변화는 지정 delta와 일치하고, 모든 case의 기대 body center와 계산값 차이는최대1.7554167342883506e-16m다. recline -10/-5/+5/+10의 앞판 법선 elevation은 -4.0800840/0.5552694/9.8191522/14.4373142°다. roll 보정값을 법선 elevation의 동일 덧셈값으로 설명하면 안 된다.

물리·기록 범위:
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:73` — 검수·봉인된 물리차단 static Editor를 viewer=False/strap=False로 사용한다. pose setter와 정적 render/capture만 호출하고 simulate/step/force/encode를 호출하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:80` — 기존 whole-body/hands에 별도front/side camera를 생성하고 설정을 기록한다. 카메라 쓰기 API의 None 반환을 실패로 취급하지 않고 실제 file/size를 확인한다(97~100행).
- `/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:102` — 매case zero steps, 초기 human body/DOF exact, 추가 camera render 전후 전체native state exact, physics API 시도0을 확인한다. 기본 camera capture의 render-readonly 검사도 재사용한다. 각 후보는 실제native p/q와 static플래그·입력·네 시점 PNG로 보존된다.
- 입력 snapshot/hash는 지정7개, custom입력시8개다. 기존 historical closure를 재복사하지 않는다. 원자동목표/학습중단을 유지하며 표본의 시각비교를 접촉·연주가능·모든 min/max 조합 보장으로 확대하지 않는 계획을 확인했다.

AST Python3.8 문법 PASS. 검수시 renderer SHA256 `140a8b979f23ebad3b26c9f1a2e3ff624057be8e6ae1d19d7b8fae05096ad301`, plan SHA256 `c3b25c1c2f4e025be2d708e2cb5bd2df77cd55842ddd11c2f9987a1c01fa3cd4`.

실제native 결과/시각적권고/최종문서는 아직 검수하지 않았으므로 최종봉인판정은 보류한다.

## 보완 후 실행 전 검수 — 2026-10-08

요약 판정: 문제없음. 실행 전 코드 판정: PASS. Critical/Warning/Suggestion 없음.

`/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:63`은 --cases일때상한5/기본25를구별한다. 112~117행은 final_checks를저장한뒤all값을확인하고불일치시AssertionError로실패종료한다. 위2개경고는해결됐고, placement/metrics/물리차단/정적capture경로는이전검수내용을유지한다.

수정 renderer AST3.8 PASS, 최종 사전 source SHA256 `1cf567f30af3f562e88d30fd40b849e0fb1eb1ec97cbff55dbd3ceb77c5430c4`. 계획SHA는위기록과같다. 검수자의native/물리/harness/이미지생성실행은0회이며순수수학수치검산만수행했다. 실제25case결과와문서이전전체최종PASS는기록하지않는다.

## 실제30개 저장 결과와 권장안 사전 검수 — 2026-10-08

요약 판정: 현재 실제자료/제안문서 범위 문제없음. 최종 산출물 문서와 main 추가분 검수는 아직 대기한다.

native25개와 combined5개 모두 aggregate2checks=true/physics_steps0이며 개별4checks=true다. 총30개의 native_state에서 human body/DOF가 각 fresh initial_state와 exact하고 step0이다. 후보 JSON은 physics_enabled=false/strap_enabled=false/strap_visible=false다. 두 실행의7/8inputs current SHA와 네시점120PNG SHA를 독립 읽기 검산해 모두exact를 확인했다.

30개 후보 pose.json의 절대 p/q로 bodycenter/neck elevation/neck audience yaw/front-normal elevation을 재계산해 comparison의 해당 metric들과 차이0을 확인했다. 추천 preferred_recline3는bodycenter[169.5845416631,65.0123451962,675.9729753889]mm,neck22.0000103115°/yaw4.9999869287°/front-normal7.9685075248°다. 입력recline+3°를앞판법선절대각3°또는기존8°Euler로설명하지않는다.

`/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md:16`의권장중심169.6/65.0/676.0mm,22°/5°/기준대비recline+3°와실제법선7.97°는저장자료rounding과맞는다. 20~27행의X±20/Y-10..+20/Z-10..+20mm,넥17..27°/방위0..10°/recline0..+5°는주관적시각탐색범위이며보간값과모든조합미인증을명시한다. 넥22°에한정한법선5.19..9.82°설명도정합하다.

proposal27행은bodycenter pivot과기존editor actor-root pivot의차이및추천JSON load를안내한다. 31~35행은기타자체배치와현재고정손정렬을구별하고±5mm/±1°의작은시작제안도접촉/관통보장이아님을밝힌다. 임의성공gate·학습재개·연주가능성인증은추가하지않았다. DECISION/combined.json5행의범위와실행결과ID·입력도일치한다.

`build_static_guitar_range_artifacts.py`의기본6sheets는기존nativePNG의라벨/축별표시와resize만수행한다. artifact_manifest의128bounded inputs 및output SHA가모두currentexact다. rotation-side contact sheet와추천candidate hands 원nativePNG를직접열어비교했다. 회전sheet열±5/±10은기준대비delta이며proposal의절대넥/방위각과구별해서캡션에써야함을root에전달했다. 추천그림을손의완전정렬·지지/접촉/연주자세인증으로해석하지않는다.

검수자는native/물리/producer/그림생성을재실행하지않았다. JSON·해시·순수metric재계산과기존PNG보기만수행했다. 추가combined산출물/최종README·색인·main문서가준비되면이어검수한다.

## 최종 산출물·문서 검수 및 동결 — 2026-10-08

요약 판정: 문제없음. Critical: 없음. Warning: 없음. Suggestion: 없음.

최종 결과 README와전체색인을검수했다. `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/README.md:3`의추천중심·22°/5°/recline+3°·법선7.97°는앞서검산한원자료와일치한다. 20~22행은주관적보간범위/모든조합미인증/bodycenter와actor-root pivot차이/semantic각과Euler각차이를설명한다. 26행은고정손정렬과기타자체배치판단을구별하고,36행은회전sheet열이baseline대비delta임을명시한다. 59~61행은물리0/원형상·humanoid상태유지/기타p,q만변경/기본시작값미교체와접촉·연주가능성미인증을정확히기록한다.

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/CHANGED_FILES.md:7`부터계획/renderer/제안/결정·입력/25native/5combined/기본6sheet와combinedproducer·mapping·manifest/최종본문을전체색인한다. 29행의main참조README1362/PLAN2192/VISUAL_REPORT2195도실제섹션에연결된다. 결과README/전체색인/제안문서의절대링크41개가존재하고명시줄번호도범위안이다.

combinedproducer의파일보존·입력SHA·상태0·원본PNG SHA검사와aspect-preserving배치코드를읽었다. 실행하지않았다. combined artifact manifest의28inputs와outputs currentSHA는전부exact이며15셀은입력5개순서×Front/Side/Hands3행과맞는다. 실제combined sheet도열어추천첫열/19°/25°/전방·위1cm/오른쪽1cm와라벨·원native형상을대조했다. 기본6sheet와raw30case검수결과는위기록을재사용했다. 접촉·관통·지지인증을이미지에서추론하지않는다.

`verification.json`은14checks alltrue/25+5/physics_steps0/physical_trials0,이전staticphase58파일보존검사완료를기록한다. 새7source의current SHA와source_final사본SHA를verification의new_source_sha256과각각대조해모두exact를확인했다. Python3소스는AST3.8문법을읽기전용확인했다. 큰historicalclosure재복사나native/producer재실행을하지않았다.

main추가분7상대링크는AGENTS의절대경로규칙에맞게root가보완했다. 수정전tail은main_append_before_link_fix.json에보존됐다. 현재7링크는전부절대경로/존재하며,execution_before_v2에저장한main3파일의원prefix SHA는여전히exact다. 새추가문구는자동물리실험/학습의중단유지,시각제안과미인증범위,bodycenter pivot을정확히설명한다. 원소스·원자료·봉인결과변경은없다.

최종 결과문서 SHA256:
- README.md: `ed088f688e17c8a43a44f78e0f44389f91ad402c8bd86a416301452cb98872bd`
- CHANGED_FILES.md: `af7c3e8d0023d356382302dc39bbacb86a9566745d89ac025045aaa32c2a8a2a`
- STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md: `3efd9aed028020e011669be021a59807d71ba354a78a7f2227a295b7695926b7`

최종 판정: PASS

판정범위는새정적renderer·30개저장결과의수학/상태·기본/조합산출물과시각적제안·최종문서·보존검사기록의정합성이다. 자연스러움자체의정답·모든범위조합·물리적지지·연주정책성공을인증하지않는다. 검수자의변경은이review.md생성/append뿐이며native/물리/harness/producer/그림생성실행은0회다. root가이후생성할현재phase artifact_inventory.json의완료를미리주장하지않는다. 이기록을마지막으로review.md를동결한다.
