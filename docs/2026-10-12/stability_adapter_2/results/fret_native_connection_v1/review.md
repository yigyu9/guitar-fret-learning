# 왼손 Fret native 연결 최종 검수

요약 판정: **문제없음 — 연결 구현·종료 녹화·결과 보고 검수 PASS**. Critical / Warning / Suggestion 없음. **운지·기타 안정화는 실패**했으며 해당 성능 목표가 달성됐다는 판정은 아니다.

검수 범위는 새 native Fret 연결 소스, `native_v3` 원자료와 영상, tensor preflight v3, 결과 README 및 변경 파일 색인이다. 공용 구현이나 물리 상태를 수정하지 않았다. 입력 보존 감사·최종 봉인은 root의 별도 담당이며 이 검수 기록을 대신하지 않는다.

## 제어와 원본 계약

- [fret_native_view_v2.py:23](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view_v2.py:23): SHA를 고정한 원본 Fret action tensor 처리와 물리 이후 평가 tail을 분리했다. 원본 shared physics 금지 분기를 보존하고 source view 자체가 물리를 전진시키지 못하도록 차단한다. terminal reset은 물리 상태를 덮어쓰지 않는다.
- [run_fret_native_connection_v3.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:49): Fret 30축, bounded hold 15축, 초기 목표 유지 36축의 소유권은 서로 겹치지 않고 native 81축 전체를 덮는다. PLAY에서 기존 왼팔 hold가 policy 목표에 더해지지 않는다. raw 제출 목표의 다른 36축은 초기 목표와 전 구간 동일하다.
- [run_fret_native_connection_v3.py:88](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:88): PREPARE 120 controls 동안 actor 호출이 없고 source frame은 0이다. t=2.0초에 source frame 0에서 actor를 연결해 46 controls/frame 0..45를 실행한다. 목표 제출 뒤 owner가 4 substep씩 전진시키고 평가를 한 번 수행한다.
- [run_fret_native_connection_v3.py:125](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py:125): 원본 첫 done에서 즉시 break한다. raw controls에서 done은 마지막 행에만 있으며 terminal info와 마지막 source info가 정확히 일치한다. 이후 actor 호출·terminal HOLD 기록은 없다.
- [native_v3/data/initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/initial_values.json): checkpoint SHA·420/30/6 계약, profile의 source target/정규화 용도, native XML hard limit, 자산 2개·구현 10개 차이, 자유 기타·스트랩 OFF 및 Strike actor 미사용을 기록한다. 원본 고정 기타 학습 환경의 재현으로 설명하지 않는다.

## 실제 녹화와 보존

[report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/report.json)의 runtime 검사 15개는 모두 PASS이며 native 실행 오류와 finalization 오류는 없다. [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/inputs_after.json)의 실행 전후 입력 1,143개 불변 결과를 확인했고, 최초 독립 검수 시 모든 입력의 실제 SHA를 대조했다. 이후 main PLAN/README에 실행 결과가 추가됐으므로 현재 모든 원래 경로의 SHA가 같은 것은 아니다. [source_preservation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/source_preservation.json)에 기록된 native v2/v3의 해당 main 파일 `source_before` snapshot SHA를 직접 대조해 실행에 소비된 모든 입력 bytes가 보존됨을 확인했다. 나머지 입력은 현재 경로의 SHA가 일치한다. 실행 후 main 기록은 `source_final/main_after_run`에 별도로 보존돼 있다.

원자료에서 PREPARE 120 + PLAY 46 = 총 166 controls, 664 physics steps가 확인된다. 물리 종료 시각은 `2.7666666666666666`초다. camera와 trace는 모두 84행이며 physics step `0, 8, …, 664`와 정확히 일치한다. 마지막 영상 프레임은 실제 종료 상태이고 모든 capture의 render-state 보존과 PNG SHA가 통과했다. 독립 ffprobe에서 전체/손 MP4 두 개 모두 1280×720, 30fps, 84프레임, 2.8초를 확인했으며 파일 SHA는 report와 일치한다. 물리 시간과 MP4 재생 길이를 구분해 보고한다.

## 실패 결과의 정합성

[terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/terminal_info.json)의 `finger_back_termination=True`, index/ring 표식 `[True, False, True, False]`, `failure_termination=True`, `goal_finished=False`, `successful_termination=False`가 확인된다. 46 PLAY controls의 `press_success_rate`는 모두 0이며 sustain 성공은 0/2다. 이 source 후면 종료 플래그를 실제 접촉·관통 확정 증거로 표현하지 않는다.

실제 t=2초와 종료 native 이미지를 확인했다. [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/trace.json)의 초기 t=0 기준 G 변화는 이관 시 51.094mm / 6.495°, 종료 시 434.475mm / 68.336°다. 기타는 PLAY 후 크게 내려가고 회전하므로 이번 시도는 안정화 성공이 아니다. README는 이 실패와 원본 환경 차이를 명확히 보고한다.

검수 중 README의 실제 관절각/profile 목표 구분, 측정 시점, 기준 pose 및 오른팔 목표 hold 표현을 지적했고 최종 문서에서 수정됨을 확인했다. 이관 시 실제 관절각의 profile 최대 초과 0.095522rad는 해당 시점의 값이며 실행 전체 최대값이라는 주장은 없다. preflight v2의 history 혼입 문제도 별도 v3 baseline 비교와 복원 관측 일치 검사로 해결되어 10개 검증을 통과했다.

## 후처리 감사 확인

[recording_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/recording_audit.json)의 23개 검사 PASS와 참조 입력 SHA를 확인했다. [analysis/inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/analysis/inputs.json)의 9개 입력, 실제 소비된 primary/preflight/계획의 `source_final` 사본, 실행 후 main 사본 및 영상 모음의 원본·복사 SHA를 직접 대조했다. 결과 README와 변경 파일 색인의 절대 경로·줄 번호 링크가 실제 존재하는지도 확인했다. 감사가 `recording_verified=True`, `checkpoint_execution_verified=True`, `music_success=False`, `stability_success=False`를 구분하는 것은 원자료와 일치한다. 최종 inventory와 봉인은 이 독립 검수 완료 후 root가 수행한다.
