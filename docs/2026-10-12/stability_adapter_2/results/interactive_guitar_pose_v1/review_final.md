# 수동 기타 초기 배치 도구 — 실제 검증 후 검수

## 정적 v2 harness 실행 전 검수 — 2026-10-08

요약 판정: 새 정적 검증 코드 문제없음. 코드 사전 판정 PASS이며 실제 결과의 최종 판정은 아직 보류한다. 동결된 review_preflight.md는 수정하지 않았다. 검수자는 물리·검증 harness·영상 생성 실행을 하지 않았다.

Critical: 없음. Warning: 없음. Suggestion: 없음.

`/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_editor_static_v2.py:65` — checks 전체를 builtin bool로 바꾼 후 JSON에 기록한다. link 오차도 14~16행에서 builtin float로 바꾼다. 기존 harness의 np.bool_ 직렬화 실패가 이 출력 경로에 남아 있지 않다. false 검사도 저장 후 AssertionError로 실패 처리한다(70행).

`/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_editor_static_v2.py:27` — 새 장면은 정적 편집과 렌더/readback에만 사용하며 이 스크립트에는 start_preview/advance/step_physics/simulate 호출이 없다. native 환경 생성의 기존 초기화는 유지하고 post-initialization physics steps=0을 직접 확인한다(47,58행).

`/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_editor_static_v2.py:8` — root의 실제 delta quaternion으로 모든 guitar link의 예상 world 위치·회전을 계산하여 상대 형상 보존을 확인한다. 6축/world-local/정밀 편집 후 2µm/2µrad 한계로 비교한다(42~45행). 사람 상태, baseline PD properties, 81 constant targets도 독립 비교한다(31~35,46행).

`/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_editor_static_v2.py:48` — 후보 저장/ON-OFF 표시 recorder 분기/새 환경 reload를 확인한다. 기존 preview는 report와 capture를 읽기만 하며 1200 steps,151 frames,2 videos,쓰기 0,의도적 guard 차단1,연속 frame step0..1200 및 render-preserves-state를 확인한다(59~64행). 이전 완료 preview에 추가 물리를 진행하지 않는다.

사전 source SHA256: `5b6a3ba13f66350842b109afeb25229084d47523ea03c2fd67ee0be4206053d5`. AST Python 3.8 문법 PASS. 실제 실행 결과 대기 중.

원 실패와 실제 preview의 구분:
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_execution.log` 끝부분의 `TypeError: Object of type bool_ is not JSON serializable`와 원 native_verification/verification.json의 truncated 끝부분을 직접 확인했다. 기존 검증 프로세스는 root 관측상 exit1이며 이를 성공으로 바꾸지 않는다. 코드 검수에서 직렬화 타입 문제를 사전에 발견하지 못했다.
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/preview_000/report.json`은 completed=true,1200 steps,151 frames,양 시점151frame/30fps/5.033333s,post-start state writes0,blocked1을 기록한다. blocked1은 원 harness의 의도적 guard 호출이다. capture.json의 시작0/끝1200/151행을 확인했다. 완료 preview와 검증 harness의 최종 JSON 실패를 별도 사실로 보존한다.
- 준비 단계 외부 font relative_to 오류도 preparation_failure.txt에 별도 보존돼 있다. 이 준비 실패를 물리 trial로 계산하지 않는다.

## 정적 v2 실제 결과 및 안내 사전 검수 — 2026-10-08

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/static_verification_v2/verification.json`의 27 checks가 모두 builtin true이며 new_physics_steps=0, 실제 X11 events=[F3,L]임을 확인했다. 전체 guitar link 최대 위치 오차는 9.357739674962331e-8m, 회전 오차는 1.8212640260610922e-7rad다. 정적 검증 후 원 v2 source SHA는 위 사전 SHA와 같다.

완료 preview의 원 저장 자료를 독립 읽기/해시 검산했다: states.jsonl 1201행의 steps는0..1200 exact, Pelvis와 양쪽 Hip/Knee/Ankle/Toe body states는 첫 상태와 전 구간 exact다. 초기 constant targets는 baseline 81 preserved targets와 exact, LA=1.1018469719600776m/strap ON이다. overlay capture의 151개 frame step은0..1200/8 exact, 그302 PNG의 current SHA와 양 MP4 current SHA는 기록과 exact다. 추가 native/ffprobe/후처리를 실행하지 않았다. frozen preflight current SHA도 `c25e40a232c06877567984e24cd7eae1313b2ffe22cbd671a073d0790f709db3`로 유지됐다.

`/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_EDITOR_GUIDE.md:17`의 키 표, 34행의 EDIT/PREVIEW 분리, 36행의 constant PD와 actor 미실행, 45행의 sim5초/영상5.033초 구분, 48행의 candidate strap 우선순위는 구현과 일치한다. 55행은 기능검증 후보를 권장 자연자세로 설명하지 않고 접촉/관통/연주 인증을 제외한다. root에 guide에도 OFF 물리 미실행 및 정적 OFF 표시·raw recorder 분기만 검사했다는 한계를 추가하도록 전달했다. 결과 문서·main append·중앙 영상 갱신은 작성 중이므로 최종 판정은 아직 동결하지 않는다.

## 최종 문서 대조 중 사실 정정 — 2026-10-08

위 사전 기록의 "빈 첫 sourcecopy 경로"라는 설명을 정정한다. 실제 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/source_before`에는 tab2body/isaacgym/docs/stability_adapter_2 하위 디렉터리와 14,029개 파일이 존재한다. font 경로 오류 이전까지 부분 복사가 진행된 것이며 빈 경로가 아니다. preparation_failure.txt의 "created empty" 문구를 그대로 사실로 받아들인 검수 기록도 부정확했다. 원 실패 기록과 부분 사본은 수정·삭제하지 않는다. 결과 문서는 이러한 원 기록의 부정확한 설명을 별도로 정정해야 한다고 root에 전달했다.

main README/PLAN/VISUAL_REPORT는 execution_before.json에 저장된 기존 크기까지 prefix SHA가 전부 exact다. 중앙 새 whole-body/hands MP4는 preview 원본 SHA와 exact다. VIDEO_INDEX_v18은 기존 v17 인덱스를 링크로 유지하고 새 2개를 추가하는 누계 구조이며, v17의 고유170경로와 새2경로의 합집합은172개다. v18 자체에172개 직접 링크가 들어간 것으로 해석하지 않는다.

결과 README/CHANGED_FILES/guide/v18의 현재 절대 로컬 링크45개는 존재하고 명시된 줄 번호는 파일 범위 안이다. candidate_001 손 이미지도 직접 열어 native 장면과 주황 strap overlay를 확인했다. 화면상의 가까움·겹침을 접촉/안정/자연자세 인증으로 판정하지 않는다. main 추가분은 automatic/startup/학습 중단 유지와 사용자 수동 도구 범위를 명확히 기록한다.

## 최종 문서 보완 확인 및 판정 — 2026-10-08

요약 판정: 문제없음.

Critical: 없음. Warning: 없음. Suggestion: 없음. 사전 검수의 전체 guitar link native readback 제안은 정적 v2의 실제 검사로 해소됐다.

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:23`은 후보를 도구 기능검증에서 저장한 시험 입력으로 명시한다. 45행은 첫 부분 사본14,029개/두 번째14,030개와 보존본이 runtime import 위치가 아님을 밝히며 원 preparation_failure.txt의 잘못된 empty 표현을 새 preparation_correction.json으로 정정한다. 실제 두 경로의 파일 수도 14,029/14,030으로 대조했다. 원 오류 파일·로그·truncated JSON은 보존되고 원 harness exit1을 성공으로 바꾸지 않는다.

`/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_EDITOR_GUIDE.md:57`은 직접 사용자 마우스 조작 미검증과 OFF 5초 물리 미실행/정적 OFF 표시·raw 녹화 분기 검사 범위를 명시한다. 결과 README 25~43행은 실제 native 카메라/route overlay와 viewer 축 표시를 구별하고, 1200 physics steps/151frames/두영상 및 정적 v2 27checks/추가 물리0을 실제 자료와 일치하게 설명한다. 영상5.033333초와 마지막 sim5초를 구별하며 기능 후보를 자연자세·접촉·clearance·평형·연주 인증으로 설명하지 않는다.

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/CHANGED_FILES.md:9`에는 pure unit test와 원 실패 harness 링크도 포함됐다. 현재 결과/색인/guide/v18의 절대 링크47개가 모두 존재하며 지정 줄도 범위 안이다. main README1346행, PLAN2167행, VISUAL_REPORT2165행 추가는 기존 prefix를 바꾸지 않았고 이번 사용자 요청의 수동 도구 범위와 기존 자동 탐색·startup·학습의 중단 유지가 명확하다.

검수 최종 문서 SHA256:
- 결과 README.md: `f918dbc245cbec7c30b88521baf7a37fe06f181003eb91cd6952bcfc3b6d9c1d`
- CHANGED_FILES.md: `243eabdc4cbe8c4ca7a1fda3617ff33931c8e01f9bb041f70c9deaace366d952`
- GUITAR_POSE_EDITOR_GUIDE.md: `d7c8814941b3dccfe3d28e06b2227d997d251a7aa702627a854daa566bca45b4`
- VIDEO_INDEX_v18.md: `30349983d9244128d4b7f0279573d5c531d4bf370e962c1f7b95ddb6e3ecc23e`
- preparation_correction.json: `e79f63d1f16352a916a1919c7bb8d29156c5469c0d35a9f916c465a0afb4f0a9`

최종 판정: PASS

판정 범위는 검수한 도구 코드·실제 완료 ON preview·정적 v2 결과·최종 문서·중앙 영상 두 복사본과 누계 인덱스다. 기존 실패의 보존과 검증 범위의 한계를 포함해 정합하다. 검수자는 새 물리·unit test·harness·후처리 실행을 하지 않았으며 review_final.md만 생성/append했다. 이후 root의 최종 보존 감사·snapshot·phase inventory 완료를 미리 주장하지 않는다.
