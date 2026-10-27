# 저장된 전체 Fret 실행 진단

## 결과

이 진단은 완료·보존된 실제 Isaac Gym 실행 [`fret_fingers_arm_hold_v1`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data>)의 389개 저장 프레임, 3100 physics step, 물리 경과 12.916667초를 후처리했다. 후처리 중 새 physics 실행·제어 변경은 없었다. 원본 조건은 준비 2초, 왼팔 9관절의 준비 마지막 목표 유지, 손가락 21관절 Fret 정책, 스트랩 OFF다.

별도의 fresh live 진단 v1, 동일 재시험, v2는 각각 0.866667초, 0.833333초, 1.0초의 마지막 완료 프레임 뒤 native camera API 오류로 중단됐다. 세 건 모두 전체 live 진단 미완료이며 부분 영상은 보존했다. 이를 이번 전체 영상이나 성공 실행으로 간주하지 않는다.

원본 task는 `index finger_back`에서 실패했고 `episode_success=false`, `goal_finished=false`, 지속 성공 0/27이다. 저장된 손목 목표 벡터 범위는 155.197–221.632 mm, 초기 대비 최대 회전 변화는 50.248°다. 조건부 body-center 위치 box에서 벗어난 표본은 389개 중 53개이며, 최대 초과량은 15.005 mm로 2.7초 world Z 하한 방향이다. 위치 box는 현재 자세의 조건부 영역이며 질량중심 기준이 아니다. 전체 회전 집합 판정은 하지 않았다.

2초 약지 목표 marker 거리는 87.617 mm, 손목 목표 벡터는 155.197 mm다. 8초 약지 marker 거리는 46.732 mm지만 다른 목표다. 따라서 같은 task에서 목표 오차가 개선됐다는 비교로 해석하지 않는다. 준비 목표와 마지막 접촉은 측정되지 않았다.

2초 handoff pose를 기준으로 8초 실제 손목 원점의 world 이동은 18.355 mm였고, 기타 root 이동은 44.393 mm·회전 변화는 47.906°였다. 손목의 기타 local 위치 변화는 59.372 mm다. 이는 강체 상대 위치 변화이며 접촉 마찰에 의한 미끄럼 길이가 아니다. 손목 원점은 표면 접촉점이 아니다. 이 이동량은 위의 현재 목표까지의 손목 벡터 오차와 별도 값이며, 결과는 기타 회전에 따른 손-기타 상대 위치 변화와 목표 접근 부족을 각각 보여준다.

## 시점과 측정 한계

2.000초 이미지의 `PREPARE` 표시는 원본 camera/trace가 handoff 직전 capture였음을 나타낸다. 이미지의 pose는 physics step 480이다. 표시된 목표 packet은 handoff 후 첫 checkpoint의 pre-integration 관측(frame 0)에서 가져왔고, 같은 physics step 480의 pose와 정렬됨을 확인했다. 그러므로 화면 phase 표기와 목표 packet 시점은 구분해서 읽어야 한다. PLAY 표본은 각 physics step의 다음 제어 직전 저장 관측으로, 직전 물리 평가와 goal advance 뒤의 목표를 쓴다. 마지막 표본은 저장된 terminal observation이다.

손끝 marker와 저장 native 손끝의 최대 정렬 오차는 1 µm 미만이다. 카메라 source SHA와 정적 matrix, 초기/공통 prefix 31 frame × 2 view의 raw pixel exact, 입력 SHA 불변 등 후처리 검사 10개가 통과했다. 기존 원본에는 camera matrix/depth가 없어 v2의 동일 초기상태·고정 camera matrix를 사용했다. 선은 투시 설명선이며 가려짐 판정은 없다. 초록 접촉 표시는 body 원점이다. 표면 접촉점·관통 깊이를 나타내지 않는다. 접촉 raw lambda는 힘(N)이 아니며 pluck-range proxy는 실제 접촉에서 제외했다.

MP4는 389 frame을 30 fps로 인코딩해 길이는 12.966667초다. 이는 physics 경과 12.916667초와 다르다. 마지막 stop은 원본 task 실패이며 평형 상태나 영상 정지가 아니다.

## 대표 프레임과 추세

2초 양손 확대. PREPARE 표기와 handoff 후 목표 packet의 시점 차이에 관한 설명은 위 항목을 참조한다.

![2초 양손·현재 프렛 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/frames/hands/00060.png)

8초 양손 확대. 목표가 2초와 다르므로 marker 거리의 직접 개선 비교가 아니다.

![8초 양손·현재 프렛 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/frames/hands/00240.png)

저장 프레임 전체 구간의 body-center 위치·회전·손목 목표 거리 추세.

![저장 전체 구간 진단 추세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/timeline.png)

## 전체 영상

전신 view:

![시작부터 원본 task 종료까지 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/whole_body.mp4)

양손 확대 view:

![시작부터 원본 task 종료까지 양손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/hands.mp4)

## 다음 단계

native camera 반복 조회 오류를 해결한 뒤, 현재 기타 기준 왼팔 9관절 손목/Fret 목표 보정 OFF/ON을 비교한다. 원본 손가락 21관절 정책의 제어권을 유지하고, 손바닥 지속 접촉은 강제하지 않는다. 목표 비교는 서로 다른 기타 상태와 목표를 섞지 않으며 원본 실패 판정을 유지한다.

## 근거 파일

- 저장 입력과 분석 결과: [`analysis/summary.json`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/summary.json>), [`analysis/capture.json`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/capture.json>), [`analysis/metrics.csv`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/metrics.csv>), [`interpretation.json`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/interpretation.json>).
- 손목·기타 상대 이동 수치: [`relative_wrist_motion.json`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/relative_wrist_motion.json>).
- 계획과 실행 기록: [`SAVED_FRET_DIAGNOSTIC_PLAN.md`](</home/ajou/yigyu/3/stability_adapter_2/SAVED_FRET_DIAGNOSTIC_PLAN.md:1>), [메인 계획 기록](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:667>), [시각 보고서](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2313>).
- 독립 결과 검수는 완료됐다: [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/review.md>). 최종 보존 산출물 `final_verification.json`, `source_final/`, `artifact_inventory.json`은 별도 담당의 예정 경로다.
