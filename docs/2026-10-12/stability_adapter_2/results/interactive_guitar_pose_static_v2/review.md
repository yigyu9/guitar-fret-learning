# 정적 기타 배치 편집기 v2 검수

## 실행 전 코드 검수 — 2026-10-08

요약 판정: 문제없음. 실행 전 코드 판정: PASS.

Critical: 없음. Warning: 없음. Suggestion: 없음.

사용자의 최신 정정에 따라 시각적 자연스러움 판단용 정적 배치만 검수했다. 기존 v1의 preview 및 자동 실험 재개는 이번 범위에 포함하지 않는다. 검수자는 이 review.md만 생성/append하며 기존 v1 소스·기록·동결 review는 수정하지 않았다. native/물리/검증 harness/이미지 생성 실행은 하지 않았다.

- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:51` — StaticCameraEnvironment가 재사용 환경 생성 전에 acquire_gym을 NoPhysicsGym으로 감싼다. 재사용 CameraEnvironment의 GraphicsGym이 NoPhysicsGym을 다시 감싼 구조에서도 create_sim은 NoPhysicsGym의 gravity=0 설정(36~38행)을 통과한다. 두 acquire override는 각각 finally로 복원한다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:40` — simulate/fetch_results와 재사용 경로의 body force/DOF effort/rigid body force API를 호출 전에 차단한다. StaticCameraEnvironment.step_physics도 독립 차단되므로 상속 step()도 첫 호출에서 실패한다. CLI event loop에는 draw만 있고 advance/preview/encode/physics step 호출이 없다(271~279행). PD 속성·목표는 초기 배치의 기록 조건으로만 유지되고 물리 적분 경로는 실행되지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:202` — Space/E는 안내만 출력한다. T는 참고 route 표시용 boolean만 바꾼다(207행). viewer의 strap lines와 저장 이미지의 strap overlay는 표시 기능이며 힘 호출을 하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:174` — 새 candidate는 physics_enabled=false/simulation_steps=0/strap_enabled=false와 별도 strap_visible을 기록한다. 과거 candidate는 baseline SHA·pose·boolean을 검증하고 기존 strap_enabled를 표시 기본값으로만 읽는다(84~93행). 불러오기로 물리를 활성화할 수 없다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:140` — 이전 검수한 전체 guitar link의 root pivot 강체변환 수식을 유지한다. 제출 후 root readback/사람 상태 불변/steps0을 확인한다. 초기 장면 생성·수동 setter는 시각 배치를 위한 것이며 시간 적분과 분리돼 있다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:182` — 재사용 녹화 helper는 단일 정적 capture만 사용한다. encode나 동영상 생성 호출이 없다. constructor 실패와 viewer 종료 시 scene 정리 경로를 유지한다.
- `/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_static.py:18` — 실제 gravity0/기준 human exact/X11 F3,L/6축/undo/렌더 불변/Space,E 무효/save,load를 검사한다. 차단 검사에서 의도적으로 simulate/fetch/force/step API를 시도하나 wrapper가 호출 전에 RuntimeError를 내는 구조이며, 전후 실제 상태와 steps0을 대조한다(37~47행). 출력 checks는 builtin bool로 변환해 JSON 직렬화한다(55행). 이 검수에서 해당 검증을 실행하지 않았다.

읽기 전용 확인: 두 Python 소스 AST Python 3.8 문법 PASS, 새 launcher bash -n PASS. 재사용 GraphicsGym/CameraEnvironment 및 환경 생성·step 경로와 static camera capture를 대조했다. 새 도구에 직접 simulate/fetch/force/encode 호출이 없음을 AST 호출 목록으로 확인했다. v1 helper의 send_key import는 함수 재사용이며 기존 v1 main/preview를 실행하지 않는다.

검수 소스 SHA256:
- interactive_guitar_pose_static.py: `e0d0001c530424088a19ecc220a9c335888708e2745f0c39da620f2152e1c35e`
- verify_guitar_pose_static.py: `a91070234ebc8fb6a992862013b5c014211695d2ddfbe4e6bbc2a19370006d0a`
- open_guitar_pose_editor_static.sh: `973734630d866bb55308b98501e62bbce191b909b681cfddea19da616185015c`
- GUITAR_POSE_STATIC_PLAN.md: `6c0d69b356797ae4cbd1748bc5cf4d4916fd04a478b6de21d926a9cb00034543`

위 PASS는 실행 전 코드 범위다. 실제 정적 native 결과·최종 문서는 아직 검수하지 않았으므로 최종 봉인 판정은 보류한다. 접촉·안정·자연스러움·연주 가능성을 인증하지 않는다.

## 실제 정적 검증 및 이미지 대조 — 2026-10-08

`native/verification.json`은18checks all true, physics_steps=0/physics_trials=0, 실제 X11 events=[F3,L,SPACE,E]를 기록한다. 새 source SHA와 execution_before.json의17inputs current SHA가 전부 exact다. main README/PLAN/VISUAL_REPORT의 저장 prefix SHA도 모두 exact다. 검수자는 저장 JSON·SHA만 읽었으며 native 검증을 실행하지 않았다.

원 ON/OFF 후보와 clean_static_capture 후보는 모두 physics_enabled=false/steps0/strap_enabled=false다. ON/OFF의 strap_visible만 분리돼 있고 각 capture는 physics_step0, render-preserves-state=true다. 이 세 후보의6PNG current SHA도 모두 기록과 exact다. clean_static_capture의 실제 전체 이미지를 열어 주황 strap/viewer 선이 없는 정적 카메라 장면임을 확인했다.

Warning — 저장 스냅샷에 이전 viewer 선이 남을 수 있는 제한:
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:273` — UI는 event batch 전체를 handle한 다음 draw한다(278행). T 뒤 같은 batch에서 S가 실행되면 clear_lines/draw 전 save_candidate의 capture(190행)가 호출된다. 실제 harness도 T 후 draw 없이 저장해 원 OFF snapshot에 이전 주황 viewer 선이 남았다. 이는 harness에서만 가능한 현상이라고 단정할 수 없다. 코드·원본은 동결 보존하고 결과/사용 안내에 표시 변경 후 viewer 갱신을 확인한 뒤 저장하라는 조건과 동일 batch 빠른 T→S의 한계를 명시하도록 root에 전달했다. clean_static_capture는 viewer=False로 원 OFF JSON을 읽어 새 정적 카메라 이미지만 만든 보완이며 기존 snapshot을 덮어쓰지 않는다.

위 제한은 snapshot 표시의 문제이며 중력0/물리 API 차단/시간0/사람 상태 불변의 검사 결과를 바꾸지 않는다. 이전 GUIDE 역시17inputs에 들어 있어 소비 후 수정하면 안 된다는 보존 주의를 함께 전달했다. 문서 최종 SHA와 위 제한 설명 보완을 기다리며 아직 최종 판정을 동결하지 않는다.

## 잔류 viewer 선 보완 entry 실행 전 검수 — 2026-10-08

요약 판정: 문제없음. 새 entry 코드 사전 판정 PASS. 위 snapshot 경고에 대한 실제 보완 검증은 아직 실행 전이다.

`/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_static.py:13` — 새 subclass는 save_candidate 진입 직후 viewer debug선을 clear_lines로 지우고, 부모의 정적 capture만 수행한 뒤 finally에서 draw로 현재 표시를 복원한다. T/S가 같은 batch여도 capture 직전에 정리하므로 원 경고의 호출 순서를 코드상 해소한다. StrapTrialRecording의 ON route overlay는 카메라 캡처 후 별도 표시라 유지된다. 선 정리/복원은 graphics 호출이며 물리 API를 추가하지 않는다.

`/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_static.py:7` — 부모 초기화와 session을 그대로 유지하고 새 source SHA를 snapshot_implementation.json에 별도로 기록한다. main은 기존 static app.Editor만 실행 기간에 subclass로 바꾸고 finally로 복원한다(23~29행). 단일 UI thread의 재사용 진입점이며 기존 파일을 덮어쓰지 않는다. 새 launcher는 새 모듈을 호출하고, ENTRY 문서는 새 권장 명령과 기존 guide의 조작법 참조를 구별한다.

Critical: 없음. Warning: 없음. Suggestion: 없음. Python AST3.8 PASS / launcher bash-n PASS. 검수자의 native·harness·물리·이미지 생성 실행0회.

사전 source SHA256:
- guitar_pose_static.py: `8ec39a4bc663cadeaec0f77b0b8980da06bc1b51014f8bf547e6b11b237bdace`
- open_guitar_pose_static.sh: `20388cf12cad24527600a67cb36584479d563a7128e4c3b8cb67eb2a04808721`
- GUITAR_POSE_STATIC_ENTRY.md: `93e5c934cf6976f7e359bc5f52a16c01ca99d9e4953214ce0c54719b45f94d18`

既存 static core/guide/plan과 원 snapshot은 보존하며 실제 연속 입력 저장 검사·최종 문서 뒤 전체 최종 판정을 기록한다.

### same-batch 캡처 회귀검사 코드 사전 검수

`/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_static_snapshot.py:17`은 viewer route ON을 draw한 다음 T/S handle을 중간 draw 없이 연속 호출하여 원 잔류선 조건을 재현한다. 부모 환경 초기화 외 physics 실행을 호출하지 않는다. whole-body/hands PNG의 지정 orange threshold pixel 수를 builtin int로 저장하고,0개/전체 native 상태 불변/steps0/strap 표시 OFF 네 조건을 검사한다(23~33행). 이 색 검사는 해당 주황 debugline 범위이며 모든 색·mesh·자세 품질 인증을 의미하지 않는다. JSON checks는 Python bool이고 counts는 Python int라 기존 np.bool_ 요약 저장 문제를 반복하지 않는다. 종료 시 scene을 정리한다.

코드 사전 판정: PASS. AST3.8 PASS. source SHA256: `a3f905aa6bc99587d42e295ddd881aa604997b0b23f7bfeb578249c029987ad6`. 검수자가 이 검증을 실행하지 않았다.

## 새 entry 실제 snapshot 검증 대조 — 2026-10-08

`snapshot_verified/verification.json`의4checks는 모두true다. 중간 draw 없는 T→S 뒤 whole_body/hands orange_debug_pixel_count는0/0, 전체 native 상태 불변, physics_steps0,strap 표시OFF를 기록한다. snapshot_implementation.json은 실행 전 검수한 entry source SHA `8ec39a4bc663cadeaec0f77b0b8980da06bc1b51014f8bf547e6b11b237bdace`와 exact다. 새 candidate는 physics_enabled=false/steps0/strap_enabled=false/strap_visible=false다.

capture.json의 step0/render-preserves-state=true 및 새 두 PNG current SHA exact를 독립 읽기 검산했다. 새 whole-body PNG도 직접 열어 주황선이 없음을 확인했다. 이4개 검사는 지정 orange debugline에 대한 보완이며 전체 geometry/접촉/자연자세 품질 검증으로 확대하지 않는다. 새 entry는 앞서 기록한 eventbatch snapshot 경고를 코드와 실제 검사로 해소했다. 원 snapshot/정적 core/18검사/clean capture를 삭제·덮어쓰지 않는다.

검수자의 native/physics/harness/이미지 생성 실행은0회다. 최종 권장 launcher와 새4소스 및18+4검사를 반영한 최종 문서 SHA 확인 뒤 전체 판정을 동결한다.

## 최종 문서 검수 및 동결 — 2026-10-08

요약 판정: 문제없음. Critical: 없음. Warning: 없음. Suggestion: 없음.

최종 권장 진입점은 `/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh:9`의 새 entry다. 기존 static core/guide/plan/launcher와 원 잔류선 이미지, clean_static_capture, 이전 v1 소스·물리 기록은 보존된다. 새 entry는 정적 core를 상속하며 물리 API 차단과 시간0 조건을 유지한다. 사전 경고였던 같은-batch T/S의 저장 선 잔류는 새 entry의 capture직전clear_lines 및 실제4개 검사로 해결됐다.

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/README.md:12`는 최종 launcher를 안내한다. 21행은 기존18검사와 별도4검사의 범위를 구분하며, 25~33행은 원 OFF snapshot의 잔류선·원본보존·새 snapshot_verified OFF 이미지와 UI eventbatch 원인을 정확히 설명한다. 자연스러움·접촉·지지/clearance 인증은 주장하지 않는다. T는표시전용/Space,E무효/물리step,trial,새영상0이라는 설명은 실제 코드·저장검사와 맞는다.

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/CHANGED_FILES.md:8`은 새 entry/launcher/ENTRY문서/snapshot검사4파일과 기존 core 보존을 구분한다. 결과 README/CHANGED_FILES/ENTRY문서의 절대 로컬 링크33개는 모두 존재하며 명시 줄 번호도 범위 안이다. main README1360행/PLAN2190행은 새 권장 명령과 원 잔류선 수정 경위를 기록한다. VISUAL_REPORT2191~2193행은 위 원 OFF 사진의 잔류를 정정하고 새 entry의 실제 OFF 이미지를 제시한다. 기존 main3 prefix SHA는 모두 exact이며 최신17inputs current SHA도 전부 exact다. 기존 자동 실험 중단 상태는 유지된다.

새 entry/launcher/ENTRY문서/snapshot검사 source SHA는 직전 사전 검수 기록과 모두 exact다. launcher_help.log의 새 CLI 옵션/정적 설명을 읽었으며 root의 실제 help exit0 관측과 정합하다. 검수자는 launcher/native/harness/이미지 생성/물리 실행을 하지 않았다.

최종 문서 SHA256:
- 결과 README.md: `405da5c98d3b24c0033d1d2a3ea2d55bf59ad678b36ac5c7a7fe78ac1512929f`
- CHANGED_FILES.md: `f364525ccf0a7283410af82cc0d5a8484889e76a5216ac901e30d08bde5d6559`
- GUITAR_POSE_STATIC_ENTRY.md: `93e5c934cf6976f7e359bc5f52a16c01ca99d9e4953214ce0c54719b45f94d18`

최종 판정: PASS

판정 범위는 물리 없는 새 정적 도구와 capture 보완 entry, 저장18+4검사, 실제 정적 PNG·후보·최종 안내와 문서의 정합성이다. 시각적 자연스러움 자체는 사용자가 선택할 대상이며 검수자가 성공으로 인증하지 않는다. 이후 root의 최종 보존 감사·선택 source snapshot·phase inventory 완료는 이 판정에서 선취하지 않는다. 검수자의 변경은 이 review.md 생성/append만이며 기존 동결 파일을 수정하지 않았다.
