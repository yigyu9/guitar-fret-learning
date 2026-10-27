# 실제 압현면 접근·감속·유지 개선

구현을 완료했고, 실제100회 학습·고정평가까지 검증했다. **학습 후 평균 달성0/67음으로 연주 성능 향상은 확인하지 못했다.** 실제 재개·원인 분리 검증과 실측영상도 완료했다. 구현/실행 검증과 학습 성과 미달을 구분한다. 이전 누적제어100회에서는 작은 지속 명령으로 손가락이 한계까지 이동했고 고정평가 평균0.978음·안전311/1024로 회귀했다. 이번 변경은 가동범위를 유지한 채 접근 목표와 정지·유지 학습 신호를 보완한다. 이전 봉인 결과는 수정하지 않는다.

## 구현

- 실제 compound neck collision mesh 두 개의 convex hull에서 공통 상향 평면을 추출한다. 현재 Gz9.3mm다. 비충돌 현 중심12.3mm보다3mm 아래이며 임의의 높이 상수를 적용하지 않는다.
- 접근 관측과 PBRS의 목표선만 이 평면에 Gz방향으로 투영한다. 현x/y·유한선분을 유지하고 프렛셀 안쪽2mm를 사용해 프렛 충돌체 내부를 목표로 삼지 않는다. 기본67음·134끝점, 지원5곡298음·596끝점의 source hull 범위를 CPU로 검증했다.
- **기존 접촉/성공 판정은 원래 현 중심·프렛·지정 손가락·0.01N 하중·clean 시간 문턱을 그대로 사용한다.** 평면 추출은 source convex 증명이며 PhysX cooked 접촉이나 실제 현 압력의 인증이 아니다.
- 손가락별 현재 음을 먼저 선택하고, 현재 음이 없으면 다음 준비음을 고른다. 현재 음이 끝나면 이전 목표의 정지 보상을 끝낸다. 같은 음에서 불필요한 반전을 강요하지 않는다.

추가 `song_finger_tracking`은 매240Hz 실제 표본에서 아래의 **유한 양성 보상률**을 적분한다.

```text
e = 선택한 압현 목표 − 실제 손가락 표면점
u = 실제 표면점의 기타 프레임 상대속도
v_desired = clip_norm(4e, 0.1 m/s)  # 기존 유효 candidate면0
quality = exp(−|e|/0.02) × (1 + candidate)
          / (1 + |u−v_desired|²/0.05² + mean((4 × LH21_action / 0.2)²))
rate = 2/s × sum(유효 선택 quality) / 곡에 존재하는 손가락 수
reward_increment = rate / 240
```

0≤rate≤4/s다. 목표에서 멀 때 접근하는 방향, 가까울 때 감속, 접촉 후 실제 정지와 요청 정지가 함께 유리하다. 손가락이 물리적으로 멈춰도 계속 움직이라는 상수 명령이면 보상이 낮다. 엄지를 포함한21축의 가동범위·4rad/s 누적 제어·PD는 유지하며 자동고정·deadzone·강제반전은 없다.

기존PBRS·접촉/clean유지/음달성·오압현·누락·실패비용과PPO/std는 유지한다. 새 음성비용을 넣어 조기종료가 유리해지는 문제를 추가하지 않는다. 실패tick의 새 양성도0이다. CPU·오른손·물리/자산은 변경하지 않는다.

GPU왼손 reward v4·surface observation v2·note ledger v2다. 상태512/행동39와3331 curriculum을 유지하되 이전reward v3모델의 strict resume를 거부한다. 새 계약끼리 복원하고 fresh 모델로 검증한다.

## 검증 현황

[동결435Python](training_source_manifest.json) · [변경 범위](source_change_scope.json) · [독립 검수](review_preflight.md) · [승인 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_press_control_20261021.md).

새 기하5·보상10·통합7 CPU검사와 독립 검수를 통과했고, 기존 관련 검사까지46개를 통과했다. 전체 단일프로세스 검사는 기존 legacy fixture JSON decode의SIGFPE136으로 중단됐다. 원시trace/FP상태는 보존했다. 해당 모듈의 새프로세스 재현은7개 통과했으며, 전체142모듈 파일별 새프로세스 검사에서는856개가 통과했고, legacy transition_capture 초기화의 JSON encode SIGFPE로 미실행된9개는 별도GDB 재실행에서 통과했다. 총865개의 서로 다른 검사를 커버했지만 최초 전체검사·첫 격리 sweep의 실패는 보존하며 단일프로세스 전체 통과를 주장하지 않는다. FPU 마스크나 검사 코드를 바꾸지 않았고 근본 원인 해결을 주장하지 않는다.

실제GPU N4 zero39 전곡 접촉 검사는 정상종료했고, 네 환경 모두32.8167초 안전 완주·각5음을 달성했다. 실제240Hz 원자료와 원장 집계를 검산했다. 단, 성공 중 선택 표면점은 source plane에서 약4.35mm 떨어져 있었으므로 이 평면에1mm까지 접근하는 것이 native 접촉의 필수조건은 아니다. [접촉 분석](contact_probe_analysis.json) · [독립 검수](review_contact_probe.md).

large1024/H32/seed7 fresh100회·3,276,800전이가 정상완료됐고, 동결435Python/580입력 pin·저장텐서 유한성·3331 curriculum 재생·원로그3200행·GPU정상close를 검증했다. post-cache free 최저7.815GiB다. 수집 중 안전 완주785곡의 평균은1.594음이며 계속 바뀌는 확률정책의 기록이다. 고정0/100 평가는 정상완료했고, 초기 평균3.8046875→최종0.0/67음, 안전 완주는1024→1021/1024였다. 단계는0이다. 이전v3 최종0.977539음·안전311/1024보다 안전은 회복됐지만 음 달성은 더 낮다. 이100회 결과를 근거로 장기2000회 학습을 권장하지 않는다. 실제100→101재개와N4 원인분리도 정상완료했다. [재개 검증](resume_verification.json) · [재개 독립 검수](review_resume.md). [학습 검증](smoke100_verification.json). 구현·CPU통과·실행완료를 학습향상으로 표현하지 않는다.

## 실행

실제 fresh100회는 아래 설정으로 실행했다. 출력 경로는 새 디렉토리여야 하며, 기존 결과 디렉토리를 덮어쓰지 않는다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu --size large \
  --num-envs 1024 --horizon 32 --updates 100 \
  --checkpoint-every 50 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_song_press_v1
```

`initial.pt`·`final.pt`와50회 중간저장본, `settings.json`·`training_contract.json`, `update_*.json`, `episodes.jsonl`·압축 raw, `report.json`을 출력에 저장한다. 이번 실제100회 결과는 이 문서 옆 `smoke100/`이며 위 `runs/` 경로는 향후 새 실행 예시다. 환경의 Isaac Gym/PYTHONPATH/라이브러리 설정은 기본 학습 문서를 따른다.

## 고정 평가와 남은 문제

| 실제 GPU1024 고정 정책 | 초기0회 | 최종100회 |
|---|---:|---:|
| 전체 첫 곡 평균 달성/67 |3.8046875|0.0|
| 안전 시간축 완주 |1024|1021|
| 물리 실패 |0|3|
|67음 전체 성공 |0|0|

단계는 접근0에 머물렀다. 공통 안전1021환경에서도 평균3.800195886→0음이다. 최종0음은 실패3곡 때문에 평균이 낮아진 현상이 아니다. 이전v3 동일100회 모델의 평균0.977539·safe311/1024와는 관측/보상이 다르며, 같은native 성공·안전 기준만 제한 비교한다. [고정 평가 분석](smoke_evaluation_analysis.json) · [동일100회 비교](compare_baseline.md) · [평가 독립 검수](review_evaluation.md).

최종 정책의 사전지정0..7 캡처는 모두 안전32.8167초·0음이었다. env0에서 손가락21축 중18축은 실제1969회 결정 내내 한 방향 명령이었다. 손가락이 전혀 움직이지 않은 것이 아니라 누적 명령으로 목표/관절을 멀리 움직이고 유효 압현 시각의 목표 기하를 놓쳤다. 60Hz 자세 기록을240Hz 극값이나 실제 현 압력으로 해석하지 않는다. [최종 정책 자세·명령 분석](final_policy_diagnosis.md).

별도N4 폐루프 진단은 최종100회 모델을strict복원하고 학습 없이 수행했다.

| 적용한 명령 | 안전 완주 | 달성 음 |
|---|---:|---:|
|학습 정책 전체 |1/1|0|
|손가락21축 명령0·팔/손목 정책 |1/1|5|
|팔/손목12축 명령0·손가락 정책 |1/1|0|
|전체39축 명령0 |1/1|5|

0은 native 관절의 실제 자세 고정이 아니라 준비된 목표를 유지하는 요청이다. 각 행은 자기 관측으로 계속 정책을 추론한다. case↔envID·N4/1024·폐루프 관측 차이가 있으므로 정밀 인과실험·모든 손가락의 도달가능성·일반화는 인증하지 않는다. 이 작은 조건에서는 손가락 누적 출력에 우선 초점을 둘 근거지만, 새 보상으로 한방향 출력이 해결됐다는 증거는 아니다. [원자료](policy_ablation_n4/report.json) · [누적 명령·하중·원장 검산](policy_ablation_analysis.md).

거리kernel의 먼 목표 신호 약화와 현재 보상/비용 대비 추종 신호 크기는 후속 가설이다. 독립 정지 보상을 크게 추가하면 움직이지 않는 쪽이 유리해질 수 있어 이번 구현에 추가하지 않았다. [후속 보상 수식 검토](followup_reward_diagnosis.md). 이100회만으로 장기수렴 불가능을 증명하지는 않지만2000회 실행 준비 완료로 분류하지 않는다.

## 실제 저장 모델 영상

점수로 고르지 않고 사전지정0..7 중 가장 작은 안전환경ID0을 선택했다. 최종100회 모델의 실제GPU 자세를60Hz로 그대로 재생하며 새 물리·자세 보간은 없다. 전신/손 모두 같은1969프레임·32.816667초·1280×720이다.

[전신 영상](final_fullbody_video/final_fullbody_60fps.mp4) · [왼손 영상](final_hand_video/final_left_hand_60fps.mp4) · [처음/중간/끝 시각 확인과 독립 ffprobe](video_qa.json)

독립 최종 검수는 [review_final.md](review_final.md), 실행 후 입력/소스 최종 확인은 [final_integrity.json](final_integrity.json)을 따른다. CPU 전체검사 최초 실패와 재실행 범위는 [cpu_tests.json](cpu_tests.json)에 보존했다. 모든 작성자·GPU/GL 실행 종료 후 이 디렉토리 파일은 `result_manifest.json`으로 봉인한다.
