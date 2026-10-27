# 위 볼록부·근위 상완 접근 최종 검수

판정: **문제없음 — 완료 자료와 제한된 진단 결과의 정리 승인.** 미결 Critical 0 / Warning 2 / Suggestion 0. 근위 상완·지정 볼록부 접촉 및 초기 기타 자세 유지 성공은 인증하지 않는다. 읽기 전용 원자료/코드/그림 대조와 CPU 수식 재계산만 수행했으며 새 native·학습은 실행하지 않았다.

## 확인한 결과와 산출물

- [native 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/review_native_v1.md:1)의 명령 합산·모델 clip·POSITION69/state·입력 SHA·초기값 비교를 최종 설명과 대조했다. 세 조건 5초/1200 physics/300 control, native2/3 전체 초기 state exact, 기타 초기 state 세 조건 exact이다. source4/5 거절값은 native에 사용하지 않았다.
- [최신 결과 설명:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/README.md:15)과 [canonical 산출물 설명:7](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/README_V2.md:7)은 강한 두 조건의 큰 회전·Head 접촉과 약한 조건의 한계를 정확히 구분한다. 약한 조건 BB 중심 59.465mm/SO3 53.935°/목 G+Y 고도 −13.709°이며, 2→5초 0.132568mm/0.066829° 정착은 초기 유지 성공이 아니다. BB 중심과 root·질량중심도 구분한다. 전체 상완 1075/1200이어도 요청한 근위 0~35%·볼록부 지역은 0/1200이다.
- [baseline probe:11](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/probe_baseline_source_v1.py:11)의 입력 SHA와 계산을 직접 대조하여 근위 **0~35% 구간 최소** source 간격 14.150128mm를 재현했다. 단일 35% 점의 간격이나 cooked/native 간격으로 확대하지 않는다.
- [native 시간 비교 그림](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png)과 [기준점/접촉 feature 그림](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)을 실제 열어 확인했다. 0/2/5초의 기타 자세 변화와 레이아웃이 설명에 맞으며, 노란 인간 motor 기준점과 파란 step1200 양의 raw lambda contact feature를 구분한다. 원자료·카메라 투영 재계산과 표시가 일치한다. 33.764275mm는 두 점의 3D 거리이며 표면 gap·depth-tested 표시가 아니다.
- 산출물 provenance1 입력45/출력12 및 provenance2 입력14/출력1·producer 해시가 현재 파일과 일치한다. README_V1의 source_v5 출처 오해는 기존 자료를 보존한 README_V2에서 정정됐다. [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/manifest_v1.json:1)의 6개 source/copy SHA 일치와 151프레임/30fps 기록을 확인했다. MP4 5.033333초와 물리 5초를 구분한다. 영상 전체 decode 인증은 수행하지 않았다.
- [main 추가 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/navigation_update_v1.json:1)의 snapshot SHA·현재 after SHA·원문 prefix와 실제 추가 행 PLAN1135/A README2230/D README63이 일치한다. canonical 문서·색인 69개 링크의 존재/유효 행을 확인했다. 과거 전체 inventory 재검사는 root 봉인 범위다.

## 발견과 보완

해결된 검수 발견 1건 — 기존 미실행 seal v2는 최신 provenance의 `outputs`/`producer`를 읽지 않아 canonical README·정정 생성기 SHA를 빠뜨렸다. [새 seal v3:47](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/seal_outputs_v3.py:47)의 `outputs`/`producer`/`inputs_after` 검사로 해결됐고 해당 실제 자료 SHA를 독립 대조했다. 문법 및 review 존재→exclusive 최종 파일 생성 순서도 확인했다. reviewer는 봉인 스크립트를 실행하지 않았으며 최종 source/inventory/verification 생성은 root 작업이다.

Warning 1 — [제어 비교 설명:25](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/README.md:25): 전완 방향·상완 목표 거리·요청힘 상한이 함께 바뀐 비교다. 개별 원인이나 힘/모멘트 기여를 분리하지 않는다. 요청힘·raw lambda는 측정 접촉힘이 아니며 관측 래치는 노력 중단을 뜻하지 않는다. 현재 설명에 반영됨.

Warning 2 — [지역 해석:33](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/README.md:33): 캡슐 구간·Gx/Gy 분류는 해부학적 겨드랑이·전체 solver 연속시간·추가 mid-depth Gz 인증이 아니다. 모델 기준의 현재 world 위 볼록부와 일반 해부학적 upper bout도 구분한다. 후기 정착이나 상완 전체 접촉을 연주·안정 초기 자세 채택으로 확대하지 않는다. 현재 설명에 반영됨.

검수 핵심 SHA256: root README `e8cca2168e8f0c98c76027a569c1d0f5c8db981d9b72896722e516dcac775075`; canonical README_V2 `f1fa7a91756ab78fef6c55842a4267ba02cdfeedb08ff9f20558c2b4ad488011`; seal v3 `834c068d683672aa8c084362f4d90beaf9a24dd3fdb9d8a00f91c700ef1e70db`. 잔여 수정 요청 없음.
