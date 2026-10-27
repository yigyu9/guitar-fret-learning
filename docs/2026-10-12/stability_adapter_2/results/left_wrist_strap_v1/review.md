# 새 왼손목 자세의 초기 스트랩 길이 — 독립 통합 검수

검수일: 2026-10-07 KST. 별도 change-reviewer가 이번 입력·저장 실행·문서·미디어를 검수했다.
쓰기 범위는 이 파일뿐이며 코드·원자료·이전 동결 검수 기록을 수정하지 않았다.
새 native simulation, 초기 환경 생성 또는 source geometry query를 실행하지 않았다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 초기 계약과 참조 자료

- [계획의 입력 범위](/home/ajou/yigyu/3/stability_adapter_2/LEFT_WRIST_STRAP_COMPARE.md:5)대로 새 왼손목 기준 full pose에서 절대 LA만 바꾼 3개 설정을 대조했다. 초기 route 1.1010801317960974 m와 LA=route−T/6000에 따라 0/1/2 N 길이가 정확히 생성됐다. 초기 법칙 힘은 부동소수 오차를 포함해 각 0/1/2 N과 일치한다.
- 세 입력의 다른 설정, 전체 105개 초기 q, humanoid/guitar 전체 초기 native state, 기타 목표 p/q, PD·cap·solver·route가 같다. native q는 초기 목표와 같고 초기 DOF 속도는 0이다. 저장 C02 q와 native model bounds에 대조해 기존 C02±0.3/model 교집합을 유지함을 확인했다.
- fresh audit의 61개 source SHA와 계약 검사가 현재 자료와 맞다. 세 조건의 geometry/hand 기록이 같고 source 음수 pair 0, LH 위쪽 반구·국소 높이·projection 조건을 통과한다. source query와 palm-up proxy는 cooked clearance·지지력·검증된 해부학적 법선 인증이 아니다.
- compatibility symlink 3개는 이름이 `wrist_minus0050`이지만 실제 새 `left_palm_boundary_v1/l_wrist_x_minus0125` 원본으로 해석된다. 각 기간의 0 N raw5는 그 원본과 정확히 같다. 이전 다른 왼손목 pose의 결과를 비교 기준으로 사용하지 않는다.
- audit_strap/comparer_strap은 지정한 small_preload frozen 사본, runner/PI/generic plotter는 직전 frozen 사본과 byte가 같다. 새 controller·gain·gate·model 변경은 없다.

## 저장 실행 독립 검증

- 9개 ON run, 1,152 physics samples와 PI update 288회를 확인했다. PI 구현을 호출하지 않고 e=q_ref−q, 적분·최종 clipping·조건부 rollback을 재계산해 error/integral/raw/applied/blocked/saturated 여섯 저장 벡터와 정확히 일치시켰다. 60Hz update 사이 기록은 유지되고 native float32 최종 목표는 허용 오차 안에서 같다.
- 팔24 PI ±0.15 rad cap·최종 C02/model target box·240Hz/60Hz 스케줄이 유지된다. 주요 66 연결에서 손가락42·몸통9·C02 하체는 PD 목표를 유지하며 실제 상태 고정이 아니다. runner의 비팔 목표 유지와 state-write 없는 target 적용 검사도 통과했다.
- 모든 저장 humanoid root state가 초기와 같다. 기타 위치와 선·각속도를 native body state와 대조하고 위치 목표 오차·quaternion geodesic 회전 오차를 재계산했다. 기타는 자유이며 기존 +5mm 목표와 초기 quaternion을 유지한다.
- 매 tick 적용 tension을 직전 route 위치·속도의 원본 k=6000/c=120/최대300 N slack 법칙에서 별도 계산해 일치시켰다. 각 run의 절대 LA는 고정이다. 첫 적용 힘은 fresh audit와 맞으며 초기 장력은 runtime 일정 힘이 아니다. 적용 힘과 post-step 길이의 시점을 구분했다.
- 접촉 행 수·고유 physics samples·첫/마지막 step, held sample 포화, 실제 arm drift/scalar-limit 차이 및 native landmark 기반 palm-up proxy 최솟값을 원자료에서 재집계했다.
- 각 장기 raw5는 동일 길이의 short prefix와 정확히 같다. 명시 command 경로·개수는 실제 9개 run과 같다. 139개 명시 입력 SHA와 native report runtime SHA가 현재 파일에 맞고, OFF 실행은 없다.

## 수치와 판정

- [입력 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/README.md:7)의 길이 3개와 [trace 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/README.md:17)의 최대 p/q 9행을 원자료와 대조했다.
- 1초 1 N 118.622889587 mm/28.826878242°, 2 N 120.835673960 mm/30.129771321°는 0 N 73.268255309 mm/13.439338517°보다 양오차가 크다. OFF 선택 집합이 비어 있고 새 길이 미채택·0 N LA 유지 결정이 계획과 같다.
- 모든 1초 LH/어깨 contact 행은 0, PI 포화는 각 212 held physics samples다. 최대 tension 15.035908–16.020121 N, 종료 선속도 0.293048–0.464767 m/s·각속도 1.191623–2.870732 rad/s와 실제 scalar-limit 위반 0.030297–0.030300°가 문서와 맞다. 목표 제한 통과와 실제 상태 위반, 접촉 관측과 지지력 인증을 분리한다.
- 소단계 결과, PLAN §41, adapter README, VISUAL_REPORT §33의 결론이 일치한다. 기준도 큰 drift가 남아 안정 연주 성공이 아니다. 다음 3초는 같은 초기조건·LA·PI의 관측 기간 연장 계획이며 아직 미실행이다. WAIT 선행 과정·새 성공기준·기타 p/q feedback·새 제어·학습을 도입했다는 주장이 없다.

## 최종 문서·미디어 확인 및 동결

- [지원 CLI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/README.md:43)를 별도 빈 `/tmp/left_wrist_strap_reviewer_plot_20261007` 경로에서 실행해 exit 0을 확인했다. 1902×1884 canonical PNG와 재생성 PNG는 byte 및 RGBA pixel이 정확히 같다.
- canonical 이미지를 직접 확인했다. 세 기간별 x축, mm/degree 단위, 0/1/2 N 입력의 세 ON 범례와 저장 곡선이 맞고 주요 설명 잘림이 없다. 그림은 저장 CPU PhysX 측정 trace 그래프이며 native renderer 출력이 아니다.
- canonical과 재생성 manifest의 embedded 입력139, comparison1, producer1, output1 SHA를 실제 파일과 대조했다. 생성된 README/CHANGED_FILES의 절대 링크와 실제 줄 anchor가 존재한다.
- CHANGED_FILES:20은 원본 경로 기록을 reference manifest에서, 원본 raw SHA를 comparison에서 확인한다고 교정돼 현재 파일 구조와 일치한다. README:37의 actual scalar-limit 위반과 목표 제한 구분도 확인했다. 남은 지적은 없다.
- checklist·인덱스 검수 상태 및 예정 snapshot/verification/inventory는 부모의 후속 metadata 정리 범위다. 이 기록을 동결하며 snapshot 수집 뒤에는 추가 수정하지 않는다.
