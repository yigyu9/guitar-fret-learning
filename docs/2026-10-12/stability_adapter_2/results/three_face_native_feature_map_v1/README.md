# 세 면 지지 feature map · 저장 자료 시각화

기존 기준·half slack·zero slack 세 실행의 저장된 contact/pose 자료 15,511행을 재표현했다. 이번 단계는 분석 결과의 그림화이며 native 초기화 0회, 새 물리 실행 0회다. 점의 색은 손 body를 나타내며 neck face 분류를 뜻하지 않는다.

## 조건과 원자료

| 조건 | 저장 실행 | 접촉 기록 | 저장 결과 |
|---|---|---:|---|
| 기준 | [saved_finger_targets](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/report.json>) | 4,346 mapped rows | 초기값과 기록을 재사용 |
| half slack | [half_slack](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/report.json>) | 5,556 mapped rows | 초기값과 기록을 재사용 |
| zero slack | [zero_slack](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/report.json>) | 5,609 mapped rows | 초기값과 기록을 재사용 |

분석 입력은 [analysis_v2.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/analysis_v2.json>)이며 SHA-256은 `028e95df7aca0cc4618cf8137bf5c6ed1fb1e77844305a7c83bffba288923959`다. 승인 brief는 [artifact_brief.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/artifact_brief.json>)이다.

## 관찰

- 세 실행의 post-step body-origin feature pair 최대 잔차는 기준/half/zero 순서로 0.00004974 / 0.00006753 / 0.00005328 mm다. 이는 깊이 또는 연속 접촉 인증이 아니다.
- palm의 finite desired-patch 거리는 각각 21.105–22.783 / 24.390–29.806 / 25.996–28.382 mm이며 palm desired patch 내부 표본은 모두 0이다. 실제 palm 접촉점은 넥 전면과 옆면의 가장자리 부근에 있으며 지정 옆면 영역과 떨어져 있다.
- thumb의 G x는 약 −23 mm, rear z는 −9.01…−7.62 mm다. 지정 rear patch 내부 표본은 기준 41, half 10, zero 2건이며 경계 분류다. rear interior 지지로 분류하지 않는다.
- index/middle 접촉은 주로 fret 4/5 부근이다. 이는 기하 proxy와의 호환성 관찰이며 해부학적 누름이나 힘 지지를 입증하지 않는다. 약지/소지와 기타 사이의 접촉 행은 없다.
- 현재 세 면 grip은 달성되지 않았다. 다음 변경 후보는 gain을 유지한 채 contact-point/facet footprint 중심을 조정하는 것이다. 다음 미실행 leaf plan은 [contact footprint 재설계 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md:1)이다. 이 phase에서 추가 trial은 없다.

## 그림

![feature_map.png](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/feature_map.png>)

위 그림은 XY/YZ feature 점과 유한 patch 및 source mesh/fret proxy를 분리해 표시한다. front skin 9.3 mm와 outer 11.230006 mm를 구분한다.

![patch_distance.png](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/patch_distance.png>)

위 그림은 양의 raw λ 행의 finite desired-patch 거리만 점으로 표시하며 결측 구간을 연결하지 않는다.

![native_hands.png](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/native_hands.png>)

위 그림은 저장된 Isaac Gym camera frame 0, 0.5, 5초를 조건별로 배열한다. 새 render가 아니다.

재사용한 5초 전체 영상:

![기준 저장 실행 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4)

![half slack 저장 실행 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/whole_body.mp4)

![zero slack 저장 실행 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/whole_body.mp4)

## 재현

`python /home/ajou/yigyu/3/stability_adapter_2/make_three_face_feature_artifacts.py --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1`

producer는 저장된 JSON/PNG만 읽고 승인 analysis SHA, 원 입력 SHA 전후 일치, 선택 native frame capture SHA를 확인한다. 분석과 원자료, 기존 source producer는 수정하지 않는다.

## 실행·검증 상태

Canonical 분석v2는19.319517초, 그림producer는9.619365초에exit0으로완료했고새native/physics0이다. 초기v1분석과소스·wrapper·입력·로그·metadata는 [normal_gate_v1 보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/normal_gate_v1/preservation.json)에exact봉인했다.

그림의상단은 Gx(가로)/Gy(세로), 하단은 Gy(가로)/Gz(세로)이며전부mm다. 회색선은source형상이고원본mesh전체표면이실제cooked접촉면과같다고보장하지않는다. SDK 문서방향normal과반대방향dot은분리기록했고면분류gate로사용하지않는다. Source에설정된substeps=1과nativeSimParams미조회는구분한다. COM도native조회로확정하지않았다.

root가실제PNG3개·선택frameSHA·입력전후SHA·수치와문서를대조했다. 별도change-reviewer는v1좌표/유한polygon수학을검수했으나, canonicalv2/그림의최종독립검수재호출은도구의 `agent thread limit reached` 오류로진행되지못했다. [검수범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/review_status.json)에부분검수와미검수범위를남긴다. 독립최종검수완료나안정화성공으로표시하지않는다.
