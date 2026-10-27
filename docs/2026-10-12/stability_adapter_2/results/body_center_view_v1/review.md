# 바디 중심 표시 독립 검수

검수자는 이 review만 작성했으며 코드·계획·입력·다른 담당자 파일을 수정하지 않았다. 이번 대상은 `body_center_coordinates.py`, `build_body_center_view.py`, `BODY_CENTER_VIEW_PLAN.md` 및 결과다. **최종 판정: 문제없음.**

## 사전 판정

**문제없음. Critical·Warning 없음.** 실행을 막는 오류를 발견하지 않았으며 아래 결과 검수에서 이미지·표·보존 검증도 확인했다.

- [helper:7](/home/ajou/yigyu/3/stability_adapter_2/body_center_coordinates.py:7), [helper:12](/home/ajou/yigyu/3/stability_adapter_2/body_center_coordinates.py:12): 동일 q에서 표시 바디 중심 `p_root+R(q)c`와 역변환 `p_center−R(q)c`가 정확한 수식이며 하나의 점/8꼭짓점 모두 지원한다. c는 기존 `[0,−0.4,−0.0217]m` 표시 기준점 가정이고 질량 CoM이 아니다.
- [helper:17](/home/ajou/yigyu/3/stability_adapter_2/body_center_coordinates.py:17): 회전한 Pelvis right=local−X, forward=local−Y, up=local+Z의 basis에 row vector를 `basis.T`로 곱하여 RFU로 역변환한다.
- [producer:16](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:16): identity/Z90 analytic 값, 256개 회전 roundtrip 및 q/−q 검사를 포함한다. [producer:84](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:84)의 Pelvis는 이전 native body-name 색인으로 조회한다. [producer:87](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:87)는 실제 저장 q에서 중심/8꼭짓점/native saved 값을 대조하고 RFU 축별 최소·최대를 저장한다. 모든 회전의 공통 box라고 주장하지 않는다.
- [producer:27](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:27): 이전 raw native 장면/view/projection/depth로 설명 선·marker만 새로 그리며 기타 원점 marker를 제거한다. 최종 caption 폭 검사도 포함한다. 새 Gym 초기화·simulate·policy·학습 호출이 없고 helper는 기존 runner에 연결되지 않았다.
- [계획:3](/home/ajou/yigyu/3/stability_adapter_2/BODY_CENTER_VIEW_PLAN.md:3): 표시 좌표 변경과 기존 actor-root/회전 범위·제어의 보존을 구별하며 실제 질량 중심·동적 접촉·전체 6축 안전영역 인증을 주장하지 않는다.

## 이전 inventory 관련 사실

[prior_inventory_note.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/prior_inventory_note.json:1)은 이번 시작 전에 이전 phase의 `review.md` 한 파일이 그 inventory SHA와 달랐음을 명시한다. 이번 producer는 이전의 실제 소비 geometry/report/raw/depth 파일을 이전 inventory SHA와 대조하고, 전체 이전 파일은 이번 시작 baseline SHA로 별도 보호한다. 기존 inventory를 수정해 이 이력을 감추거나 모든 과거 inventory가 일치한다고 주장하지 않는다.

## 결과 검수

**구현·좌표·원자료·이미지·최종 문서 판정: 문제없음.** 검수자는 새 Gym 또는 physics를 실행하지 않고 저장 결과를 대조했다.

- 세 조건의 정면/측면 **6PNG를 모두 실제 열람**했다. 기타 원점 marker를 제외하고 분홍 바디 중심, 하늘색 조건부 사용자 box, 노랑 팀원 box, 초록 넥 방향만 표시한다. 실제 RFU값·두 범위·고정 회전 한계와 후처리 출처가 읽히고 footer 잘림을 발견하지 않았다. 각 결과 크기는 **1280×910**이다.
- summary/attempt 실제 manifest는 **30입력**이며 그 SHA 및 현재 원문 SHA가 exact 동일하다. 소비된 raw/depth/geometry/report와 이전 native 상태를 새 물리 없이 사용한다. 새 Gym 초기화/physics step/학습은 모두0이다.
- [summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/summary.json:1)의 analytic identity/Z90·256회전 roundtrip/q·−q·saved 중심/꼭짓점·입력 보존 검사 pass를 확인했다. 실제 native p/q에서 바디 중심과8꼭짓점을 별도로 재계산한 값이 summary와 일치한다. [CSV](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/body_center_ranges.csv:1)의3행 모든 수치도 JSON과 일치한다.
- 현재 수평의 실제 중심 RFU는 약 **(16.9585,24.5012,10.8973)cm**, 조건부 사용자 표시 범위는 오른쪽 **−10..25cm**, 앞 **0.83..30.83cm**, 위 **5.80..29.17cm**다. 보고 기준·중앙의 위치/회전으로 바꾸면 같은 actor-root box라도 중심 RFU 범위가 달라진다. 모든 q에 공통인 새 고정 허용 box가 아니라는 설명에 부합한다.
- 보호 current-baseline **44파일** SHA가 그대로다. 이전 inventory의 현재 불일치에는 이미 기록된 review와 이번에 append한 PLAN이 나타난다. 이번 before/PLAN SHA는 이전 inventory와 일치하므로 PLAN의 차이는 승인된 새 기록이고, 사전 review1파일 불일치 note와 모순되지 않는다. 이전 review/봉인을 수정하지 않았다.

## 최종 문서·보존 확인

최종 README의 표·6이미지 출처·RFU 단위·폭과 실제 위치가 CSV/JSON에 부합한다. 표시 기준점과 질량 CoM, body-center 표시와 기존 actor-root 제어, 각 q의 조건부 box와 전체 허용 영역, 저장 native 후처리와 새 초기화를 명확히 구분한다. 이전 inventory/review 시점 불일치도 기록한다. FILE_INDEX의 source/helper/producer·계획·누적 기록 위치를 확인했으며 두 최종 문서의 **42개 절대경로 링크·실제 줄**이 존재하는 파일과 범위에 맞는다.

새 main PLAN/D README/D VISUAL_REPORT의 append 본문도 같은 수치·가정·후처리 범위를 설명한다. before PLAN **634줄**, D README **561줄**, D VISUAL_REPORT **2297줄**의 본문 전체가 새 파일의 exact prefix로 보존됐다. source_final helper/producer/세부계획 **3파일**은 현재 소비 원문과 exact 동일하다.

[최종 root 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/final_verification.json:1)은 실제 존재하며 status=pass다. 입력30개/보호44파일/6PNG/3표행/256회전 검사와 새 native·physics·학습0 수치가 독립 대조 결과에 맞는다. 기존 actor-root/회전 범위와 제어는 보존됐으며 helper를 runner에 연결한 구현이라고 주장하지 않는다.

**최종 검수 완료. 미해결 Critical·Warning 없음.** 이후 main 체크 완료 기록과 inventory 생성·봉인은 root가 담당한다. 이 review는 지금 먼저 닫으며 새 inventory·봉인 이후 추가 수정하지 않는다.
