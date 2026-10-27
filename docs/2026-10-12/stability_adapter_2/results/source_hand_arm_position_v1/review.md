# 팔 위치 source74제안 코드·수치 계약 검수

요약 판정: **문제없음(PASS)**. 확인한 코드·작은 독립 수치 계약에서 실행 blocker는 없다. 소유 파일은 이 review.md뿐이며 기존 review/소비 소스·타인 파일을 수정하지 않았다. Geometry/FK/search/native/분석/렌더/감사 main은 실행하지 않았다. 요청 당시 미소비 코드의 읽기 검토로 시작했으나 수치 확인 종료 시 search.json이 이미 존재함을 관측했다. 실제 source 출력/선택/native 결과는 아직 검수하지 않았으며 이번 PASS를 해당 실행 완료 판정으로 사용하지 않는다.

- [74제안 생성](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:95)은 원source-hand5와 Wrist_y−.10가설 두 seed에서 각seed자체1+Thorax/Shoulder/Elbow9축×4delta=37조건씩이다. 최대 두 초기축을 원baseline 기준 actual float32 delta로 표현하고 arm12 조건부모델에 전달한다. 실제 finger1 계층을 유지하며 손목13조건의 baseline/seed HG를 [허용오차1e−10m로 재현](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:163)해야 한다. 새 FK/native 정확성 인증은 아니다.
- [범위 제외](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:105)는 기존left33offset을 float64로 더한 raw→float32목표와 초기81·held81·손목sin±.005양끝을 먼저 검사한다. 위반이면 raw초기/target·위반좌표/값/bound를 기록하고 source_evaluated=false/source_clear=false/geometryNone로 빠져 geometry나native에 넣지 않는다. 빈교차 결과로 통과를 위장하거나 clipping하지 않는다. 검수자가 원raw/범위/offset으로74개를 독립 재조립해 **68안전·6제외**를 확인했다. 제외는 각seed에서 Thorax_x−.025/−.05 및 Thorax_y+.05, 총6개이며 초기/held/손목양끝에서 같은해당축 위반이다. 비변경79/80각·held exact, 안전조건의 전체81native/effective범위·offset±.3·손목양끝도 통과했다.
- [이동 형상:76](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:76)은 L_Thorax XML subtree 전체를 유도한다. XML 직접검산상26 body에 pad/top 포함, Chest는 제외돼 body9목표/root하체와 구별된다. [affected union:144](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:144)은 실제 바뀐 각축의 body subtree를 합쳐 그 밖의 predicted upstream pose만 고정검사한다. 팔 변화에 따라 움직여야 하는 shoulder/elbow/wrist를 잘못 고정하지 않는다. 손 palm 이하 parent-relative 계층과 whole-LThorax 밖 mesh identity도 검사한다.
- Source 검사에는 전체 human–G/cross/self1188 및 up>0, palm/thumb3 patch거리upper/lower·soft평면정렬이 포함된다. [선택:178](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:178)은 범위검사를 통과한 source-clear 조건 중 originalbaseline 대비 actualdelta L2→patchupper제곱합→alignment→고정order다. 범위제외 조건은 source_clear=false라 선택될 수 없다. [후보 조립:180](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:180)은 원offset전체를 보존하고 새phase전용trial·proposal을 만든다. source_state는 제거하고 source_prediction은 별도자료로 기록해 actualstate로 재생하지 않는다.
- [wrapper 입력:25](/home/ajou/yigyu/3/stability_adapter_2/run_arm_position_phase.py:25)은 새leaf/원실제상태/기존모델·손목결과/봉인inventory·직접helper·XML/mesh를 측정 전에 SHA/사본 보존한다. Native만 실제 frozenrunner 소비 inherited closure와 선택proposal/trial/prediction을 추가하며 frozenruntime/inner SHA를 강제한다. [adapter](/home/ajou/yigyu/3/stability_adapter_2/run_arm_position_candidate.py:10)는 기존 fresh actualaudit를 재사용하고 원scope/failure출처를 남기며 try/finally복구한다. 한후보만actualgate/통과시같은init5초, 실패면0step거절terminal과partial을 보존한다. 코드에 새controller/추가외력/기타고정/지속pose 덮어쓰기 경로는 없다.
- [원계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:7)과 [실행leaf](/home/ajou/yigyu/3/stability_adapter_2/ARM_POSITION_EXECUTION.md:3)은74수치제안/6범위제외/68source와향후한actual 검증을 구분한다. LA/Gfullstate/PD·body9/root하체·최종66권한·자유기타 및 원offset보존을 유지한다. Source-clear나범위호환을 실제지지·자연스러움/fret-strike연주목표 완료로 대체하지 않는다. Actualsource 판정/후보/물리응답은 별도 후속 검수다.

Python3.8 AST 통과 및 확인 SHA-256:

- search_arm_position.py: `b53319eaf536b5b3fb790a195a2f5a8743ff8e040ce7f6d8ef4380b18d52519d`
- run_arm_position_phase.py: `f4d756ba73a3e6b08d7205bd96cbcf2b68b029333d7db0c7d20399085178c761`
- run_arm_position_candidate.py: `1818147214bb707b63df58d9694b464865d7f80501b51b6d3aa0b2b4ffd77600`

검수는 소스·XML 읽기/AST/독립 수치계약만 수행했다. 이 기록을 남기고 실제 산출물 검수 요청을 기다린다.

## 실제 source74제안·저장 분석 및 다음 계획 추가 검수

요약 판정: **문제없음(PASS, 이번 source/저장 분석 범위)**. 저장 SHA·원자료 수치·코드 읽기와 독립 NumPy 재조립으로 검수했으며 search/FK/geometry solver/native/분석/렌더/감사 main을 재실행하지 않았다. 그림·최종 README/변경색인·root 봉인 감사는 이 추가 기록의 완료 범위에 포함하지 않는다.

- [실제 search 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/search_execution.json)은 exit0/completed, wall22.297370119초다. 72개 입력의 before/after/현재 SHA와 [72개 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/search_source_manifest.json), search.log SHA를 직접 대조해 모두 일치했다. Search9checks는 모두 true이며 source 코드는 사전 검수 SHA 그대로다. 저장 분석은 76개 입력 before/after/현재 SHA 및 [직접6개 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/analysis_source_manifest.json)이 일치하고 exit0/11checks true다. 76은 원72개에 새 분석 소스·search 출력/실행/사본manifest 4개가 추가된 수이며 76사본을 새로 만들었다는 뜻은 아니다.
- 원 actual 초기81·기존 trial의 원33offset·effective 범위를 사용해 **74개 전체 실제 float32 초기/held 조립, 변경축의 initial/held delta와 L2, 다른79/80 exact, 손목sin 양끝**을 독립 재계산했다. 저장 `changes`/범위 위반 목록/제외 raw81 arrays가 모두 일치했다. 제외 order는 **1,3,8,38,40,45**이며 [geometry 전에 제외:126](/home/ajou/yigyu/3/stability_adapter_2/search_arm_position.py:126)한 6행의 HG/cross/self 및 [분석 반경·쌍 수:38](/home/ajou/yigyu/3/stability_adapter_2/analyze_arm_position.py:38)는 None다. 이를 교차0/통과로 변환하지 않는다.
- 나머지 **68행 모두 HG가 남아 source_clear=false**이며 cross/self1188은 clear, palmup 최솟값0.925554472626>0, 상대손 계층/비이동mesh/upstream identity 저장 검사도 모두 true다. Zero pose 오차는 position1.271920262e−16m/rotation3.320715682e−16rad다. 원 seed와 Wrist_y−.1 seed의 HG쌍/반경은 기존 손목 결과와 재현 검사한다. 이 identity·교차는 저장된 조건부 source 모델 결과이며 새 native/cooked 형상 인증이 아니다.
- [분석74행:33](/home/ajou/yigyu/3/stability_adapter_2/analyze_arm_position.py:33)의 단위변환·HG쌍 수·최대반경·thumb2/palm반경·up/alignment·제외값을 search 원행에서 독립 재계산했다. [seed별 진단 best:54](/home/ajou/yigyu/3/stability_adapter_2/analyze_arm_position.py:54)는 seed0 **row6 Thorax_y+.025, 최대HG2.212092533mm/5쌍**, seed−.1 **row47 Thorax_z+.025, 최대HG1.231575777mm/palm1.079515513mm/5쌍**과 일치한다. 이는 남은 최대반경을 줄인 진단 순위이지 clear 후보 선택이나 실제 PD 채택 순위가 아니다.
- `zero_thumb2_overlap_orders`의 **[31,43,48,52,55,57,64,66,68,72] 10행**도 모두 다른 HG 교차가 남는다. 해당 필드의0은 source 보고 임계값1e−7m보다 큰 thumb2–G 쌍이 없다는 표현이며 실제 거리0/접촉/PhysX clear를 뜻하지 않는다. LP 공통내접반경 역시 PhysX 침투 깊이와 구분한다. Source palm/thumb3 거리 **136개 upper/lower/gap·두 witness 간 거리·기록된 feasibility/weight sum**을 수치 대조했다. Optimizer_success=false54개도 보존되어 있으며 upper는 feasible witness, lower/gap을 함께 읽어야 한다. 최대 gap6.170071945e−7m로 exact 최단거리나 optimizer 성공을 선언하지 않는다.
- [analysis scope:60](/home/ajou/yigyu/3/stability_adapter_2/analyze_arm_position.py:60)와 실제 경로를 대조해 **selected=null, proposal/source_prediction/native/native_execution 없음, 새 native 초기화/physics/actor/train0, 5초 안정성 미측정**을 확인했다. 기존152영상에 추가하는 실행 경로가 없다. 이번 실패를 조용한 actual 기준의 기타 유지 성공/실패나 연주 성공으로 확대하지 않는다.
- [다음 연속 계획:7](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:7)은 이번 최대2축74제안과 구별되는 **arm12 원baseline 대비±.15rad**, 초기/held/source/native/normalized/손목양끝 교집합, 기존offset·fingerrelative/LA/G/PD/body9/root/최종66 보존이다. [두 seed 각400/합계800 상한:9](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:9), 구현 전 가중치·단위 leaf 확정, 전체source-clear만 후보, [한 actual gate/통과시 동일init5초:21](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:21), [bounded 실패시 실제 quiet 기준 복귀:27](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:27)가 명확하다. 새 plan의 patchupper 우선 선택 순서는 이번 L2 우선 search의 실제 결과에 소급 적용하지 않는다. 이 계획은 미실행이며 source 범위호환/근접/임시30mm·5° 및 후기5mm·1°를 자연스러움·물리지지·연주 인증으로 사용하지 않는다. 현재 범위의 구체적 blocker는 없다.

추가 확인 SHA-256:

- analyze_arm_position.py (Python3.8 AST PASS): `365a1040f965f36f5818fac9b9ecf5a9bf746e6d6947607af8efb7411d339dc4`
- search.json: `e0bbbd1ce33989afc6f23a0caec54ec9f7d40315eb4cd14c5112f2d0b841e4b3`
- SOURCE_HAND_ARM_CONTINUOUS_PLAN.md: `e355db92791d4a8e121ae844a4b2cfa187adc9d7fba2fd82d6774e6cd927c0d2`

현재 source/저장 분석 추가 검수를 마쳤다. 최종 그림·문서·감사 소스는 별도 완료본 검수 후 최종 판정을 추가한다.

## 최종 그림·문서·봉인 감사 코드 검수

요약 판정: **문제없음**. 실제 저장 PNG를 열고 그림의 원자료·SHA·문서 범위 및 미실행 감사 코드를 대조했다. 실행 blocker는 없으며 소유 review.md만 추가했다. Solver/search/native/분석/producer/render/감사 main을 실행하지 않았다.

- [실제 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifacts/arm_source_geometry.png)는 9패널·요청 delta(rad)·최대 HG LP 반경(mm), 두 seed의 색/기준선을 명확히 구분한다. [producer 값 구성:121](/home/ajou/yigyu/3/stability_adapter_2/make_arm_position_artifacts.py:121) 및 [패널 구성:166](/home/ajou/yigyu/3/stability_adapter_2/make_arm_position_artifacts.py:166)을 저장 74행과 독립 대조했다. 66개 비baseline 점과 두 seed 기준값4.288364821171085/2.0765223062130405mm가 나타나고 모든 값이 y축 안이다. 두 기준값은 9패널에 반복되는 점선으로 표시하며 별도 관측을 늘린 것이 아니다. 범례·제목·축·세 줄 캡션에 데이터 가림/겹침을 관측하지 않았다.
- **표시 한계(기록 완료):** [sharex 설정:158](/home/ajou/yigyu/3/stability_adapter_2/make_arm_position_artifacts.py:158)과 [tick formatter:180](/home/ajou/yigyu/3/stability_adapter_2/make_arm_position_artifacts.py:180) 때문에 의도한 † tick은 실제 PNG에 없다. 실제 제외는 NaN 공백이며 0점으로 그리지 않았다. [README:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/README.md:7), [ROOTnotes:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/ROOT_VERIFICATION_NOTES.md:15), [VISUAL:2092](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2092)가 두 seed 각각 Thorax_x−.05/−.025 및 Thorax_y+.05의 정확한 제외 위치와 한계를 설명한다. 데이터 불일치/blocker가 아니며 소비된 producer/PNG를 수정하지 않는다.
- [artifact 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifact_execution.json) exit0/completed, **82입력/82사본**과 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifacts/manifest.json)의 전후/현재 SHA가 모두 일치했다. 모든 원본→사본 SHA, producer/wrapper 전후 SHA, 출력 PNG SHA, 닫힌 artifact.log SHA를 직접 확인했다. Log는 정상 empty stdout/stderr의 SHA다. Manifest와 실행기록의 native/physics/actor/train 카운터는0이다. [wrapper:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifacts/run_producer.sh:15)는 기존 출력 거부 후 입력 사전복사→한producer→닫힌로그 SHA·metadata 순서이며 원본 consumed source/결과를 덮어쓰지 않는다.
- [README 표:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/README.md:13)의 baseline/best/L2/HG쌍/palm 값과 [결론:18](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/README.md:18)을 원행·앞선 독립 분석 검산에 대조했다. Palm0 집계값≠거리0, thumb2미보고10조건≠전체clear, sourceLP≠cooked침투/실제접촉/지지, 전체68조건 실패≠전가동범위 불가능성, 새native0/5초미측정을 정확히 구분한다. 양손 검사와 self1188을 별도로 설명한다. [변경색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/CHANGED_FILES.md:1)의 절대경로·실제 function/결과 줄 및 문서 링크를 직접 확인했다.
- Main [README 결과:1203](/home/ajou/yigyu/3/stability_adapter_2/README.md:1203)/[산출물:1214](/home/ajou/yigyu/3/stability_adapter_2/README.md:1214), [PLAN 결과:2024](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2024)/[산출물:2035](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2035), [VISUAL §116:2090](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2090)의 수치/실행범위/후속 미실행 설명이 일치한다. Journal_before의 main3문서 prefix SHA도 현재 그대로다. 기존 videos152개 수와 v12→v13 update/index SHA를 확인했다. 과거 영상·봉인파일 전체 byte 보존의 최종 검증은 root 실제 감사에 맡기며 이번 읽기 검수를 감사 실행 완료로 기록하지 않는다.
- [미실행 감사 producer:18](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/root_final_audit_producer.py:18)은 source72/log/copies/74·68·6제외/identity·self1188/새native0, analysis11/currentinput, artifact SHA·counter, mainprefix, 기존inventory·152영상/index·최종독립판정을 검사한다. [기존 선언자료:43](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/root_final_audit_producer.py:43)는 thumb2 v2의 교정 inventory_v2를 사용하며 7개 inventory metadata union2639항목의 중복 정의도 일치했다. [봉인:57](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/root_final_audit_producer.py:57)은 최종 source/doc/review 사본을 대조하고 inventory에서 append 가능 maincanonical3만 제외하며 그 사본은 포함한다. Phase 내부 열린 stdout 로그를 만들지 않는 root 실행 지침과 정합한다. 감사 자체는 아직 미실행이며 Python3.8 AST 읽기 검수만 통과했다. 기존 파일 보존을 검증한 뒤 snapshot/inventory를 생성하는 호출 순서에서 구체적 blocker는 없다.
- [다음 arm12 연속 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:1)은 이전 추가 검수 범위 그대로 미실행이다. 실행 전에 별도 단위/가중치 leaf·구현 검수, 최대800평가와 한actual 상한, 실패시 quiet actual 기준 복귀가 필요하다. 이번 PASS는 이 미래 구현·actual/PD응답·자연스러움·연주 완료 인증을 포함하지 않는다.

최종 확인 SHA-256:

- PNG: `25f83804e11e0319424edbc70ce59cb90a7693f5cf57b91b7caf0e165be2b73a`
- producer(Python3.8 AST PASS): `873d1b36c25802fbbf3283a131aa6febb63c852dc15d2d168bcfde40bf8f0a08`
- artifact wrapper: `341589a7ee90f37c86ec8ee4b00012f912b8d63b5449623d2bd8e952a20421cc`
- README: `35c2357117864681887864117eb9753497a02b1e483d53ea1a5461f5787bc640`
- CHANGED_FILES: `d1309c3f19e44ec8300f392dd645bd1698abdf520245f20efd83de8118dcd7a0`
- ROOT_VERIFICATION_NOTES: `a335e57233727bec51ca54298df9ea24170bbeac967b7901fc72746629bd1445`
- VISUAL_REPORT: `3896f6588f6d804db7e64177905ed84efc6170caea6ed2d49ebaf62e5496de76`
- root_final_audit_producer.py(Python3.8 AST PASS、미실행): `27d430a7539720b62846542904a115a7c59a172588c5416afc56230a9dff812e`

소스·입출력·소비 산출물을 변경하지 않았으며 이 최종 검수 기록을 동결한다. Root의 실제 ONE 보존 감사·봉인은 이후 별도 실행 기록이다.

최종 판정: PASS
