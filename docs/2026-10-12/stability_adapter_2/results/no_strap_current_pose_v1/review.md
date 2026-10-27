# 현재 초기 자세의 무스트랩 영상 사전 검수

요약 판정: **문제없음**. 최종 미실행 adapter/wrapper에 구체 실행 blocker가 없다. 검수 소유권은 이 파일뿐이며 원본 runner·기존 봉인 결과·타인 파일은 수정하지 않았다.

- [새 환경 subclass](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_current_pose.py:28)는 원 CameraEnvironment 초기화/scene/filter/초기 state/PD/카메라를 재사용하고 live leg DOF가0인지 검사한다. 부모 초기화는 prepare/reset/목표 제출/route read만 수행하며 외력 제출이나 simulate 호출이 없다. 이후 override는 tension0·simulate/fetch·steps 증가만 수행하여 부모의 cable-force 경로를 호출하지 않는다. 기존 중력·native contact·PD는 유지한다.
- [외력 API guard](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_current_pose.py:18)는 `apply_body_force_at_pos`, `apply_body_forces`, `apply_rigid_body_force_tensors`, `apply_rigid_body_force_at_pos_tensors`를 차단/시도 계수한다. 최초 검토판에서 SDK의 `apply_body_forces`가 누락됐으나 미소비 단계에서 추가돼 해소됐다. 현재 호출 경로에서 숨은 strap-force 호출은 발견하지 않았다. 실제 시도0·전 trace tension0은 실행 후 원자료에서 별도 확인해야 한다.
- [runtime 교체/복구](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_current_pose.py:44)는 모듈의 환경/recorder/save를 교체하고 finally에서 복구한다. 원 frozen runner는 main 안에서 환경과 recorder를 import하므로 교체 대상이 실제 루프에 반영된다. 원 GymTrialRecording을 사용해 whole_body·hands 두 view의 원본 native 프레임을 저장/encode하며 route overlay를 추가하지 않는다. 새 metadata는 strap 비활성/표시 없음과 inactive nominal rest length를 명시하고 inherited scope를 출처로 구별해 보존한다. 원초기/PD/81목표·손목 파형을 바꾸는 코드가 없으며 source fresh14/1188은 재사용된다.
- [wrapper 사전 보존](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_video_phase.py:24)을 frozen runner의 실제 hash/read 목록과 대조했다. 최초 검토판에서 계획4개와 DejaVuSans 글꼴5입력이 빠졌으나 최종판32..35행에 추가됐다. canonical 계획/소스 사본과 R 밖 글꼴의 별도 external 경로 사본, proposal/trial/current baseline 자료를 보존한다. 이전 proposal의 실제 소비 closure는 SHA로 유지하며 과거 nested snapshot을 재귀 복사하지 않는다. proposal 전 SHA와 frozen entry `2f6565f3…`/runner `34d50c9f…`도 실행 전에 강제한다. 실행 후 SHA/로그/exit/환경을 남기며 원 runner는 오류/partial을 보존한다.
- [계획](/home/ajou/yigyu/3/stability_adapter_2/NO_STRAP_VIDEO_PLAN.md:1)은 현재52.09° 초기 자세에서 스트랩 힘을 끄는 별도 비교로 명확하다. source 호환 손5관절 후보·새 자세 탐색·actor·학습을 이번 trial로 확대하지 않는다. 기타 낙하/자세 변화도 결과이며 안정성을 완료 gate로 강제하지 않는다. 현재 rest-length/route trace는 비활성 진단값으로 구별하고 스트랩 그림만 숨긴 기존 영상 편집으로 설명하지 않는다.

검증: 최종 두 소스 SHA 일치와 Python3.8 AST 통과. 클래스만 AST로 분리해 가짜 Gym에서 부모 초기화 상속, 부모 strap step 미호출, simulate/fetch 한 번, steps+1/tension0 및 네 API의 거절·계수를 확인했다. 실제 Gym·실행 main·runner·physics·actor·훈련·렌더는 import/실행하지 않았다. 원 proposal/source SHA와 trial 선언 SHA도 읽기 대조했으며 실제 출력/초기값 동일성/영상 QA는 후속 검수다.

- 최종 `run_no_strap_current_pose.py` SHA: `9e065b99874b66d75601afa1c9a40df4062348ef75ce6a606fc3811def799324`
- 최종 `run_no_strap_video_phase.py` SHA: `639b7ed8be071f3b94f40725afebf3b17c567e2dea01d6c01a808abbf4883e49`

## 실제 무스트랩 실행·저장자료 분석·영상 수집 검수

요약 판정: **문제없음**. 원 native와 분석·수집 main을 재실행하지 않고 실제 저장 자료를 독립 계산/해시 대조했다. native 실행14028입력/180사본, 분석327입력/17사본, 수집148입력/5사본의 현재 원본·사본·전후 SHA/로그/exit0가 각 기록과 일치한다.

- 실제 report는 1초기화 시도/1초기화/1200step/5.000초 완료·failure 없음이다. baseline과 현재 초기 상태/PD/G·motion 등을 비교하는 [필드 목록](/home/ajou/yigyu/3/stability_adapter_2/analyze_no_strap_video.py:28)은 실제 **20개**이고 모두 exact다. 소비된 check명 `all21_initial_fields_exact`의21은 명칭 오류로 root에 전달했다. 원본 소스/분석을 수정하지 않고 후속 문서에서20개와 legacy check명 차이를 설명하도록 했다. 검사 대상 자체 누락/실패를 뜻하지 않는다.
- 81×1200개 final target, physics_step·updated flag·command clock·wrist delta가 baseline과 exact다. 두 조건 각각1201개 raw state/trace의 순서·시간, 고정 Pelvis/하체9 body, report checks, fresh14검사/1188 source self pair clear를 확인했다. [무스트랩 mode](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/no_strap_mode.json:1)는 force API 시도0/1200step, 전1201 trace의 실제 제출 장력은0이다. Nominal route/rest length 진단값은 스트랩 힘 활성의 증거로 해석하지 않는다.
- Raw 기타 body pose에서 goal 오차를 다시 계산하고 SciPy SO(3)로 회전을 독립 검산했다. 또한 시작2..4초/1/60초 stride의121개 완전1초 window(각241샘플)를 별도 계산했다. [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis.json:1)와 위치·각도 max/end/rolling 수치가 계산 오차5e−15 이내로 맞는다. 무스트랩의 초기goal 최대 이탈은20.584004105mm/12.152976624°, 종료20.525764460mm/12.145216233°다. 후기1초 최대 변화는0.335897491mm/0.064720324°이며 baseline은0.648624666mm/0.115306041°다. 무스트랩은 초기 임시30mm/5° 조건 밖1145/1201샘플, 후기1초 조건 안121/121 window다. 후기 변화 감소를 초기 자세 유지/자연성/연주성공으로 확대할 수 없다.
- 원 capture151프레임의0..1200/8step 시각·read-only와302 PNG SHA를 확인했다. 두 MP4 현재 SHA와 실제 ffprobe는 각각1280×720/151frame/30fps/5.033333초다. 시뮬레이션은5.000초이고 MP4 길이는151/30초다. 실제 t=5초 hands PNG를 열어 원 native 장면과 주황 route overlay가 없음을 확인했다. [collector](/home/ajou/yigyu/3/stability_adapter_2/collect_no_strap_videos.py:25)의 전 source/dest 사전검사 후 복사와 실제 수집 기록을 대조했다. 기존140영상·index v10 SHA 보존, 새 원본2개 exact 복사/142개·index v11/update v10 일치다.
- 소비된 분석 wrapper는 `build_fixed_lower_asset.py`를 보존하지만 거기서 import되는 `strap.py`를 분석 stage 입력으로 별도 나열하지 않는다. 이를 root에 전달했고, 해당 canonical `strap.py`의 native 실행 전후 SHA/사전 사본/현재 SHA가 exact인 것을 직접 확인했다. 후속 root 감사는 이 이전 native 보존 근거를 명시적으로 확인한다. 별도의 분석 stage 전체 transitive source closure를 보존했다고 확대하지 않는다. consumed wrapper/출력은 유지한다.

세 새 후처리 Python 소스 AST3.8 검토 통과. 이 검수에서 수행한 영상 도구 호출은 저장 MP4 ffprobe 읽기뿐이며 새 native·physics·분석·수집·렌더·actor·학습 실행은0이다. 최종 결과 문서/ROOT 설명/누적 VISUAL 추가분은 후속 검수 범위다.

## 최종 문서·실제 이미지·감사 코드 검수: PASS

요약 판정: **문제없음(PASS)**. 남은 material blocker는 없다. [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/README.md:1)의 표 전체를 독립 재계산 수치와 대조했다. 실제20필드와 legacy21 check명 구분, nominal LA/route의 비활성 상태, 무스트랩 후기 변화 감소와 큰 초기회전의 tradeoff, 자연스러움·연주·cooked contact 미인증 범위가 정확하다. 두 MP4는 inline embed이고 새 실제 영상으로 설명한다.

- README의 hands/whole_body t0/t5 원본4 PNG를 실제로 열어 확인했다. 원 native scene이 기록됐고 주황 route overlay가 없다. 실제 sim5.000초/MP4 151/30=5.033333초 구분과302PNG·두151프레임영상 설명이 맞는다.
- [ROOT 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/ROOT_VERIFICATION_NOTES.md:1)은20필드 label 정정과 transitive `strap.py`의 native 사전 보존 근거/분석 stage 별도 사전행 누락 한계를 명시한다. 이를 원자료 변경이나 분석 stage 사전 보존 완료로 소급하지 않는다. CUDA/visual geometry 경고 보존과 CPU PhysX 관측 범위도 구분한다.
- [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/CHANGED_FILES.md:1)과 [main README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1110)·[PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1931)·[VISUAL §111](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2024)의 실제 수치·실행 횟수·권한·별도 무스트랩 조건/후속 손5관절 계획 구분이 정합한다. 문서 링크와 실제 line 범위, journal의 main 기존 prefix SHA 보존을 확인했다. CHANGED의 시점에 종속됐던 precheck-only 문구는 중립적인 독립검수/봉인 기록 설명으로 정정됐다.
- 미실행 [root 최종 감사 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/root_final_audit_producer.py:17)를 읽기·AST3.8 검토했다. 현재 입력/사본/로그·이전 선언 inventory·140→142영상·main 기존 prefix·0force/tension·실제 카운터/PNG와 supplemental strap helper를 확인하는 범위에 구체 blocker가 없다. 마지막 미소비 delta는 이후 append 가능한 main canonical3개를 inventory에서 제외하되 실행시 SHA 대조와 source_final 사본/사본 inventory는 유지하는 변경이며 보존 목적과 맞는다. root 소유 감사 main은 검수자가 실행하지 않았다.

최종 동결 문서 SHA: README `b47002b390a7d27e7edad16b086e12108968f2a4fb44b378f0a734d59b488f6b`, CHANGED_FILES `190cd22d1826f2a8c6c6d0db778de9f1e19bba681db9e05eabee78891848f87c`, ROOT_VERIFICATION_NOTES `78ecef250fb860ebb810a27e7883f42f5dc837c9b03b0e7f13c755637cf25e1a`이다. 최종 미실행 감사 소스 SHA는 `888af5b01a3df88bb5455cb5605dad145060ec7df94af47c2297016c4e909817`이다. 검수 기록을 동결한다. 이후 실제 최종 감사·봉인은 root의 별도 실행 기록으로 남긴다.
