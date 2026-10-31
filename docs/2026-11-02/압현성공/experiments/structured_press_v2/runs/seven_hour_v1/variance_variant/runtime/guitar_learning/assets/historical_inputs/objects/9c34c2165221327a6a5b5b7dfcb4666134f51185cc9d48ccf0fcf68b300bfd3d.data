# 전곡 공동 학습

이 문서는 기존 BC 이전·양손 공동 학습의 전문 경로다. 새 정책으로 손별 전곡 학습을 시작하려면 [기본 실행](../../../README.md)을 사용한다. 공용 환경·측정·음별 판정은 `guitar_learning/song/`으로 승격했으며 아래 전문 초기화·평가 계약은 유지한다.

현재 실험 대상은 `05_BN2-131-B_solo`의 원매핑67음 전체다. 단음 전용 `joint/`와 다른 계약으로, 한 native episode에서 곡 끝까지 이어간다. PPO rollout 경계에서는 장면·관절·기타·곡 시계·음별 원장을 초기화하지 않는다. episode 종료/물리 실패 때만 prepared 상태로 reset한다.

## 곡과 입력

원음29.3063946초 + 능동 준비3초 + 말미0.5초를 60Hz 경계로 올려1969 tick=32.8166667초를 실행한다. reset부터 첫 목표가 보이도록 lookahead4초를 제공하며 전체곡 최대18/64토큰이다. 첫 음은 정책3.6385초, 마지막release-capped end는30.0048초다. 단음 실험처럼 원곡의 처음을 잘라내 시간 원점을 옮기지 않는다.

정본은66이벤트에67음이 있다. unsupported `event-000042`만 원note_on에 두 번의 공격으로 펼친다. 두 번째 방향은 원자료에 따로 없어 aggregate 방향down을 두 음에 상속한다. 이는 명시적 파생 가정이며 원정본 파일은 바꾸지 않는다. 23.3ms 간격은60Hz에서약1.4tick이라 어려운 전환이다. 67음의 원번호·onset·fret·현·손가락·release 상한·SHA를 계약과 schedule에 기록하며 음을 생략하지 않는다. 모두 압현음이며 이번 경로는 열린현을 명시적으로 거부한다.

상태500=기존 몸/기타/음악468+전곡이력32, 이벤트64×24, 우선슬롯2, 출력39=왼손33+오른손6이다. 두 Actor가 독립 파라미터로 같은 전곡 관측을 받고 reward/cost Critic은 중앙에서 학습한다. 기존 검증BC에서 동일 이름·scale의 물리460열과 이벤트/attention/head/std를 이전하고, 재정의된 음악8열+전곡이력32열은0으로 시작한다. 단음95이력은 버리고 Critic/Adam은 새로 시작한다. 이전 출력·성공·optimizer를 상속하지 않는다. strict resume는 전곡 architecture/계약/PPO config를 정확히 비교한다.

## 판정과 안전

모든 목표를 매240Hz 표본에서 원접촉 기준과 `classify_fretting`으로 분류한다. 반복 목표의 동일 물리tuple 분류는 캐시하지만 목표를 건너뛰지 않는다. 전곡은 기존 연속 StrikeDetector의 finite sweep·깊이·속도·zone·재무장을 사용한다. 단음의 한 번만 성공 가능한 latch와 매음 완전 손 해제 조건은 사용하지 않는다. 다음 정당한 음으로 바뀌는 접촉은 해제 실패로 몰지 않는다.

음별로 clean audible 유지, 오압현/미압현, 완화된±0.5초 목표 타현과 miss, 타현 순간 양 끝 표본의 clean 압현을 기록한다. 한 crossing은 가장 가까운 미매칭 목표 하나만 소비한다. 음별 LH 유지 기준은 min(음길이,max(50ms,음길이×0.4))다. 전곡 성공은 전구간안전완료와 모든67음의LH/RH/협응 달성 및 wrong/repeat0을 함께 요구한다. 원50/100ms MusicLedger는 별도다. 밀집 접근·기타 상대 피크 guide는 보상일 뿐 압현/타현 성공 근거가 아니다.

Root만 고정하고 하체는 원유한유지제어를 사용한다. 기타는 자유 강체·중력ON·스트랩OFF이며 원gain/limit/접지·이탈·관절안전 조건과240Hz 비용·종료를 보존한다. 실패한 control tick의 양성 보상은 네 표본 전체에서 억제한다. 가슴 접촉 지속은 필수조건이 아니다. 실제 음압·현 진동·음향·Root자유균형·보행 검증은 아니다.

## 실행과 파일

- 공용 `guitar_learning/song/task.py`: 원자료 검증·67음·전곡 시계·파생 규칙.
- 공용 `guitar_learning/song/measurement.py`, `metrics.py`: 실제 접촉/타현과 음별 판정·보상·500상태의32이력.
- 공용 `guitar_learning/song/environment.py`: native0초 준비, 단일persistent장면에서4물리표본/60Hz39축 동시제어.
- `policy.py`, `transfer.py`, `settings.py`: 새500계약·전문가 증거·명시적 특징 이전.
- `worker.py`, `train.py`: spawn worker·PPO·메모리 보호·checkpoint·곡진행/음별 결과 요약.
- `evaluate.py`: 고정 특징 초기값 또는 전곡 PPO의 한 번의 전체 deterministic 시도와 native pose/측정 streaming 원자료.

프로젝트 루트에서 rl38 Python을 사용한다. 이전 단음 joint 체크포인트를 `--resume`로 직접 불러오지 않는다. 새전곡checkpoint는 같은계약/config에서 strictresume 가능하다. 출력은 새 디렉토리여야 한다.

```bash
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:$LD_LIBRARY_PATH
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.experiments.song.train \
  --settings docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_settings_v1.json \
  --out /tmp/guitar_full_song_new
```

평가는 같은설정으로 `python -m guitar_learning.tool.experiments.song.evaluate --settings ... --run 학습디렉토리 --out 새평가경로`다. `--run`을 생략하면 검증된 BC의 특징만 이전한 초기 정책으로 평가한다. 최초 모델의 전곡 성공을 의미하지 않는다.

10초 주기 heartbeat, 자원·전이·episode·learning 로그와 원checkpoint/optimizer를 보존한다. 전곡 지표는 `song_report.json`의 완료episode 집계, 마지막부분궤적 snapshot, 최대곡시각·만료음 개수를 구분한다. 누적 카운트를 전이마다 합산하지 않는다. 실제 결과는 `docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/`에 기록한다.
