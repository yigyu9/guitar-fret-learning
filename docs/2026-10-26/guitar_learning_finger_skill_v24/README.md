# 왼손 손가락 학습 구조 v24

승인한 [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_finger_skill_v24_20261026.md)의 구현·검증 기록이다. 기존 전곡 학습은 유지하며 새 구조는 `--learning-family finger-skill-v24`로 선택한다. 코드 구동과 학습 성능 향상은 구분한다. 최종 검증 상태는 [검증 결과](VERIFICATION.md)에 기록한다.

## 실행

프로젝트 루트에서 Isaac Gym 실행 환경을 활성화한 뒤 실행한다.

```bash
python -m guitar_learning.train \
  --hand left --physics gpu --learning-family finger-skill-v24 \
  --size large --num-envs 1024 --horizon 32 --updates 3000 \
  --out outputs/guitar_learning/finger_skill_v24_run01
```

하나의 실행이 합의한 035/v14 준비 상태를 불러오고 R→F→J를 관리한다. native 대기 시간은 0초, 정책 준비 시간은 3초다. `--updates`는 자동 실행의 J 예산이며 R은 최대32회, F는 최대256회다. 최초 고정 평가에서 준비가 충분하면 R 학습을 생략한다. 준비/획득 기준을 채우지 못하면 해당 단계의 정체를 기록하고 종료하며 자동으로 기준을 낮추지 않는다. 외부 전문가 모델이나 수동 자세 설정은 필요 없다.

처음에는 독립 탐색·매60Hz 결정을 쓴다. 다음 옵션은 효과를 분리해 확인할 명시적 비교 조건이다.

```bash
python -m guitar_learning.train \
  --hand left --physics gpu --learning-family finger-skill-v24 \
  --skill-phase F --skill-exploration correlated --skill-hold-ticks 3 \
  --size large --num-envs 128 --horizon 32 --updates 100 \
  --out outputs/guitar_learning/finger_skill_v24_f_comparison
```

직접 지정한 F를 새로 시작하면 support도 초기 모델이다. 자동 R→F에서 이전한 support와 같은 조건이라고 해석하지 않는다. 단일 단계의 `--resume CHECKPOINT --updates N`은 동일 계약에서 추가 N회이며 원래 단계 예산과 추가 실행 예산을 별도로 기록한다. 자동 실행의 재개는 기존 총예산의 남은 양을 따른다. v22/v23 저장본의 엄격 재개나 암묵적인 성과 이전은 지원하지 않는다.

## 동작

| 단계 | 학습 대상 | 나머지 동작 | 과제 |
| --- | --- | --- | --- |
| R | 팔·손목12축과 엄지5축 | 네 손가락은 초기 결정론적 명령 | 손목 영역·엄지 안내·물리 안전 |
| F | 검지·중지·약지·소지16축 | support 정책은 동결하고60Hz로 재계산 | 원곡의 연속 구간 |
| J | 왼손 전체33축 | 비활성 오른손6축은0 | 원곡67음 전체 |

정책 인코더·이벤트 인코더·출력부·표준편차를 support와 finger로 나눈다. 동결 파라미터는 optimizer에서도 제외한다. F의 팔은 강체로 고정되는 것이 아니라 기존 물리와 동결 정책대로 움직인다.

원곡20개 겹침 묶음에서24개 학습 view를 만든다. 원본 ID·압현·음 시작·종료 시각을 유지한다. 원래15음 묶음은 뒤의 약10ms 간격 때문에 자체 시작 기준 안전한60Hz 종료가 없어17음까지 확장된다. 단음 과제를 새로 만들거나 진행 중인 음을 잘라 버리지 않는다. reset 때 손가락별 bucket을 균등 순환한다.

로컬 물리 시계와 원곡 악보 시계를 분리하며 선택 mask를 보상·감점·관측·추종·음별 분모에 함께 적용한다. 준비3초의 B 체류는 원곡 실제 회복창 성과와 따로 기록한다.

상관 탐색은 공통 굽힘과 두 차이 방향을 갖는 완전한3축 분포다. 각 관절의 초기 탐색 분산은 독립 탐색과 같고 자유도는 줄이지 않는다. F의 결정 지속 옵션은 최대3/6tick이며 음 경계의 전후60Hz 경계에서 줄인다. 물리는240Hz, 저수준 제어는60Hz를 유지한다. 결정별 확률·실제 지속시간에 맞는 할인·GAE·PPO를 사용한다.

손가락 움직임 비용0·전체 native 범위·4rad/s·PD/힘 상한·자유 기타·기존 접촉/clean 기준을 유지한다. B는 약한 idle 선호이며 압현 준비/음 구간에는0이다. 새 움직임 보너스나 강제 B 복귀는 없다. 첫 구조 비교의 F/J 음악 그룹 비중은 기존 v22 초기값으로 고정하며 R/F/J를 기존 음악 stage0/1/2로 바꾸어 부르지 않는다.

## 결과와 진단

상위 `report.json`은 단계·정체 사유·최종 checkpoint·실제 학습/평가 전이 수를 모은다. 각 단계 디렉토리는 설정·실제 계약·입력 SHA·초기/최종/정기 checkpoint·`learning_metrics.jsonl`·원시60Hz `transitions.jsonl.gz`·결정별 `decisions.jsonl.gz`·완결 `episodes.jsonl`을 저장한다. 수집 경계에서는 곡과 장면을 이어가고 단계 전환에서는 이전 실행을 마감한 뒤 새 준비 에피소드를 시작한다.

음별 원장은 원본67개 ID와 선택 mask를 모두 보존한다. 각 손가락의 달성·clean·wrong/missing·B·엄지·극단 관절 조합에 더해, 고정128개 패드점의 이동을 팔/기타 상대 이동과 내부 손가락 운동으로 나눈다. 변위는 압현 힘의 기여율이나 음향 성공 인증이 아니다.

```bash
python -m guitar_learning.tool.evaluation.evaluate_finger_skill \
  /absolute/path/to/checkpoint.pt --out /absolute/path/to/new_evaluation \
  --scope full_song

python -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint /absolute/path/to/checkpoint.pt \
  --out /absolute/path/to/new_video --scope full_song
```

평가는 동일 정책/제어 계약의 결정론적 실행이며 실패도 고정 분모에 포함한다. 영상은 사전 지정 env0의 첫 에피소드로 손/전신을 저장한다. 가장 좋은 환경의 영상이라고 해석하지 않는다.

## 소스와 검수

- 변경 전474개 Python과 관련 문서: [원문 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_v24/manifest.json).
- 첫 후보의 기본 helper 호출 호환 수정 전495개 Python: [후보 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261026_finger_skill_v24_before_compatibility_fix/manifest.json).
- 현행 [소스 봉인](support/source_manifest.json), [CPU 검사](support/cpu_checks.json), [독립 검수](support/review.json).
- 편집 종료 확인 후 현재 소스로 [최종 재검증](VERIFICATION.md)을 완료했다. large1024 저장/재개와 전곡 평가·[손 영상](render_F3_final/hand.mp4)·[전신 영상](render_F3_final/fullbody.mp4)을 포함한다. 짧은 직접 F8회 모델은 평균4.9375/67음이며 모든 달성이 검지에 편중되었다. 구조 연결 검증과 학습 성능 개선을 구분한다.

원문 보존 대상 `music_task.py`·`song/task.py`·`song/__init__.py`와 과거 결과/보관본을 변경하지 않았다. 현행 코드에서 보관본을 import하지 않는다.
