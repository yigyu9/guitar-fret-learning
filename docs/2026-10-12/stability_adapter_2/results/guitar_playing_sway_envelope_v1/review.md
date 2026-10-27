# 연주 흔들림 시각 범위 끝점 — 실행 전 검수

## 1차 사전 검수 — 2026-10-08

요약 판정: 수정 권장. Critical: 없음. Suggestion: 없음. 검수자는이review.md만생성/append하며target코드/native/producer를실행하지않고기존동결파일을수정하지않았다.

Warning:
- `/home/ajou/yigyu/3/stability_adapter_2/render_guitar_playing_envelope.py:26` — abs(angle)≤[18,15,15]만검사해custom입력의elevation-18°(절대4°)와recline-15°도허용한다. 계획14행의기준delta허용범위는elevation[-12,+18]/yaw[-15,+15]/recline[-5,+15]이므로각min/max를별도로검사해야추가조합도계획범위를지킨다. 기본13개JSON값은정확하다. 실행전에root에전달했다.

확인한 범위:
- endpoints.json은center1+XYZ각최소/최대6+elevation/yaw/recline각최소/최대6으로13고유ID다. 중심은originalbaseline대비translation0/semantic[0,0,3]이며몸통중심은이전기준과같다. 이동끝점의다른성분은같은선호중심으로유지된다.
- X/Y/Z끝점은±0.05m,넥상승각은기준22°대비-12/+18→절대10/40°,방위는기준5°대비±15→절대-10/20°,recline은originalbaseline대비-5/+15°다. 중심recline+3°대비로는-8/+12°다. 넥/yaw끝점의recline입력은+3°로유지한다.
- renderer21~36행은이전검수한semantic회전순서와bodycenter local[0,-.4,-.0217] pivot 보정식을유지한다. 넥상승은horizontal neck×up축좌곱,yaw는음의worldZ,recline은변경된neck축의음의회전이다. 각도는Euler XYZ절대각이아니며기존actor-root pivot과다르다.
- 65행은봉인된NoPhysics static Editor를viewer=False/strap=False로사용한다. 렌더/수동pose제출만있고simulate/step/force/encode호출은없다. per-case4checks는steps0/humanbody·DOF exact/extra-render전체state exact/API시도0을확인하고실패시종료한다(94~100행). 최종input SHA gate도저장뒤실패종료한다(103~108행).
- 기본입력hash는plan/renderer/baseline/endpoints와4재사용소스의8개,custom입력시9개다. 기본최대13/custom최대4와ID중복을검사한다. 원카메라2개와front/side2개를정적촬영하고PNG존재/size/SHA를기록한다.
- 계획16~18행은일정목표기준14mm/3°를실제fret/strike연주흔들림통계로설명하지않고,이번외곽은여유있는시각후보라고명시한다. 6축단독끝점이64모서리/연속경로/모든조합/실제도달·접촉·지지가능성을인증하지않는다. 고정손과기타끝점의불일치를이후팔·손추종설계문제로분리하고controller/gate/reward변경이나자동실험재개를하지않는다.

읽기전용AST Python3.8문법PASS/JSON13행13고유ID확인. target소스함수는분리실행/수치실행하지않았다. 기존회전수식사전검수결과와입력의정적수치대조만수행했다.

검수시SHA256:
- GUITAR_PLAYING_SWAY_ENVELOPE_PLAN.md: `e29bf01abd50e44734caa6a4269737f68aacd0c86631ce86f50c05035552133d`
- render_guitar_playing_envelope.py: `5dc99ef3e0ef4cd1ebb5306cd728e6df8986f09c622205526dafb78382ee8fcb`
- endpoints.json: `2d57b4b18a902a389c6f4dc320d7111f60c136624485e927ec9ccb695d439f49`

기본입력은적합하나custom하한보완후사전판정을갱신한다. 실제이미지/권장시각범위/최종문서검수는아직수행하지않았으므로전체최종PASS는보류한다.

## 새 v2 실행 전 재검수 — 2026-10-08

요약 판정: 문제없음. 실행 전 코드 판정: PASS. Critical/Warning/Suggestion 없음.

`/home/ajou/yigyu/3/stability_adapter_2/render_guitar_playing_envelope_v2.py:26`은semantic하한[-12,-15,-5]과상한[18,15,15]을별도로검사한다. 이전경고의custom과도하한허용이해소됐고기본13개JSON은변경없다. oldproducer/계획/원수학결과는보존하고v2와보완leaf를새파일로만들었다. source diff에서그외변경은runtimeinput목록에보완leaf를포함한것뿐이다. physics/render/회전pivot/상태검사/최종SHA실패gate는이전검수내용을유지한다. v2의기본runtimeinput은9개,custom추가시10개다.

보완leaf는실제새module을실행진입점으로지정하고물리0/사람상태유지/스트랩OFF/64조합미인증을유지한다. 저장math_checks_v2.json의34checks(13center+angle각2=26,범위거절7,AST1)가alltrue이고physics_steps0/puretransform범위임을읽었다. 검수자가이수학함수나target소스/native를재실행하지않았다.

v2 AST3.8 PASS. renderer source SHA256 `2f33db578fd8a363197ff7032f69492349f3ef2043c277801c6015e753dbc99c`. 보완leafSHA256 `fa123876db2301e8d6d3d95a364ddc3436ec3ce3f54b386868a6a375fd1b5f8d`. 원계획/endpoints SHA는위1차기록과같다. 검수자의변경은review.md append뿐이다. 실제13개이미지와최종문서이전전체최종판정은보류한다.


## 실제 결과 및 최종 문서 검수 — 2026-10-08

요약 판정: 현재 결과는 문제없음. 최초 후처리 버전의 완전 보존은 실패한 상태로 남는다. 검수자는 이 파일만 append했으며 코드/native/producer를 실행하거나 다른 파일을 수정하지 않았다.

Critical: 현재 산출물에 새 실행 차단 사유 없음.

Warning — 복구 불가한 과거 보존 결함:
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/README.md:83` 및 `/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_DECISION.md:24` — 최초 contact sheet 생성 뒤 gutter를 바꾸면서 첫 producer/그림이 보존되지 않았다. 최초 버전 보존 판정은 FAIL이다. 현재 버전 재생성과 SHA 일치는 그 유실을 복구하지 않는다. 원본 native와 현재 보존점 이후의 검증만 인정하며, 이 누락을 이후 inventory/보고에서도 계속 표시해야 한다. 최종 문서가 이 한계를 숨기지 않고 `final_verification.json:20`에 false로 기록했다.

Suggestion: 없음.

실제 수치·상태·그림 확인:
- 저장된 native/comparison.json은 중심 1개와 단일축 끝점 12개, aggregate 2검사 PASS다. 각 case의 4검사 PASS, physics_steps=0, 사람 body/DOF 원상태 exact, 52개 원본 PNG SHA exact를 읽기전용으로 대조했다. target 함수를 실행하지 않고 저장 p/q에서 독립적으로 도출한 바디 중심·semantic 각의 최대 차이는 1.3877787807814457e-17이었다. native runtime 입력 9개 current SHA도 일치했다.
- 실제 중심은 world [169.584541663,65.012345196,675.972975389]mm, 넥 22.000010312°/방위 4.999986929°다. 이동 끝점은 각 축 ±50mm, 넥 10.000010138~40.000005067°, 방위 -10.000016838~19.999990179°다. 앞판 correction -5/+3/+15°의 실제 법선 상승각은 약 0.555265429/7.968507525/19.038586008°다. README 9~18행과 DECISION 7~14행의 반올림·절대각/보정각 구분에 맞는다.
- front/side/hands 실제 v2 시트를 열어 행·열·끝점 라벨과 그림을 확인했다. Y/Z 변화에 따른 몸통·고정손 관계와 회전 side의 앞판 기울기 변화가 문서 설명에 맞는다. 넥 40° hands 원본의 헤드가 카메라 밖인 제한도 README 58행과 DECISION 22행에 명시했다. front를 전체 기타 판단 시점으로 사용한다. 시트 producer 132~149행은 aspect 유지 축소·셀 배치이며 원본 crop/기하변형/도형 overlay를 추가하지 않는다.
- 바디 중심 pivot과 actor-root pivot을 구분하고 앞판 correction을 절대 Euler각으로 오해시키지 않는다. README 77~79행, DECISION 16~20행은 이 범위를 팔·손 추종을 전제로 한 시각 제안으로 제한한다. 실제 연주 진폭·동적 유지·접촉/관통·스트랩 지지·팔 도달·64개 복합 모서리·연속 경로의 인증이 아니다. 기본 pose/controller/gate/reward/학습 변경이나 자동 목표 재개는 없다.

현재 보존점 및 최종 문서 확인:
- artifact_preservation_before_v2.json의 현재 파일 9개 SHA와 source_before_artifacts_v2의 선택 사본 3개 SHA가 모두 exact다. 여섯 현재 PNG는 원래 artifacts 경로에 유지되어 있다. 최초 버전의 별도 사본이 있다는 뜻은 아니다.
- 새 sheet v2 producer와 현재 original-path producer의 diff는 OUT 경로 한 줄뿐이다. 각 manifest의 bounded inputs 68개와 outputs 7개(6 PNG+mapping)가 모두 current SHA exact다. 두 경로의 PNG 6개 SHA가 모두 동일하다. source_final의 신규 8파일도 원본 및 final_verification 기록 SHA와 exact다.
- final_verification.json의 current_result_checks 16개 PASS와 최초 버전 보존 false가 구분되어 있다. 이전 phase 252파일 보존은 root의 확정 검사 결과를 참조했고 불필요하게 기존 검증을 반복하지 않았다.
- execution_before_v2의 사전 입력 15개 current SHA exact, main README/PLAN/VISUAL 기존 prefix 157379/229294/289350 bytes SHA exact다. 새 main append README 1368행/PLAN 2201행/VISUAL 2204행은 결과·한계·보존 누락을 정확하게 요약한다. 최종 README/CHANGED_FILES와 이 main 추가분의 절대경로 링크 94개는 대상 존재 및 지정 줄 범위를 확인했다.

최종 확인 SHA256:
- README.md: `885d8f288f8246b4aec109b8945aa1740219391f03d038e3ef87a194f379ea61`
- CHANGED_FILES.md: `e602b667dec7d5519551a94f891cb01382202c7a64de8be36149ad9e62e557aa`
- GUITAR_PLAYING_SWAY_ENVELOPE_DECISION.md: `6124bdc73480c1ed868c2ebacaf6bfbe8a3ec8c9377cb6f89da04d411d3cb2fc`
- final_verification.json: `a12258054dcea04212fec45adc9b191dd88badfabeb3117b745f72db35c64d89`

최종 판정: PASS (현재 수치·상태·원본 native 보존·v2 이미지·최종 문서 범위).
최초 contact-sheet producer/산출물 버전의 완전 보존 판정: FAIL — 복구 불가한 누락을 유지한다. 이번 PASS는 그 과거 보존 실패를 취소하거나 전체 이력 완전 보존을 인증하지 않는다.
