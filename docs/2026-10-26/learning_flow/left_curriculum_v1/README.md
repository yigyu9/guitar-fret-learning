# 왼손 전곡 학습의 성능 기반 보상 단계

사용자 요청에 따라 기본 왼손 학습을 손목 위치 잡기 → 압현 → 곡 연결의3단계로 확장했다. 같은 커맨드에 자동 적용하며 전곡67음·035/v14 초기 자세·native 대기0초·정책 준비3초·240/60Hz·39행동·원 물리 안전을 유지한다. 코드 확인일과 구현일은2026-10-20이며 요청한 문서 디렉토리 날짜와 구분한다.

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --out /home/ajou/yigyu/3/runs/left_song_01
```

실행 환경과 전체 흐름은 [상세 학습 흐름](../README.md)을 따른다. 출력은 새 경로여야 한다.

## 보상 전환

진행도는0~2이며 아래 세 지점 사이를 선형으로 보간한다. 현재 비중은 전이에 기록되고 수집 동안 고정된다. 손목 도달 여부로 접촉 보상을 끄거나 손가락을 강제 고정하지 않는다.

| 묶음 | 위치 잡기0 | 압현1 | 곡 연결2 |
| --- | ---: | ---: | ---: |
| 손목 위치·약한 방향 보조 |1|0.35|0.10|
| 준비/수행 clean 접촉·오압현 |0.15|1|1|
| 원곡의 clean 유지·음 성공·누락 |0.10|0.35|1|
| 기존 손끝 거리 접근 |0.20|0.10|0|

공유 행동 변화 감점·실패 감점·안정 비용은 비중을 줄이지 않는다. 물리 실패tick에는 새 손목/접촉 보상을 포함한 모든 양성 song 보상을 억제한다. 음악 성공은 기존 원곡 시간축의67음 clean 유지와 안전 전곡 완주를 계속 요구한다. 손목 도달이나 준비 구간 접촉을 음악 성공으로 대체하지 않는다.

최근8회 완료 에피소드의 성능을 두 worker에서 모아 부모가 판단한다. 최소4회 기록이 있어야 하며 안전한 전곡 비율75% 이상·손목 도달 비율 평균70% 이상이면0→1을 진행한다. 1→2에는 clean 접촉 달성 비율 평균60%도 필요하다. 새로운 안전 전곡이 있는 PPO 갱신당 최대0.1 증가하고 실패는창에0점으로 남긴다. 부분 궤적·새 실패만으로는 진급하지 않는다. 이 수치들은 초기 학습 기준이며 수렴이 입증된 설정은 아니다.

## 손목과 접촉의 측정

기존 곡의 절대 손목 오프셋은 초기 자세의 실제 손목과 약13.90cm 차이가 있어 그대로 사용하지 않았다. manifest SHA/bytes로 확인한 곡 자료의 `anchor_fret`만 읽는다. 실제 reset 손목의 기타 기준 x/z를 유지하고 현재 기타의 anchor 프렛과5프렛 y 차이를 더한다. 초기 상대 손 방향은 약한 보조 기준이다.

```text
목표_기타 = 초기손목_기타 + [0, 현재프렛_y(anchor) − 현재프렛_y(5), 0]
```

현재035/v14 준비 상태에는 string1/fret5/index의 실제 clean 접촉 후보가 기록되어 있다. 목표 생성은 이 손 모양을 프렛 방향으로 평행 이동하는 보조 가이드이며 모든 프렛의 역기구학 도달 가능성이나 실제 압력·음향을 보증하지 않는다. 지원5곡의 anchor 무결성과 좌표 변환을 검사했다.

손목4cm·방향0.6rad 이내의 연속 표본 구간을 준비 시작2초 전부터 음 종료까지 누적한다. 목표별 최대0.1초 요구 시간을 만족하면 도달로 센다. 접촉은 press~end의 실제 clean 표본쌍에서 초당0.5와 최초 요구 시간 달성0.5를 준다. 접촉 요구 시간은0.05초와 해당 구간 길이 중작은 값이다. 원곡의 onset~end 유지 기준은 별도로 유지한다. 별도 해제 보상이나 모든 음 사이의 강제 완전 해제는 추가하지 않았다.

## 구현과 저장

| 위치 | 역할 |
| --- | --- |
| [wrist_guide.py](/home/ajou/yigyu/3/guitar_learning/song/wrist_guide.py) | anchor 검증·현재 기타 프레임의 손목 목표와 오차 |
| [left_curriculum.py](/home/ajou/yigyu/3/guitar_learning/song/left_curriculum.py) | 최근 성능 창·진행도·보상 비중·상태 검증 |
| [left_environment.py](/home/ajou/yigyu/3/guitar_learning/song/left_environment.py) | 실제240Hz 보상·도달/접촉 근거·512관측 |
| [curriculum_runtime.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py) | 부모 집계·27개float64 checkpoint buffer·worker 동기화 |
| [launch.py](/home/ajou/yigyu/3/guitar_learning/training/launch.py)·[runner.py](/home/ajou/yigyu/3/guitar_learning/training/runner.py)·[parallel.py](/home/ajou/yigyu/3/guitar_learning/training/parallel.py) | 왼손 기본 연결·PPO 이후 기록/전환·장면 reset 없는 관측 갱신 |

왼손은 기존500개에 손목 오차6개·접촉 보너스 진행/달성/전체 비율3개·단계와 비중3개를 더한512상태다. 오른손과 전문 전곡500경로에는 새 보상을 적용하지 않는다. 이전500왼손·563단음 모델은 새 왼손 계약에 strict resume할 수 없다.

진행도와 최근 에피소드 창은 정책buffer에 저장하므로 모델·optimizer·부모 난수와 함께 재개한다. 새 프로세스의 물리 장면·곡 시계는 초기 자세의0에서 시작한다. 같은 실행에서 짧은 수집 경계를 넘으면 장면·시계·음별 원장을 유지한다.

전이/에피소드의 `left_curriculum`에는 실제 적용된 비중, 손목 목표·오차, 도달·접촉 비율과 원보상 항목이 들어간다. 에피소드에는 음별 근거가 보존된다. `update_*.json`·`song_report.json`에는 다음 수집에 사용할 진행도와 최근 창 평균이 들어간다. PPO 갱신 성공 직후 전이를commit하고 단계 동기화를 수행하므로 후속 통신 실패가 이미 학습한 전이를discarded로 바꾸지 않는다.

## 검증

핵심 검사에서 현재 기타 프레임·목표 생성·성능 전환·실패 억제·PPO/단계 저장·복원·작업자 동기화를 확인했다. 실제 PPO checkpoint로 진행도·ring 이력과 두 optimizer를 복원한 뒤 후속 갱신이 일치함을 검사했다. 두 실제 spawn worker의 단계 갱신에서도 물리 step과 reset 횟수가 바뀌지 않았다. 단계 비중을 바꾼 CPU 환경 검사는 원보상과 실제 적용 보상의 합, 실패tick의 양성 억제, 원래 음악 성공 판정의 분리를 확인한다.

실제 runner에 단계 broadcast 실패를 주입한 회귀 검사에서는 갱신된2전이가 committed로 남고 discarded가0이며 복구 모델의 업데이트 수가1임을 확인했다. 이후 보고서가 기록되지 못한 사실은 별도 recorded count로 남는다. [실패 주입 로그](failure_injection_tests.log)를 따른다.

| 실제 native 실행 | 수집 | PPO | 결과 |
| --- | ---: | ---: | --- |
| [왼손2환경](native_left/report.json) |512전이, 환경별256tick·4.2667초|2회|512관측, 새 손목·접촉 보상, 모델 저장·물리 감사 통과 |
| [왼손 재개](native_resume/report.json) |40전이, 환경별20tick|누적2→3회|strict load 후 초기 자세의 새 곡 시작, 모델 저장 |
| [오른손](native_right/report.json) |20전이|1회|기존500관측·보상, 모델 저장·물리 감사 통과 |

왼손의 첫 수집 경계128→129tick에서 곡 시계가2.1333→2.15초로 이어졌고 reset은 없었다. 실제 새 clean 접촉 보상도 기록됐다. 세 실행 모두 입력 무결성·금지 호출·물리 flag·지속형 장면 감사를 통과했다. 이번 시험은 전곡 길이1969tick보다 짧아 완료 에피소드와 전곡 음악 성공은0회다. 최근 성능 창이 비어 있어 진행도0을 유지한 것이 정상이며 native에서 단계 진급·학습 수렴을 확인했다는 뜻은 아니다.

전체 **126개 모듈·734개 검사**가 모듈별 별도 프로세스 실행으로 통과했다. 실제 왼손 final과 재개 initial의 전체 payload는 metadata를 제외하고 정확히 같았다. 여기에는 모델·양 optimizer·업데이트 수·부모 난수·27개float64 단계buffer가 포함된다. 실행 중 동결한404개 Python 소스 SHA가 최종 파일과 같고 문서 링크90개도 확인했다.

전체 모듈별 회귀 결과는 [검사 요약](module_tests_summary.json), 실제 실행·저장 모델 비교는 [최종 검증](verification.json)을 따른다. [별도 change-reviewer 검수](review.md)에서는 최초 회계 지적의 수정과 나머지 구현의 정합성을 확인했다.

기존 단일 프로세스 전체 검사에서 보고된 JSON/float SIGFPE 원인을 이번 변경으로 고쳤다고 주장하지 않는다. 단계의 실제 학습 수렴과 전곡 음악 성공은 단기 실행 검증과 구분한다.

## 이전 원문 보존

[보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_left_curriculum/manifest.json)에450개 파일의 이전 원경로·SHA를 기록하고 내부 CAS에 등록했다. 기존 실행/학습 모델·곡 입력을 덮어쓰지 않았다. 보호 대상 `song/task.py`, `song/__init__.py`, `music_task.py` 원문과 native 원자산/제어는 유지한다. [보존 기록](preservation.json), [실행 소스](source_manifest.json), [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_left_curriculum_20261020.md)을 함께 둔다.
