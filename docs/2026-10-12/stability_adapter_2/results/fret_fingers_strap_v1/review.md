# 고정 길이 스트랩 + Fret 손가락 최종 검수

요약 판정: **문제없음 — 구현·제어권·native_v2 완료 기록 검수 PASS**. 기타 초기 회전 유지·운지·음악 목표는 미달성이며 첫 native fault 원인은 미확정이다.

Critical: 확인된 코드 결함 없음.

Warning:

- [native_crash_audit.json:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_audit.json:2): 첫 실행은 exit139로 중단되고 마지막 1.9초까지 58frame만 보존됐다. 같은 소스·물리 재시도가 완료됐어도 원인 해결·반복 재현성이 입증되지는 않는다. **제안:** 두 시도의 분리 보존과 미확정 원인 표기를 유지하고, 이후 동일 fault가 재발하면 faulthandler stack의 실제 native 호출을 먼저 확인한다. 이번 문서/감사에서는 이를 명시했다.

Suggestion: 없음.

## 소스·제어권·물리 적용

[underneck_strap_environment.py:13](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:13): raw force callback의 우회는 전용 수동 스트랩 제출에 한정된다. 나머지 force/effort·시작 후 state API는 기존 NoStrapGym guard를 유지한다. 현재 기타 목표 오차가 force law에 입력되지 않으며 기타 고정·손 부착·반복 pose 덮어쓰기가 없다.

[underneck_strap_environment.py:24](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:24): 현재 13점 route/속도와 inherited rest 1.1018469719600776m, k6000N/m, d120Ns/m, cap300N으로 기존 law를 평가한다. 기록 892행의 force/tension/route length/length rate를 독립 재계산해 모두 exact 일치했다. 매 physics step 0~891이 1행씩 있고 경로 힘 합의 최대 수치 잔차는 3.55e-15N이다. 길이·gain·관절 초기값을 조정하는 변경은 없다.

[run_fret_fingers_strap.py:109](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py:109): 2.000초 준비 후 Fret21/인계 L9/hold15/초기36의 81축을 단일 목표로 제출한다. L9의 준비 마지막 제출 목표는 PLAY103control 동안 exact 유지됐다. 실제 L9는 인계값에서 최대 0.037986rad 움직여 물리 고정과 다르다. 실제 제출 목표/history 회신, 단일 control당 4step, 원본 source frame0~102 평가·최초 done 종료 및 학습0·Strike OFF가 유지됐다. native runtime24검사가 PASS이며 금지 state 쓰기는 없다.

## 영상·비교·자료 보존

- native_v2는 892step/3.716667초에서 원본 index finger_back 실패로 종료됐고 actor103회·source done 마지막 1회다. 최종 controls.source_info와 terminal_info는 같다. goal_finished/normal_termination=False, press0%, sustain0/4다. 5초 cap 또는 terminal 이후 HOLD가 없다.
- native t=0 body/DOF 상태는 직전 strap OFF baseline과 exact 같다. 이후 PREP 상태/목표가 동일하다고 주장하지 않는다. 소스·물리가 같은 1차와 재시도의 저장 58frame raw/overlay SHA prefix도 exact였다. 다만 이것이 첫 fault 원인이나 전체 실행 재현성을 증명하지는 않는다.
- native_v2 카메라 113frame은 terminal step892를 포함하며 trace/camera step 열이 같다. raw/overlay452PNG SHA와 두 MP4 SHA를 재확인했다. 각 영상 113frame/30fps/3.766667초와 물리 시간은 구분돼 있다. 완료 영상 2개와 첫 시도 partial2개의 모음 복사본이 원본 SHA와 같다.
- terminal을 제외한 모든 camera route 점은 같은 physics step의 다음 force 평가 route와 exact 일치한다. 2초·종료 native 전신/손 PNG를 직접 확인했다. 주황색 선은 실제 13점 경로 overlay이며 장력0N에서도 표시된다. 천의 두께·처짐·물리 재질 렌더 또는 지속 지지의 증거라고 주장하지 않는다.
- 완료 run1156입력은 실행 중 불변이었다. 두 run의 현재 main PLAN/README2개 사후 추가는 각 source_before 소비 SHA로 보존됐고 나머지 현재 입력 SHA가 일치한다. 분석16개 입력 SHA, 공통 시각 자료3개 입력 SHA, 최종 audit19개 입력 SHA, source_final11개 원본 SHA가 일치한다. 첫 시도의 정상 wrapper closure는 없으며 root 사후 확인과 구분돼 있다. 직전 봉인 phase1213artifact도 재해시해 모두 그대로였다.
- analysis26검사/recording_audit35검사 PASS. frozen README29개·CHANGED_FILES33개 절대 링크와 실제 줄 번호가 유효하다. 첫 시도 중단·완료 run 운지 실패·학습환경 전이 차이·원본 profile/native XML 한계·CPU PhysX/GPU 동등성 한계가 문서에 표시돼 있다.

## 물리 판정

[analysis/time_samples.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/time_samples.json:1): 양의 장력은 step41~47, 0.170833~0.195833초의 7step에서만 발생했고 최대 32.365446N이었다. PLAY2초 이후 전부 0N이다. 초기 실제 route1.073577334m와 최종 적분 직전 route0.967968522m는 고정 rest보다 짧다. 숫자는 law로 계산·제출한 값이며 force sensor 측정값이 아니다.

같은 2.766667초에는 OFF72.743mm/9.855°→ON66.212mm/8.924°로 조금 줄었으나, 같은 3.700초에는 OFF24.473mm/47.569°→ON51.306mm/49.441°로 더 커졌다. 새 실행 전체 최대69.082mm/51.500°·최종68.456mm/51.500°이며 운지는 실패했다. 일관된 안정화·초기 회전 유지·음악 성공은 확인되지 않았다. 한 길이 시험의 결과를 모든 strap 구성의 불가능성으로 일반화하지 않는다.

## 검수 자료 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py`: `e60fe4d4f792254d5b95bd4c1fb689a1c11293c67663dcf67e2f12a0427dc88e`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py`: `a6533a1a7a8151eac1105ef75308cd737f927454c6beeea2a2c04f811d4c9064`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_strap_preserved_run.py`: `efc4680541d6a5ad9d80503c7065311b10b0857b553c0a1c4a1dd624d3025dc0`
- `/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_STRAP_PLAN.md`: `7f95a5bcba348920787309d15cbdb4249563b0a5ade4f212bd24f0a70bf0017f`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_strap.py`: `c60dd5537c9dbc0204ca37e28ab5f30dbba7fec6eb49a406125a0ed1a522a60e`
- `/home/ajou/yigyu/3/stability_adapter_2/strap.py`: `2dd34bc52286878569ee83a1c02e15daeb35b8fe14a275d64d8a1be1969d3361`
- `/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py`: `a52a33eecdb943d0acbc7faffa51816ab47447c7a9c48d4036e8dd70fb7353f3`
- `/home/ajou/yigyu/3/stability_adapter_2/PLAN.md`: `0d3c7346964dadcab18676fc70847818fbda4f25aa55ebb5aea2dd87e06e493e`
- `/home/ajou/yigyu/3/stability_adapter_2/README.md`: `50f39685ddbabadd2e60bb771d303a7d3bcf6f741f64b7b5ad12a0e3d28b380d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md`: `97cef5b6f8cf923b53c5d8b5966b24067498287ddb570d86e3f4e2ec8afdf65b`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/CHANGED_FILES.md`: `b84147ba85cda13f39103e13a582b8127b3a38e2b0a676e36f7b2cfa9ed7ecc0`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/pre_review.md`: `70ec781d72e40753bdc8098dcaec1198b273e0b022c9b6dfb060c8d8978031cf`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/crash_review.md`: `dfa9af74b51b4a5007958fc3b71404d915bebd0d8f4f215806e7950060dae23a`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_audit.json`: `2cbfcdf116a4f1956814ccbeae1d0fbc36a1d9172243e7f240e150d82037cabc`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/retry_plan.json`: `836a79d0d47cadcc7aaa0fda5a1cf02593e65c10d66ab674614ebb82cb5bc50c`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/source_preservation.json`: `5b7d7f88ee92d36f961bcff66b847f3c5e6beb7d4e6eed56fbbd9ccedd66d9c4`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/recording_audit.json`: `6ea10f53f37683cf2a14f9bf1266726e4f5cc7b52fc06eb5cf9edcf7f79e4f1c`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/summary.json`: `49e4d65bd4bbe209338068649dbc526114732bf284fca97d92e2caf8a71d79f7`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/inputs.json`: `04929800e8781b7c9015410d09f85b3808ffdaafc20ebe09cc909ca6d66e6a9d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/time_samples.json`: `756c2bde83a63a15c20f916580a24588c4ee36185c3862be5d2ba33efb84315d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native/inputs_before.json`: `15e9e90716d5aa157db80fa9965b6ec021b27bf4e4ee3cc7d88c58d4921ad196`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native/data/images/capture.json`: `f0bec303f836ba073cb7f41072458ed4242fb4e055199f50677fc5f4ba963575`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_partial_v1/manifest.json`: `3bfee8a1fe2928eebe07f6366c4158625d149162787ccc17526633c223a9ee56`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/inputs_before.json`: `15e9e90716d5aa157db80fa9965b6ec021b27bf4e4ee3cc7d88c58d4921ad196`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/inputs_after.json`: `c43cc7e6ab623c06e2859432fc2a6cfa64920dd85ab9f64d18b1c3bbd91d0db8`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/report.json`: `30d30609e7448892cd3731610aacab82a7fd72eba006e7bb8e42fef266984012`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/initial_values.json`: `091c36527d40ec8c601cece91c490541433b118182dcf424102343f471d6cb74`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/handoff_values.json`: `ed30bbf1b5ef941a27f33c985b2d681c72cf1e50a4c8bb7b24e53848e3570659`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/terminal_info.json`: `ce8c11fa6d19cc98761cf188932487937fa990584fab08e3a1816ae43265398d`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/controls.json`: `9022c9c509be97955172d42f78d625a111c47c49fcbf216eaa00ea4f11bdefa5`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/trace.json`: `fe25a11da2822f071edb6f6e436ac2d66348d832696f6a83055b29118a677abd`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/strap_forces.json`: `42e9e3a1c59a68784b1321cfe5220ec317bb40e0a2c07ee32a8e45fcc760a1cf`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/capture.json`: `83b0da6c49081dfee10aa955f5d9aefe6f3c6663d2559f643e77cefc3be25459`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_fret_strap.md`: `19634e1a37b8ff59be610cfda8728866cd5ea64b64c7a94762dc11a90b0735ba`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_COLLECTION_fret_strap.json`: `4054eb7342c3751eff3d7dbf798819be22f9ac54fa1cab070fc053e687a9388b`
