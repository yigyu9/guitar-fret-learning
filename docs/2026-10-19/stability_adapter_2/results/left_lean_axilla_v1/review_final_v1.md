# 왼쪽 몸통 기울임·상완 접근 — 최종 독립 검수

요약 판정: **문제없음.** Critical 0 / Warning 1 / Suggestion 0. 기록·명령·문서 검수 승인이고 **겨드랑이 지지 또는 자유 기타 유지 성공의 승인이 아니다.** 새 물리 실행·학습·기존 파일 수정은 하지 않았다.

## 결과와 제어

저장 trace의 초기 대비 actor-root 이동·SO3와240Hz endpoint 접촉을 직접 대조해 [강화 분석2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v2/verification.json:1), [조합 분석3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v3/verification.json:1), [두 점 분석4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v4/verification.json:1)와 일치함을 확인했다.

| 완료 조건 | 바디 BB 중심 / root 이동 | 초기 대비 SO3 | 상완 / 전완 / Head / left 존재 표본 |
|---|---:|---:|---:|
| 몸통만 왼쪽4° | 187.876 / 258.387mm | 73.904° | 0 / 173 / 782 / 0 of 1200 |
| 왼쪽4°+팔·기타 초기 보정 | 205.134 / 323.030mm | 50.178° | 0 / 346 / 0 / 0 of 1200 |
| 같은 조합+상완 motor 점 추가 | 203.862 / 319.918mm | 49.689° | 0 / 351 / 847 / 0 of 1200 |

세 시험 모두5초·1200 physics/300 control을 완료했다. `passed`는 기록·명령 검사 통과이며 안정화 성공이 아니다. 상완 접촉은 모두0으로 source 근접이 실제 접촉 지지를 보장하지 않았다. 두 Head 접촉 조건은 거절하고, Head0인 조합도 큰 이탈로 유지 실패다. body BB 중심은 source bbox 기준이며 COM/root와 구분한다. raw lambda와 접촉 존재 수는 N 힘·지지 비중이 아니다. 후기 정착은 초기 자세 유지 성공을 뜻하지 않는다.

조합 기준과 상완점 추가의 initial JSON은 전체 exact였다. 두 점의 요청 합산·model clip을1200행 직접 재계산해 최대 요청 차이3.55e−15Nm, 실제 actor effort 호출1200회를 확인했다. right12 EFFORT에만 합산하고 other69 effort0/새 POSITION 목표·owner window/상태 불변/Jacobian gate를 유지한다. 직접 기타 외력·부착·pose 덮어쓰기는 추가하지 않는다. 실제 shape filter256/4096의 AND0과 약0.1mm contact offset은 확인했지만, 이것만으로 cooked 형상·접촉 정상성 전체를 인증하지 않는다.

[최종 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/README.md:39)은 기준도 능동 전완 제어임을 명시해 이전 ‘수동 대 능동’ 표현 Warning을 해소했다. 상완 점은 인간 기준점 요청이며 측정 접촉점/힘이 아니다. 점별30N 상한은 합계30N 상한이 아니며 전체 중력보상·Jacobian·각 접촉의 힘/모멘트 기여는 미인증이다. 초기 팔 scalar 보존과 팔 world pose 보존도 구분한다.

## 그림·표기·보존

PNG5개를 실제로 열어 확인했다. 최신 초기4조건/시간3조건 그림과 source 간격 그래프는 원자료 수치·실패 해석과 일치한다. 카메라/초기 기타 위치가 다른 초기 비교는 정성 참고로 한정한다. [README_V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V2.md:20)는 전체 세 조건을 유지·연주 성공으로 판정하지 않는다.

[영상 INDEX_V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V3.md:3)는 native1을 **몸통4°·기타 초기 p/q 유지**로 정정한다. manifest V2→V3는 native1 두 영상의 label만 바뀌고 경로/SHA/메타는 유지한다. 영상6개의 source/copy SHA가 exact이며151프레임·30fps 기록을 확인했다. 물리5.0초와 MP4 5.033초를 구분한다. 과거 INDEX/manifest는 역사 자료로 보존한다.

현재 phase source/native/analysis 입력9,993개 기록은 이전·현재 [navigation 스냅샷](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/navigation_update_v1.json:1) 예외를 적용해 불일치0이었다. 세 main append의 before/after SHA·prefix·직전 phase 연결을 직접 확인했다. artifact provenance3종 입력·출력 SHA 및 현재 문서/색인의 파일·행 링크도 일치했다.

[seal_outputs_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/seal_outputs_v1.py:16)의 historical/current nav 예외, dict/list provenance 처리, 리뷰 gate, 배타적 출력 논리 및 Python3.8 구문에 중요한 오류를 발견하지 않았다. 실제 봉인 실행과 이전 phase1392/old7255/archive86 전체 재검사는 root 후속 범위다. 예정 source_final/inventory/final_verification을 완료된 감사로 주장하지 않는다.

## Warning

1. [source_gap_comparison.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)의 `Upper arm at 65%`는 **근위0~65% 구간의 최소 gap**이다. [measure의 구간 제한](/home/ajou/yigyu/3/stability_adapter_2/om_axilla_source_geometry_v3.py:37)으로 계산한 값이며65% 단일 지점의 간격으로 확대하면 안 된다. 본문 ‘근위65%’ 설명은 맞으며 소비된 PNG는 보존한다. 후속 표기는 구간 최소값임을 명시하는 것이 좋다.

방향은 이번에 실행한 **player-left=넥 쪽=정면 화면 오른쪽**으로 제한한다. 대기 중인 방향 확인의 답변이나 반대 방향 채택을 추정하지 않는다. 이번 초기 접근 결과를 최종 연주 자세나 학습의 유지 성공 초기값으로 등록할 근거는 없다.

검수 SHA256:

- root README: `0bcdb0e35ecca3f5632e33d212eec1e56dc9bb687a842c297a3708f854e14d61`
- artifact README_V2: `ffb403214dc04527425332a0bf0509a299d59cd8ef78c7469777a9df042a28aa`
- 영상 manifest V3: `bdb800ee218bc81195ba747557ba5483325c16f91c52a1b1dc8fb1736416ac97`
- 봉인 스크립트: `b58050c01d31d6ef2420a87ffc1ea86205f2d5ed993026407683937369555c29`

이 새 리뷰 파일만 작성했다.
