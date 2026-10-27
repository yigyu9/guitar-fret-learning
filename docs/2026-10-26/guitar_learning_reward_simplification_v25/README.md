# 왼손 학습 단순화 v25

승인한 [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_reward_simplification_v25_20261026.md)의 구현 기록이다. 새 구성은 `--learning-family finger-skill`로 선택한다. 기본 `song`과 이전 `finger-skill-v24`는 재현 경로로 유지하며 새 보상·종료 계약을 암묵 적용하지 않는다.

**구현·검증 완료:** CPU565검사·24구간 shadow·large1024 저장/재개·large128 단기64회·전곡16평가·손/전신 영상·독립 검수를 완료했다. 기능 검증은 통과했으나 전곡 평가는16개 모두 손목 종료, 평균0/67음이다. 장기 학습과 자연스러운 압현 성능은 입증하지 못했다. [결과와 한계](VERIFICATION.md).

## 실행

기존 Isaac Gym/rl38 환경에서 프로젝트 루트를 기준으로 실행한다.

```bash
python -m guitar_learning.train \
  --hand left --physics gpu --learning-family finger-skill \
  --size large --num-envs 1024 --horizon 32 --updates 180 \
  --out /home/ajou/yigyu/3/runs/left_simplified_v25_01
```

출력 경로는 새 경로여야 한다.035/v14 상태를 에피소드 경계에서 복원하고 첫 tick부터 팔·엄지·네 손가락33축을 모두 학습한다. 준비 시간은3초이고 R/F 준비 관문·사전 평가·외부 전문가 모델은 없다. 비활성 오른손6축은0이다.

처음 계획한 실제 전이 예산의25% 동안 원곡의 연속 구간을 사용하고 이후 새 에피소드부터 원곡67음 전체로 바꾼다. 이미 연주 중인 구간은 끝나거나 실제 실패할 때까지 유지한다. H32는 곡 종료나 reset이 아니다. 전환 기준은 저장본에 고정하며 재개나 추가 학습 때 구간 학습으로 되돌리지 않는다.

같은 구성의 `--resume /absolute/path/to/final.pt --updates N`은 추가 N회다. 모델·Adam·난수·sampler·노출 예산과 실제 committed scope 수를 엄격 복원한 뒤 새 준비 에피소드에서 시작한다. 구버전557상태 모델을 새561상태에 이어 쓰지 않는다.

## 보상과 종료

활성 reward는 목표 패드 접근, 최초 접촉, 압현 유지, 압현 달성, 오압현, 음 수행 부족, 대기 자세, 엄지 안내, 행동 변화의9개다.

접근과 추종은 거리·근접 방향 품질의 단일 potential로 합쳤다. 누락과 미달성은 `max(missing/D, 1−best_clean_streak/required)`의 부족률 하나로 평가하고 음당 최대0.10b 예산 안에서 누락 증가분과 음 끝 차액을 정산한다. b는 현재 선택 과제의 기존 손가락 균형 계수다.

손목 위치 감점·별도 추종·별도 missing/missed·실패 reward−2는 합산하지 않는다. 정상 연속 물리 cost도 제거하고 실패 시 다음 비용만 한 번 부과한다.

```text
종료 cost = 5 + 2 × 남은 로컬 시간 + 남은 선택 음의 미관측 감점 예산
```

물리 실패 문턱은 기존과 같다. 손목은 초기3초 이후 안내 상자 밖 추가3cm에서 이탈 상태를 켜고0.75초 지속하면 종료한다. 추가2cm 안으로 복귀하면 상태와 timer를 지운다. 심각 이탈은 추가10cm에서0.10초 지속 시 종료하며 준비 시간에도 적용한다. 음이 바뀌거나 PPO가 갱신돼도 timer를 지우지 않는다.

물리/손목 실패는 해당 환경만 reset하고 학습은 계속한다. 숫자/제어 인증/입력 SHA/자원/저장 오류만 실행 보호 중단이다. 손목 실패와 물리 붕괴는 따로 집계하며 동시에 발생해도 비용은 한 번이다.

PPO는 reward/cost advantage를 합친 뒤 한 번 정규화하는 `joint`와 고정 cost weight1을 사용한다. 정상 cost 삭제와 합산 변경을 포함하므로 종료 비용의 원시 숫자만 과거와 비교하지 않는다.

## 유지한 조건과 한계

자유 기타·중력ON·스트랩OFF·Root/의자 고정·하체 유한 제어·native105/97/8·48POSITION/57EFFORT·기존 패드/접촉/clean 측정을 유지한다. 손가락 움직임 비용0·전체 가동범위·4rad/s·PD/힘 상한·약한 B와 엄지 안내도 유지한다.

팔은 기존 초기 참조각 기준 위치 요청이고 LH21은 기존 누적 제어다. 작은 팔 출력과 엄지 누적 편향이 보상 통합만으로 해결됐다고 가정하지 않는다. 팔이 압현을 대신하는 현상도 기존 고정 패드점 운동 분해로 확인해야 한다.

공용 측정 원장의 `scope`와 자세 진단 `integration`에는 과거의 stage-weighted/graded-missed 용어가 일부 남아 있다. 이 문구는 측정 출처 설명이다. v25 실제 최적화는 `reward.active_terms`·`reward.simplified`의9개 고정 계수와 max 부족률 정산을 따른다. 원장의 실제 지불액·정산 여부와 `reward_components`를 계산 근거로 사용한다.

## 평가·영상과 기록

```bash
python -m guitar_learning.tool.evaluation.evaluate_finger_skill \
  /absolute/path/to/final.pt --out /absolute/path/to/new_evaluation --scope full_song

python -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint /absolute/path/to/final.pt --out /absolute/path/to/new_video --scope full_song
```

노출 로그는 실제 구간/전곡 전이 수를 PPO commit 범위에서 기록한다. 음별 원장은 원본67개 ID·선택 mask·지불액·정산 여부를 보존한다. 영상에는 원시 자세와 손목 종료 관측4열도 같은 제어 끝점에서 저장한다. 기존 로그를 덮어쓰지 않는다.

현재 검증 현황은 [검증 문서](VERIFICATION.md)에 모은다. 변경 전 원문500개 Python과 관련 문서는 [보관 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_reward_simplification_v25/manifest.json)에 있다. 별도 active_press 실험 파일은 이번 변경 범위 밖이며 보존했다.
