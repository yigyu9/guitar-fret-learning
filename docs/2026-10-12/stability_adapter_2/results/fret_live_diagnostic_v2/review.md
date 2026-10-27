# 현재 기타 기준 Fret 실시간 진단 v2 독립 검수

## 사전검수

**요약 판정: 문제없음(사전검수).** 분석 입력 봉인 Warning은 실행 전 개정본에서 해소됐다. v2 native 결과 검수는 아직 수행 전이다.

- **Critical:** 없음.
- **Warning:** 없음. 최초 analyzer의 입력 helper SHA 누락은 [analyze_live_fret_diagnostic.py:25](/home/ajou/yigyu/3/stability_adapter_2/analyze_live_fret_diagnostic.py:25)에 `gym_trial_recording.py`, `live_fret_geometry.py`, `body_center_coordinates.py`, `validate_team_pose_envelope.py`를 추가하여 해소됐다. 분석 실행 전 개정이며 초안/개정본은 별도 보존됐다.
- **Suggestion:** 없음.

새 leaf 계획, `live_fret_recording_v2.py`, `run_live_fret_diagnostic_v2.py`, `.sh` 및 새 analyzer를 읽었다. 기존 v1 recorder와 runner/wrapper는 수정하지 않았고, v1의 두 native camera writer crash 및 partial 자료를 보존한다.

`NativePixelRecording.capture()`는 기존과 동일하게 `step_graphics` → `render_all_camera_sensors` → 동일 `IMAGE_COLOR`를 읽고, RGBA 배열을 즉시 copy한 후 PIL PNG만 저장한다. 기존 raw recorder의 디렉터리·views/fps/interval·frame list·encode 인터페이스와 호환된다. `LiveFretRecordingV2`는 v1의 목표/좌표/접촉 관측과 source/native/target 불변 검사를 상속한다. wrapper는 원본 runner의 recorder 및 view 생성만 임시 교체하고 `finally`로 복원하며 physics/controller/goals 호출을 추가하지 않는다.

독립 문법검사: v2 recorder/wrapper 및 analyzer **AST PASS**, v2 shell **bash -n PASS**. 실제 새 `NativePixelRecording.capture()`를 fake camera/native-state에 연결한 검증에서 두 RGBA PNG의 decode 픽셀 exact round-trip, 1개 frame/time 기록 및 상태 불변을 확인했다(**PASS**). 이 mock은 실제 native 렌더 검증을 대신하지 않는다. 실제 native PNG의 픽셀, 전체 제어·trace exact 일치, first done 종료 coverage는 실행 결과에서 확인해야 한다.

## 후속 결과 검수

**최종 요약 판정: 재작업 필요(전체 live 녹화 미완료).** v2도 native `get_camera_image` 호출에서 exit 139로 중단됐으며 마지막 완전 diagnostic frame은 step 240 / 1.0초다. 첫 source done까지 실시간 진단 full run 검증은 통과하지 못했다. v1의 파일 writer만이 원인이었다고 결론 내릴 수 없고 정확한 native crash 원인은 미확정이다. 확인된 논리·보안 Critical은 없으나 full live 성공으로 보고할 수 없다.

독립 픽셀 대조: v1 첫 실행과 v2의 공통 27frame × 2view = **54 PNG**를 RGBA로 decode하여 byte 배열을 비교했고 다른 픽셀은 **0개**였다. 이는 공통 prefix 픽셀 보존 증거이며 전체 실행 또는 crash 원인 증거는 아니다. 저장된 v2 31frame은 관측 source/native/제출 target 불변을 기록했다.

반복 native 실행을 중단하고 이전에 완료된 baseline native frame/state/control을 사용한 별도 saved/offline 진단으로 이어간다. 기존 자료를 읽은 offline 진단과 신규 live instrumentation 완료 여부를 구분해야 한다. offline 신규 검수는 별도 지정 review에 기록한다.

최종 README 검수: 마지막 완전 31frame/step 240/1.0초 뒤 native 조회 crash와 full live 미완료를 정확히 기록한다. v1/v2 27frame×2view 및 완료 baseline/v2 31frame×2view 픽셀 일치를 전체 실행 성공 또는 crash 원인 증거로 확대하지 않는다. 보존 raw/표시/partial 자료와 링크 존재를 확인했으며 문서상 추가 Critical/Warning/Suggestion 없음. 검수 기록을 닫으며 v2 전체 live 실행은 미완료 상태로 보존한다.
