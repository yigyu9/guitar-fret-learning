# Source 호환 손5관절 초기 배치 검수

요약 판정: **문제없음(PASS)**. 최종 native 실행 전 구체 blocker는 없다. 소유권은 이 검수 파일뿐이며 타인 파일/소스·기존 봉인 자료를 수정하지 않았다. 실제 prepare/native main은 검수자가 실행하지 않았다.

## 사전 코드 검수

- [준비 코드](/home/ajou/yigyu/3/stability_adapter_2/prepare_source_hand_initial.py:48)는 현재 initial-aligned의 실제 초기/held 행을 각각 사용해 LH thumb1_x/y,thumb3,index1_x,ring1_x만 가장 가까운 effective 경계의 float32 1ULP 안쪽으로 옮긴다. 다른76초기각/유지목표와 trial 나머지 설정을 보존하고 새 q에 맞는 offset을 재계산한다. warmstart compose는 clipping 없이 native bounds를 검사하며, 초기/held 전체81과 손목±.005 극값 effective 범위를 대조한다. 기존 조건부18축 FK를 호출하지 않는다.
- [새 proposal 구성](/home/ajou/yigyu/3/stability_adapter_2/prepare_source_hand_initial.py:90)은 이전 `source_state`를 제거하고 숫자 준비에 한정된 admission scope를 명시한다. Legacy `admitted_for_native_near_contact_diagnostic=True`는 frozen runner 계약을 위한 수치 준비 허용값이며 geometry admission이 아니다. Support search false/이유를 유지하고 실제 integration 전에 새 fresh gate를 강제한다.
- 최초 native 검토판의 `filters == expected`는 human66키와 원정책105키(G39포함)를 비교해 무조건 false가 되는 blocker였다. Root에 즉시 전달했고 미소비 [최종판](/home/ajou/yigyu/3/stability_adapter_2/run_source_hand_initial.py:24)은 human과G의 실제 properties/spans를 각각 읽어 이름별 원정책과 대조/기록하므로 해소됐다. 같은-left 비인접 pair와 native 허용 graph>2 pair의1188 source self screen, human–G/cross-hands, palm up, fixed root/하체/G fullstate·PD·81/66제어권·0step/read-only를 확인한다. Source hull LP는 cooked 동적 침투 인증이 아니다.
- [runtime admission/save 교체](/home/ajou/yigyu/3/stability_adapter_2/run_source_hand_initial.py:73)는 원 near_contact audit를 대체하고 finally에서 복구한다. 새 audit는 row의 source_state/FK를 소비하지 않는다. Frozen runner가 추가하는81q exact/native bounds·초기PD=q·LA exact까지 모두 통과해야 integration을 시작한다. 새 audit12검사+runner 추가3검사로 **실제15검사 예정**이며 기존14개 숫자를 강제하면 안 된다. 출력의 legacy gate 명칭과 실패 설명은 direct native source gate로 교체하고 원 scope/실패를 출처로 구분해 보존한다.
- [stage wrapper](/home/ajou/yigyu/3/stability_adapter_2/run_source_hand_initial_phase.py:28)의 실제 frozen runner 소비 closure를 대조했다. 이전14k입력은 실제 소비되어 SHA로 유지하고 canonical 소스/계획·trial/proposal·외부 font 사본을 별도 보존하며 과거 nested snapshot을 재귀 복사하지 않는다. Frozen runner SHA를 강제하고 실행 후 입력/로그/exit를 남긴다. Source gate 거절의0step terminal은 report로 구별하여 partial t0 영상/이유를 보존하고 pass만 같은 초기화1200step/151프레임 두 strap 영상으로 진행한다.
- [새 실행 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_INITIAL_EXECUTION.md:1)과 [기존 후속 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md:1)은 큰 thumb 변경/새 초기배치·수치 조건과 실제 geometry/동적 지지를 구별한다. 고정LA·기타 초기 p/q·root/하체·몸통PD·손목파형·최종66권한을 유지하며 source box 호환을 자연성/연주/안정화 성공으로 확대하지 않는다.

## 실제 숫자 준비 출력 검수

Root의 1회 준비 뒤 저장 [preparation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/preparation.json:1) 9검사 true와 proposal/trial SHA를 독립 대조했다. 각 수치를 원 source 범위 행에서 직접 `nextafter(float32 boundary,inward)`로 재계산해 exact 일치했다. 다른76·trial 복원 동일성/무clipping81목표/손목양끝/native-effective bounds·입력 closure도 통과했다. 준비 stage14030입력/182사본·현재/전후 SHA/로그/exit0 일치, 신규 native 초기화/physics0이다.

| 좌표 | 새 초기각 = 새 유지목표(rad) | 새 offset(rad) |
|---|---:|---:|
| LH:thumb1_x | 0.530243992805481 | 0 |
| LH:thumb1_y | −0.9044572114944458 | 0 |
| LH:thumb3 | 0.38739678263664246 | 0 |
| LH:index1_x | 0.7539531588554382 | 0 |
| LH:ring1_x | 0.8619377613067627 | 0 |

저장 bridge mid/half/scale로 새 초기/held의 normalized history를 별도 계산했다. Fret 최대절대값0.9999998807907104, Strike0.9997100830078125로 둘 다[-1,1] 안이다. 이 숫자 결과는 아직 fresh native geometry 통과를 뜻하지 않는다.

최종 소스 AST Python3.8 통과 및 SHA:

- `prepare_source_hand_initial.py`: `22b8860f001584cda821ef5632769975fdb2abddf64e2d00fafcb20ad5b815bc` (준비에 소비됨)
- `run_source_hand_initial_phase.py`: `ab964562a75c404376c17213db1664066d4f049ff4ee3228009a6be177939f68` (준비에 소비됨, native 전 불변)
- `run_source_hand_initial.py`: `a318a62b47f93dce1d3c526a64297d419341cc4983784e0aa4e2443b4f11a8b7` (수정된 최종 native 미소비판)

검수자는 소스 읽기·AST·독립 NumPy 수치/해시 대조만 수행했다. 새 실제 native·geometry producer·물리·actor·훈련·렌더·main 재실행은0이며 실제 gate/영상/동적 결과는 후속 검수 범위다.

## 실제 초기 gate 거절과 저장 후처리 검수: PASS

요약 판정: **문제없음(PASS)**. 이것은 후보 통과나5초 완료가 아니라, 실제1초기화 뒤 fresh source gate가 거절한 **0step·1frame** 결과다. Native child exit1과 wrapper의 `initial_geometry_rejected_zero_steps` terminal을 정상5초 완료로 해석하지 않는다.

- [actual audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json:1) 실제15검사 중 `source_human_guitar_clear` 하나만 false이며 다른14개는 true다. 저장된 유일 교차는 `LH:thumb2`–`guitar` source LP common radius0.004288364821171085m(4.288364821mm)다. 원 audit와 analysis의 pair/수치가 일치하고 기존 source LP 코드의1e−7m threshold에 따른 거절과 정합한다. 이는 source hull 교차량으로 cooked 물리 침투깊이가 아니다. 형상 solver나 native를 재호출하지 않았으며 LP 수치는 저장 결과 간 대조 범위다.
- 저장 actual human66/G39 shape-filter readback을 원105-key정책과 이름별 대조했다. Self1188쌍/교차손 clear와 raw native palm quaternion으로 별도 계산한 up proxy0.9565471586122463가 기록과 맞는다. Source_state/FK prediction은 proposal/audit 경로에 없다. Full81 실제q는 expected q·초기PD·raw native DOF와 exact며 다른76초기q/declared held·G fullstate·PD·physics·LA가 baseline과 같다. Declared held 목표는 수치 검증값이고 gate 뒤의 실제 command로 제출하지 않았다.
- [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/report.json:1)는 completed false/1init/0physics/0.000초/1frame 및 direct gate failure를 보존한다. 원자료 state/trace 각1행 step0, controls/contacts 각0행이다. [analysis](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/analysis.json:1) 15검사 true와 `five_second_stability_measured=false`, 원 preparation5관절 rad→degree 수치를 독립 대조했다. 검사 통과는 거절 기록의 정합성 통과이지 geometry 통과가 아니다.
- Native stage14033입력/183사본, [finish 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/finish_execution.json:1)167입력/14사본의 현재 원본/사본·전후 SHA·로그를 확인했다. Native child exit1은 예상 거절 terminal이며 저장 후처리 metadata exit0와 구별된다. [후처리 소스](/home/ajou/yigyu/3/stability_adapter_2/finish_source_hand_initial.py:22)는 stdlib로 저장 자료 검산/영상 원본복사만 수행하며 AST3.8 통과, SHA `da87c823aa4bb173db4c4a2a2506f8c61937eb24854cbf2be92633b2dfeb5a2a`다.
- 원+overlay4 PNG SHA와 read-only step0 capture를 확인했다. 실제 raw hands와 overlay whole-body 이미지를 열어 원 native 장면/route overlay가 구별되는 것을 확인했다. 두 원본 MP4의 현재 SHA와 실제 ffprobe는1280×720/1frame/30fps/0.033333초다. 이는 경과시간0초의 partial 한 프레임이며5초 영상이 아니다. [수집 update](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v11.json:1)의 이전142영상/인덱스 SHA 보존, `ZERO_STEP_PARTIAL` 이름의 새2파일 exact copy/각frames1·physics_steps0, 총144개·index v12 SHA를 확인했다.

검수에서 실행한 것은 저장 MP4 ffprobe 읽기와 독립 수치/해시 계산뿐이다. Actor·physics·runner·geometry screen·후처리 main·렌더 재실행은0이다. 이번 후보의 동적 지지/연주/자연성/5초 안정화는 미측정이다. 다음 geometry 조정 방향과 최종 문서/이미지 설명은 별도 후속 검수 범위다.


## 최종 문서·초기 이미지·후속 계획·감사 코드 검수: PASS

요약 판정: **문제없음(PASS)**. Critical/Warning 잔여 사항은 없다. 표의 ring1_x 초기 변경량 반올림 오류는 원자료 −8.107338922156755°에 맞춘 −8.107339°로 정정됐음을 확인했다. 소스·물리·분석·렌더·감사 producer는 재실행하지 않았다.

- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/README.md:5)의 다섯 초기/held 각도·초기 변경량은 저장 analysis와 일치한다. [거절 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/README.md:13)은 fresh15개 중HG만 실패/나머지14통과, LP 공통내접반경과 cooked 침투깊이의 차이, report completed=false와 native_execution exit1의 출처, 0step·1frame partial과 5초 미측정을 구분한다. 실제 저장 hands overlay PNG도 직접 열어 native 장면 위 주황 route 표시를 확인했다. 앞선 raw/whole-body 이미지·MP4 검수와 정합하며 추가 물리 효과나 동적 접촉 성공을 주장하지 않는다.
- [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/CHANGED_FILES.md:7)·[root 범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/ROOT_VERIFICATION_NOTES.md:3)과 main [README:1129](/home/ajou/yigyu/3/stability_adapter_2/README.md:1129)·[PLAN:1950](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1950)·[VISUAL §112:2047](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2047)은 이번 거절/후보 미채택/총144영상/후속 미실행과 일치한다. Phase README/CHANGED의 절대 경로·줄 링크는 실제 파일과 유효 줄을 가리킨다. 숫자 준비/저장 분석 PASS를 초기 geometry PASS로 확대하지 않는다.
- [다음 thumb2 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md:5)은 실제 거절 native state의 finger1 변환을 고정하고 기존 검증 scalar thumb2만 사용한다. 시작각0.3384127914905548rad는 원 actual initial과 일치한다. Zero-identity 후 0/±.05/±.1/±.2rad의 7개 source 조건·전체HG/cross/self1188/up·거리 관측, 최소|delta| 후보 선택 및 fresh gate 통과 때만 같은 초기화5초로 이어가는 **미실행 계획**이다. 변경된 finger1에 기존18축 FK 인증을 확대하지 않으며, 범위 호환을 넘어 지지 회복/기타 오차 개선을 목적으로 명시한다. 향후 구현·source 결과·native 승인은 이번 검수에 포함되지 않는다.
- [최종 감사 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/root_final_audit_producer.py:20)는 preparation/native/finish exit0/1/0 및 입력 전후/현재 SHA·소스 사본·로그, 이전3 inventory와 main prefix를 검사한다. [실제 결과 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/root_final_audit_producer.py:34)은0step 거절/15fresh 중HG만 실패/단일thumb2 LP/self1188/15저장검사/4 PNG/142→144 partial 영상·인덱스를 확인한다. 모두 통과한 뒤 source_final 사본과 inventory를 만들고 append 가능한 main canonical3개는 inventory에서 제외한다. Python3.8 AST 통과를 확인했으며 검수 시점 final_verification/inventory는 아직 없어 **감사 실행 완료를 인증하지 않는다**.

최종 확인 SHA-256:

- README: `cdb5142549acd9d03adc403b68b645943a06b9f982d989e9bb5c43f894dbf4ee`
- CHANGED_FILES: `27d46c44df94ff97d56e2128af30b867a2b000dfbbe5d28515a4f8dcaab569ea`
- ROOT_VERIFICATION_NOTES: `df12cc5e7f6419c1f31445f0b8f4016586bab0c27ae8e11dc5f3ee8e3d6802a7`
- 미실행 root 감사 producer: `d5fe53ebf75865cda9606deb3a565d21c3fc7469338a785cb219b3e92cf3cab6`

검수 소유 파일은 이 review.md뿐이다. 최종 검수 기록을 동결하며 이후 root의 별도 보존 감사 결과를 따른다.
