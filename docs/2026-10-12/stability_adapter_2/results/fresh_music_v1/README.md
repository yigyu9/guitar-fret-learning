# 음악 조건 새 정책 구현과 첫 학습

2026-10-15. **입력·제어·학습·평가·실제 모션 저장을 연결하고, 기존 가중치 없이16회 갱신을 완료했다. 연주 성공은 아직 아니다.** 사용자 확인 사항은 [한 문서](/home/ajou/yigyu/3/docs/FRESH_MUSIC_USER_REVIEW.md)에 모았다.

## 구현 범위

입력은 기존 오디오 처리로 만든 song bundle의 줄·프렛·운지·시각과 현재 native 상태다. 정책이 raw waveform을 직접 읽는 구조는 아니다. 현재 목표와4개 미래 이벤트를 포함한744차원 관측을 공유128×2 encoder와 support15/fret33/strike6 actor heads, 보상·비용 critic에 연결했다. PPO의 새 알고리즘을 제안하거나 이 구조 자체의 논문 독창성을 입증한 결과는 아니다.

하나의 시간축과 움직이는 기타 좌표계에서 접근·압현 후보·유지·해제·줄 통과 후보를 평가한다.240Hz 물리,60Hz 제어를 사용하며 정책 출력은54개 관절 목표다. root·하체 고정, 내부 충돌 ON, 스트랩 OFF, 자유 기타 조건이다. human PD·중력 보상·제한된 근위부 지지를 사용한다. 기타 직접 힘·고정 부착·지속 pose 덮어쓰기는 실행 기록에서 없었다.

현재 버전은 [launch_v4.sh](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/launch_v4.sh) / [run_v4.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/run_v4.py) / [environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment_v3.py)다. 이전 소비 버전과 실패 결과는 보존했다. 실행 방법은 [구현 README](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/README.md)를 따른다.

## 실제 결과

곡은 `00_SS1-68-E_comp`다. B는 첫 압현 단음, C는 첫 두 이벤트, D는 첫8개 이벤트다. 실제 시간축 보존과 명시적 준비·preroll을 사용했다. B에서만 새 정책을 학습했다.

| 실행 | 실제 완료 범위 | 성과와 한계 |
|---|---|---|
| scratch B 학습v4 |16갱신·4,096전이·완료 에피소드16개 |오류0, 제외0. 마지막 추가 에피소드는 예산 종료 시 미완료이며 정상 전이는 PPO에 포함 |
| B 초기 기준 |245제어·4.0833초 |발음 구간 marker 목표거리 평균154.192mm, 접촉·기하 유지0초 |
| B checkpoint0016 단회 평가 |245제어·4.0833초 |평균154.101mm, 접촉·기하 유지0초, 유지·해제 후보 미완료 |
| C 시간축 검증 |251제어·4.1833초 |0행동 및±0.2 무작위 행동 실행 완료. 학습 성과 아님 |
| D 기준 녹화 |475제어·7.9167초 |8개 이벤트·15개 줄 타현 목표 중 후보 일치0개. 학습 성과 아님 |

초기 대비 평가의 거리 변화는 약0.092mm로 실질 개선이 미미하다. 학습 중 확률 행동의 평균149.69mm를 결정론적 평가 성능으로 대신 제시하지 않는다. B 평가의 보상 합은0.298104→0.298293, 비용 합은0.058081→0.050200이었다. 위치 허용 범위 이탈은 두 실행 모두0이었다. 회전 비용은 Euler 허용 집합까지의 **실현 가능한 거리 상한**을 사용하므로 정확한 최단 회전 오차로 해석하지 않는다.

실제 초기 checkpoint에서 actor heads의 weight·bias가0, log_std가−3임을 확인했다.16갱신 뒤 encoder·세 actor head·두 critic·분산 파라미터가 모두 바뀌었다. 최대 파라미터 변화는0.004562다. 평가가 정확한0016 checkpoint SHA를 읽었고 평가 중 추가 갱신은 없음을 확인했다. 최종 정책은 [checkpoint_0016.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/pilot_b16_v4/checkpoint_0016.pt)다.

PPO의 epoch 후 KL은0.0333~0.4160, clip fraction은0.4414~0.8477이었다. `target_kl=0.03`은 epoch 후 다음 epoch를 중단하는 기준이지 상한을 보장하는 제약이 아니다. 이번 기록은 학습 안정성의 증명이 아니며, 작은 초기 탐색 분산과 학습 갱신 크기의 관계를 후속으로 확인해야 한다.

## 영상과 실제 모션

B 기준과 평가의 각 영상은124프레임, D 기준은239프레임이다. 시작 상태부터 마지막 물리 시점까지 포함한다. 영상은30fps이고 첫·마지막 프레임을 포함하므로 재생 길이와 물리 시간 길이가 약간 다르다. 실제 joint 상태는60Hz와 시작 상태를 합쳐 각각246/246/476프레임이다. 모든 내보낸 관절 위치·속도·기타 상태가 원본 로그와 정확히 일치했다.

![학습 후 단음 평가 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/eval_b16_v4/whole_body.mp4)

![학습 후 단음 평가 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/eval_b16_v4/hands.mp4)

- [B 초기 모션](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/motion_baseline_b_v4/motion.jsonl) · [학습 후 B 모션](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/motion_eval_b16_v4/motion.jsonl) · [좌표·관절 이름·단위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/motion_eval_b16_v4/manifest.json)
- [8이벤트 D 기준 모션](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/motion_baseline_d_v4/motion.jsonl). 원본 skeleton·자산을 사용하는 native 궤적이며, 리타기팅한 BVH/FBX 파일이 아니다.

실제 렌더에서 전신·기타·양손의 큰 구조를 확인했다. 실행 로그의 visual geom 경고와 작은 줄·프렛 시각 요소의 한계는 남아 있다. 영상만으로 정확한 압력이나 줄 접촉을 인증하지 않는다.

## 검증과 보존 이력

단위 검사33개가 통과했다. 독립 검수는 [review_v4.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/review_v4.md)에 있다. qualificationv2는 원래 실패한153개 명령 재생,0행동 B/C/D,±0.2 무작위 행동 B/C/D의7개 실행을 통과했다. 재생의 앞152개 native 모션·목표·effort는 원본과 완전 일치했다. 현재/직전 표본의 전체 body·지지점 후보를 각각 일관되게 검사하며0.01m/s 문턱을 유지했다. 선택된 모든 native 후보는 current였다. 이 결과는 해당 유한 실행의 속도 표본 호환성 검사이며 모든 행동의 물리 안전성이나 torque Jacobian 정확성의 증명이 아니다.

첫 v2 학습은 속도 검사로0갱신·152개 전이 제외 후 중단했다.±0.8 스트레스도 현재·직전 두 후보가 실패해 중단했다. 이 실패를 지우지 않았다. 이후 작은 초기 탐색 표준편차 exp(−3)를 사용한v4는 행동 권한과 학습 가능한 분산을 유지한다.

qualificationv1 실행 중 진단 스크립트의 완료 판정이 수정되는 보존 위반이 있었다. 원래 결과의 `inputs_unchanged=false`를 유지하고 원문을 복원했으며, 변경본을 별도v2로 다시 실행했다. [사건 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/guard_source_change_record.json)과 [독립 검수v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/review_v3.md)에 범위와 SHA를 남겼다. 최신 native 학습·평가의 입력 변경은0개이며 과거 사고까지 변경 없음으로 설명하지 않는다.

원자료에서 계산한 수치와 모션 검증은 [analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/analysis_v1.json)에 있다. 입력 검사는 현재 human·guitar XML의 모든 mesh 선언을 포함한다. [최종 root 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json)에서 최신 실행 입력 union1,333개의 불변을 확인하고 소스·설정1,024개를 `source_final/`에 보존했다. 산출물 목록은 마지막 문서 검사가 끝난 뒤 `artifact_inventory.json`으로 봉인한다.

## 남은 기술 과제

첫 목표까지 약15cm의 접근을 현재 관절 범위에서 달성할 수 있는지 확인하고, 접근→접촉→유지의 학습 단계를 검증해야 한다. 무조건 학습 시간만 늘려 성공을 기대하지 않는다. 현재 distal marker 판정은 실제 손가락 패드 압력·줄 진동·음향을 모델링하지 않으며, root·하체 고정 결과를 전신 동적 제어 성과로 쓰지 않는다. 같은 단음의 단회 평가로 곡·초기 자세 일반화를 주장하지 않는다.

전체8개 song bundle 중7개는 선택된 B/C/D 입력 검사를 통과했고, `02_BN3-119-G_solo`는 `training/strike_plan.json` 누락으로 명시적으로 거부했다. 기존 데이터를 임의 생성하지 않았다. 전체 곡의 모든 이벤트를 검증한 결과는 아니다. 상세 목록은 [입력 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/input_audit_v1.json)에 있다.
