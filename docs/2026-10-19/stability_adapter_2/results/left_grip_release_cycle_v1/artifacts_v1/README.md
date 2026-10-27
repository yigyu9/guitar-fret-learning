# 왼손 넥 그립·이동·해제 안정성 진단

## 관찰 결과

Isaac Gym에서 왼손으로 넥 위치 A를 잡고 놓은 뒤, 넥 축을 따라 B로 이동해 다시 잡고 놓는 16초 진단을 두 번 실행했다. V2는 3,840 physics step, 481개 프레임으로 정상 완료됐다. 분석 기록에서 입력 변경과 금지 호출은 없었고, 지정된 target rate·model limit·effort cap 불변조건도 모두 통과했다.

A 유지(3.0–4.5초)와 B 유지(10.0–11.5초)는 각각 360/360 표본에서 엄지와 다른 손가락의 양의 접촉 lambda가 함께 관측됐다. A 해제 후 손을 연 구간(6–7초)은 240/240, B 해제 후 열린 구간(13–16초)은 720/720 표본에서 왼손 기타 접촉이 없었다. 오른쪽 위팔과 오른쪽 엉덩이의 지지 접촉은 2초 준비 이후 기록된 endpoint마다 존재했다. 그러므로 관측된 자세 유지에는 유한한 인간 지지 접촉이 함께 작용한다.

실제 손목의 A–B 평균 위치 차이를 현재 기타 넥 축에 투영한 값은 36.727 mm였다. 요청한 40 mm보다 3.273 mm 짧다. 같은 표본의 전체 손목 위치 범위는 44.168 mm다. 이 값은 목표 명령 이동량이 아니라 측정된 손목 위치 차이다.

2초 준비 종료 상태를 기준으로 한 신체 중심의 최대 편차와 SO(3) 최대 회전은 각각 22.264 mm와 9.796°였다. 초기 상태부터 준비와 사이클을 모두 포함하면 최대 편차는 41.255 mm, 회전은 10.455°였다. B 해제 구간(11.5–13초)에는 시작 대비 최대 12.885 mm와 5.275° 변화가 있었다. 이후 열린 B 구간(13–16초)의 13초 기준 최대 변화는 0.0187 mm와 0.00662°였다. A 열린 구간(6–7초)은 구간 시작 대비 최대 0.415 mm와 0.136°였다.

## 실제 장면

아래는 native V2 캡처의 원본 프레임을 바이트 변경 없이 복사한 것이다. 각 쌍은 같은 시각의 전신 및 손 카메라 장면이다. 캡처는 30 fps이며, 시간은 명령된 단계가 아니라 시뮬레이션에서 관측된 시각이다.

### A 유지 중 · 3.5초 (frame 00105)

![A 유지 중 전신 native frame, 3.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/whole_body_00105.png)

![A 유지 중 손 native frame, 3.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/hands_00105.png)

### A 해제 후 손을 연 상태 · 6.5초 (frame 00195)

![A 해제 후 전신 native frame, 6.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/whole_body_00195.png)

![A 해제 후 손 native frame, 6.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/hands_00195.png)

### B 유지 중 · 10.5초 (frame 00315)

![B 유지 중 전신 native frame, 10.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/whole_body_00315.png)

![B 유지 중 손 native frame, 10.5 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/hands_00315.png)

### B 해제 후 손을 연 상태 · 14초 (frame 00420)

![B 해제 후 전신 native frame, 14 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/whole_body_00420.png)

![B 해제 후 손 native frame, 14 s](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/native_v2/hands_00420.png)

## 단계 및 접촉 요약

| 실제 시각 | 단계 | 왼손 기타 접촉 관측 | 신체/기타 측정 |
|---|---|---|---|
| 0–2 s | 준비 | 목표 접촉을 보장하지 않는 초기 준비 | 준비 종료 기준으로 이후 신체 편차 산정 |
| 2–3 s | A 닫기 | 접근·접촉 전환 | 단계 중 혼합 접촉 표본 |
| 3–4.5 s | A 유지 | 엄지+다른 손가락 양의 접촉 lambda 360/360 | 신체 단계 최대 변화 1.064 mm / 1.031° |
| 4.5–6 s | A 해제 전이 | 접촉이 점차 사라짐 | 단계 내 왼손 접촉 해제 표본 포함 |
| 6–7 s | A 열린 상태 | 왼손 기타 접촉 없음 240/240 | 최대 0.415 mm / 0.136° |
| 7–8.5 s | 열린 손으로 B 이동 | 왼손 기타 접촉 없음 360/360 | 구간 끝 손목 목표 위치로 이동 |
| 8.5–10 s | B 닫기 | 접근·접촉 전환 | 단계 중 혼합 접촉 표본 |
| 10–11.5 s | B 유지 | 엄지+다른 손가락 양의 접촉 lambda 360/360 | 신체 단계 최대 변화 1.773 mm / 0.640° |
| 11.5–13 s | B 해제 전이 | 접촉이 점차 사라짐 | 최대 12.885 mm / 5.275° |
| 13–16 s | B 열린 상태 | 왼손 기타 접촉 없음 720/720 | 13초 기준 최대 0.0187 mm / 0.00662° |

SO(3) 회전값은 원 분석의 회전거리 정의에 따른 값이다. A/B 위치 간 36.727 mm는 현재 neck axis에 투영한 평균 손목 변위이며, 전체 손목 위치 범위 44.168 mm와는 다른 측정량이다.

## 반복성과 조건

V1과 V2는 같은 초기 상태였고, 반복 비교 기록은 전체 기타 root trace와 quaternion 성분이 두 실행에서 정확히 같다고 보고한다(최대 차이 각각 0). 이는 동일 조건에서의 두 번의 결정론적 진단 재현이다. 무작위 초기조건을 통한 강건성 평가는 아니다.

기타는 자유 동역학 상태였으며 고정, 손 부착, 매 프레임 pose 덮어쓰기, strap 사용은 없었다. root/lower-body 고정은 사용하지 않았고 self-collision은 켰으며 right strike는 껐다. 오른쪽 위팔과 엉덩이 지지 접촉은 계속 관측됐다. 따라서 결과는 완전한 무지지 균형이나 수동 평형, force closure를 보여주지 않는다.

V2의 접촉 분류는 왼손 접촉에서 고정된 왼쪽 엉덩이의 오분류를 제외하도록 수정됐다. V1에는 실행 전 설정 해시 누락과 raw LHip 분류/증거 범위 문제가 있었다. 따라서 V1 원자료는 그대로 보존하지만, V2 수정 결과를 V1에 소급 적용하거나 V1을 독립적으로 완전 인증된 기록이라고 해석하지 않는다.

이 진단은 넥 위치를 짚고 해제하는 특정 조건의 결과다. 자연스러운 연주, 전 곡 수행, 여러 초기조건에서의 강건성, 수동 안정성, 접촉 force closure를 입증하지 않는다.

## 자료와 영상

- [V2 전신 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/whole_body.mp4>) · [V2 손 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/hands.mp4>) · [엄지 뒤쪽 시점](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/thumb_back.mp4>)
- [V2 raw report](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/native_v2/report.json>) · [V2 분석](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/analysis_v2.json>) · [반복 비교](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/repeat_comparison_v1.json>)
- [V2 초기 native 장면](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/native_v2/media/initial_native.png>) · [초기 줄 표시 장면](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/native_v2/media/initial_strings.png>) · [초기 지지 측면 장면](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/native_v2/media/initial_support_side.png>)
- [V1 원 분석](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/analysis_v1.json>) · [V1 증거 범위 정정 기록](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/v1_evidence_scope_correction.json>)
- [V2 복사 SHA 검증 기록](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/copy_manifest_v2.json>) · [V2 작성 전 입력 SHA 기록](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/artifact_before_v2.json>) · [V1 복사 SHA 검증 기록](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/copy_manifest_v1.json>)
