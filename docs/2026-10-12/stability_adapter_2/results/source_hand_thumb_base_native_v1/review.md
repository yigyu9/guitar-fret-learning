# 엄지 기저부 native 4후보 사전 검수

요약 판정: **문제없음(PASS)**. 확인한 최종 코드에서 실행을 막는 Critical/Warning은 없다. 소유 파일은 이 review.md뿐이며 이전 P2 review·소스·타인 파일은 수정하지 않았다. 준비/native/보정 producer를 실행하지 않았다.

- [후보 순서:20](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:20)는 thumb1_x−.05,thumb1_y+.05,thumb1_x−.10,thumb1_y+.10rad로 [계획:7](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md:7)과 일치한다. 기준은 source-hand5의 실제 초기·held이며 한축 초기=held/offset0만 변경한다. Source_state를 제거하고 numeric admission scope를 분리하며 실제 fresh gate가 필요하다.
- [준비 검산:75](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:75)은 trial 변경을 원복해 나머지 설정을 대조하고 다른80초기/held 보존, 무clipping81목표, native/source-effective 범위와 손목±.005 양끝을 검사한다. 검수자는 저장 원자료만 사용해 float64조립→float32제출을 별도 재계산했다. 네 후보 초기각은 순서대로0.480243980884552/−0.8544571995735168/0.43024399876594543/−0.8044571876525879rad이며, 실제delta−.050000011920928955/+.050000011920928955/−.09999999403953552/+.10000002384185791rad다. 전체목표 재조립·범위·손목양끝이 통과했다. 초기G/LA/root하체/PD/몸통9·기존thumb2 초기/held·최종66범위는 기존 trial과 frozen runtime을 통해 유지한다.
- [입력 보존:51](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:51)은 canonical 신규코드/계획·원native initial/원proposal/trial/범위/참조inventory와 실제 inherited closure를 실행 전에 SHA·직접 사본으로 보존한다. 원trial SHA와 source range sealed SHA를 대조한다. [Native:129](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:129)는 frozen 직접runtime/inner runner SHA 및 이전 native 입력 closure를 강제하며 각 시도마다 새 proposal/trial/실행자료와 사전manifest를 남긴다. 오래된 nested snapshot은 해시참조로 유지한다.
- [실제 실행 경계:135](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_native_phase.py:135)는 네 후보를 순서대로 직접 gate에 넣는다. exit0+completed 보고서만 완료이며1200step/151frame를 추가 요구한다. fresh gate false이고0step인 비zero exit만 초기 형상 거절 terminal로 구분하고 나머지 오류는 중단한다. 첫 완료 후보 뒤 break, native_batch가 이미 있으면 재시작하지 않아 최대4초기화/하나5초 계획과 맞는다. 통과 후보를 재초기화하는 경로는 없다.
- [scope adapter](/home/ajou/yigyu/3/stability_adapter_2/run_thumb_base_candidate.py:12)는 기존 audit_initial을 그대로 사용하고 output의 원scope/failure를 inherited provenance로 남기며 현재 direct gate명칭을 구분한다. 후킹은 try/finally로 복구된다. 새 finger1다축 FK/source_state를 통한 pass 예측이나 controller·강제 고정·추가 외력은 없다. 실제 fresh15검사/형상·동적 결과/각1200명령·미디어는 실행 후 별도 검수 범위다.

Python3.8 AST 통과 및 사전 확인 SHA-256:

- run_thumb_base_native_phase.py: `056c9cc15cfdf465ab8ce07afe77a41c583583f2a629be64feaeceb49177371e`
- run_thumb_base_candidate.py: `43168e239b209e8b7184fb54e01a890a276987b89cdb0f09d8274af76211e4bf`

## 직전 P2 닫힌 감사 로그 보정 코드 검토

[보정 계획](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/CLOSED_LOG_CORRECTION.md:1)과 [root_post_log_seal.py:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/root_post_log_seal.py:15)를 읽었다. 첫 inventory와 현재 파일을 직접 비교한 결과 차이는 root_audit.log 한 개뿐이며 기록된0bytes에서 닫힌79bytes가 됐다. 원 final_verification의27개 checks는 전부true다. 원 소스·원 inventory·원 verifier·원 로그는 보존하고, 달라진 파일이 이 로그뿐임을 assert한 뒤 별도 final_verification_v2/artifact_inventory_v2로 보정하는 로직이 정합한다. 새 보정 inventory 작성 뒤 모든 기록 SHA/크기를 재확인한다. stdout을 같은 phase 파일로 다시 열지 않는 실행 방침과 맞으며 재검색/렌더/물리는 없다.

보정 소스 Python3.8 AST 통과/SHA `ca1f306f68c42ba3021ca9d6677228d629a2dccf541789e48dfda6d5b81f4159`. 검수자는 보정 main을 실행하지 않았고 보정 실행 완료를 인증하지 않는다. 첫 inventory의 열린 로그 기록 오류와 별도 보정 결과를 구분해 보존해야 한다.


## 실제 네 초기화·저장 후처리·최종 산출물 검수: PASS

요약 판정: **문제없음(PASS)**. 네 후보 자체는 모두 초기 source geometry gate에서 거절됐으며 채택 후보/완료된5초가 없다. 이 검수 PASS는 거절 기록·입력/원자료·산출물의 정합성에 한정된다. 추가 Critical/Warning은 없다.

- 준비23검사/exit0와 네 실행 각각exit1·`initial_geometry_rejected_zero_steps`·report completed=false/1init/0step/0sim초/1frame를 확인했다. [분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/analysis.json:1)의35검사는 모두true, batch는4init/0step/selected=null이다. 각 actual81q=선언q=초기PD=raw state DOF exact, 다른80초기/declared held와G fullstate/PD/physics/LA exact를 직접 대조했다. raw state는 native_initial_state와 같고 Pelvis+하체8 body 상태가 원baseline과 exact다. State/trace각1행, contacts/controls각0행이므로 유지목표를 실제 동적명령으로 제출했다고 해석하지 않는다.
- Fresh15검사 중 네 run 모두 HG만false다. 저장 audit/analysis의 단일thumb2–G LP반경은 순서대로5.193222414/5.015439809/6.079508797/5.789206663mm로 일치하며 기준4.288364821mm보다 커졌다. Actual human66/G39 filter105개를 원정책과 이름별 대조하고 self1188/cross clear를 확인했다. 원raw palm quaternion으로 별도 계산한 up proxy0.9565471586122463가 저장값과 같다. LP solver는 재호출하지 않았으며 cooked침투깊이/힘/지지·연주 성공이나 모든엄지자세 불가능성으로 확대하지 않는다.
- 실행 입력/사본·현재/전후SHA·로그를 독립 대조했다. Preparation14031입력/12사본, native각14043입력/8사본, finish230입력/42사본이 exact다. [저장 후처리 코드](/home/ajou/yigyu/3/stability_adapter_2/finish_thumb_base_native.py:21)는 stdlib로 저장 자료를 검산하고 새영상8개 전부의 sourceSHA/destabsence를 모은 뒤 copy한다. 시뮬레이터/solver를 호출하지 않는다. AST3.8 통과/SHA `17110ebbaf580076d782507e8b4b17255b2e71c5c182a0923eb9cca5de9aacb4`다.
- 실제16개(raw+overlay)PNG의SHA/step0/read-only capture를 대조했다. 두view×네run의 원MP4를 ffprobe로 직접 읽어1280×720/1frame/30fps/0.033333초임을 확인했다. 이전144영상·인덱스 SHA, 새8 `ZERO_STEP_PARTIAL` exact copy/frames1·physics0, 총152/indexv13/updatev12가 일치한다. [README의 raw hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/native/thumb1_y_plus005/raw/frames/hands/00000.png)를 직접 열어 저장native 장면임을 확인했다. MP4길이1/30초는 경과simulation0초의 한프레임 인코딩이며5초영상이 아니다.
- 실제 [bar PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/artifacts/thumb1_base_native_source_radius.png)를 열어 기준+4후보의5개 반경mm/축·조건·caption·잘림/겹침 없음을 확인했다. Artifact exit0, 직접11입력/producer·wrapper포함13사전사본/현재·전후SHA·로그/출력SHA가 exact다. Producer AST3.8 통과/SHA `31bac709ba3fc9896ad4e9ee3b170e029936a5a45c9388a772f533a14224ed0a`, wrapper SHA `c944fe0d5821b2d2a97c7288d4e254c478d8870eed47dead6645872cfa47244d`다. Artifact의 native0와 이번phase 실제4init를 구분하며 동적비교 그림으로 설명하지 않는다.
- 최종 README 표의float32 초기각/delta/LP값 및0step·5초미측정 설명, CHANGED/ROOTnotes와 main [README:1169](/home/ajou/yigyu/3/stability_adapter_2/README.md:1169)·[PLAN:1990](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1990)·[VISUAL §114:2069](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2069)이 실제 결과와 맞는다. 링크의파일/줄 및 main 사전prefix 보존을 확인했다.
- [다음 손목 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:7)은 source-hand5 원baseline으로 돌아가 실패한thumb1/2 변경을 승계하지 않는다. Wristx/y/z의zero1+각±.05/±.10=13조건, 실제float32delta·전체descendant·identity/HG재현/전체screen/거리·정렬을 검사하고 최소변경 clear한후보만 fresh native/통과시같은init5초로 잇는 **미실행 계획**이다. [기존 left33 offset 유지:8](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:8)를 명시해 다른80·손목sinusoid·LA/G/PD/root하체/몸통9·최종66범위를 보존한다. 손목initial=held로 바꾸지 않으며 source 모델을 actualcontact/자연성·연주 인증으로 확대하지 않는다. 미래 구현/승인은 별도 검수다.
- P2 supplemental artifact_inventory_v2의198파일을 현재 SHA/크기로 직접 확인해 exact였다. 원inventory 로그시점 오류와 보정본을 분리보존한 결과이며 P2 review는 수정하지 않았다. [새 감사 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/root_final_audit_producer.py:22)는 이번6stage/거절·source/그림/이전5inventory·152영상·mainprefix를 검산한 뒤 source_final/inventory를 쓰고 전항목현재SHA를 재확인한다. Main canonical3개는 사본을 유지하며inventory에서 제외한다. AST3.8 통과/SHA `63563ee3554922dce87d0b6b1b84fb6a435cc5630dec7dc5dd105ac2ea4f386c`다. 감사 코드는 읽기만 검토했으며 root 감사 실행 완료를 인증하지 않는다. 닫히지 않은 결과폴더 stdout로그를 inventory에 넣지 않는 실행방침을 유지해야 한다.

최종 확인 SHA-256:

- README: `286780795a8fe455a22597f0ab9422218d9e2d2f7bb786523e8033c71b90a025`
- CHANGED_FILES: `98a32b69c27c7cd467d93c581cbdb18a97256f62f45300c389c727c6f6412ab9`
- ROOT_VERIFICATION_NOTES: `8b34f2ae99b988860c139d790f30a5c99927d3bd37b2b9e8fc3ca8985f2d79db`
- PNG: `c6888f09c38a421fbd2f147674b6327fd74f1cc72686ce50457caa15265e27ae`

검수자는 저장 파일/코드 읽기·독립수치·SHA/ffprobe·기존PNG 보기만 수행했다. 신규physics/solver/분석/그림/audit main 실행0이며 이 review.md 최종 추가 기록을 동결한다.
