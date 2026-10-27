# 실제 snapshot 기반 부정 사례 감사

2026-10-27. **감사 실행은 완료했으나 단계2의 물리 부정 사례 검증은 부분 완료 상태다.** 잘못된 줄/프렛·다른 손가락만 닿음·높은 프렛 간섭은 실제 native 자세를 원래 곡의 다른 목표로 정적 판독해 확인했다. 하중이 있는 back-facing 패드, 실제 음악 시간의 짧은 접촉 전용 episode와 실제 해제는 아직 입증하지 못했다.

[기계 요약](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/summary.json)의 stage2_status는 **partial**, stage2_validation_complete는 false다. results.json의 completed는 이 CPU 감사 작업의 완료만 뜻한다. GPU·package·기존 원자료를 변경하지 않았다.

## 어떤 자료를 어떻게 사용했나

[사전 정의](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/precommit.json)를 저장한 뒤 baseline 초기/최종의 사전 지정 env0에서 균일16시점과 각 손가락 최초 candidate/최초 wrong 시점을 정해진 순서로 선택했다. 총37개의 실제 q/body/force snapshot을 사용했다. 현재 pilot의 학습 결과로 조건을 고르지 않았다.

각 실제 snapshot을 compiled67 원곡의 target67개에 대입했다. string/fret/finger/onset/end를 새로 만들지 않았고, **원래 음 하나만 scope로 선택해 그 음의 audible midpoint로 판독 시각을 바꿨다.** 실제 자세·힘·원시 physics tick은 그대로 유지했다. 실제로 그 음악 시점에 연주했다는 뜻은 아니다.

기존 current_contact_replay.sample_masks와 현행 positive/wrong v2를 재사용하고, 실제 raw body quaternion·위치·force로 패드점과 full10-body virtual surface를 NumPy에서 별도로 재구성했다.37×67=**2,479개 조건**에서 positive·wrong·몸체별3원인·candidate 불일치0, 좌표 차이 최대**7.56e−8m**였다. 측정 코드6개의 SHA는 원래 baseline과 같았고 compiled 곡 입력7개도 baseline SHA와 맞춰 전후 봉인했다.

기존9개 static/teacher 추적의240Hz 표본201,600개에서는 저장된 shared-mask 관계도 다시 확인했다. 이 검사는 positive_mask.any, wrong source flags, candidate의 논리 일치 검사다. 모든240Hz 표본에서 전체 native body/force를 다시 복원한 검사와 혼동하지 않는다. full-native 독립 재계산은 위37개 snapshot에 대해 수행했다.

[상세 결과](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/results.json)에 source 파일 SHA, env/row, 실제 tick/time, 원래 candidate target ID, 진단 target ID/time/scope와 실제 기여 표본을 기록했다. 대표35개 native 배열은 [보존 표본](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/representative_actual_native_snapshots.npz)에 원본 그대로 복사했다.

## 확인된 정적 판독 사례

줄 번호는 아래 표에서1부터 센다. P는 지정 패드 positive, W는 wrong, C는 최종 candidate다. 이 표의 모든 사례는 **실제 native snapshot을 다른 원래 target/scope/time으로 읽은 정적 대조**이며 실제 음악 보상은 지급하지 않았다.

| 사례 | 실제 source 시각 | 원래 곡에서 선택한 진단 목표 | 확인 내용 | P/W/C |
| --- | ---: | --- | --- | --- |
| far | 초기 env0,0.0167초 | 검지3번줄4프렛 | 최근접 유효 패드점~목표 셀27.79mm, 몸체 하중0 | 0/0/0 |
| 근접하지만 무하중 | 초기 env0,0.0167초 | 검지3번줄6프렛 | 같은 패드점의 위치·방향은 통과하나 native body resultant0 | 0/0/0 |
| 잘못된 줄 | 초기 env0,0.1000초 | 검지2번줄5프렛 | 실제 기여 패드점은5번줄6프렛, body resultant1.513N | 0/1/0 |
| 잘못된 프렛 | 초기 env0,0.1000초 | 검지4번줄7프렛 | 실제 기여 패드점은4번줄6프렛. 다른 점의 wrong-string도 함께 있어 한 요인만 격리한 대조는 아님 | 0/1/0 |
| 다른 손가락만 같은 셀 | 초기 env0,0.6833초 | 중지3번줄6프렛 | 검지 패드가3번줄6프렛에 loaded/facing, 지정 중지는 무하중·멀리 있음 | 0/0/0 |
| 다른 손가락의 높은 프렛 | 최종 env0,4.3833초 | 약지2번줄7프렛 | 지정 약지 positive가 있어도 소지2번줄8프렛 source가 higher로 veto | 1/1/0 |

다른 손가락이 같은 프렛에 닿았다는 이유만으로 wrong을 주지 않는 비감점 대조도 확인됐다. 지정 중지의 성공으로 대체하지 않았으므로 candidate도false다.

높은 프렛 사례는 실제 raw resultant가 약지130.35N·소지130.75N이었다. 이는 현재 판정이 어떤 source로 veto하는지 보여주는 사례이며, 정상 압력·안전한 자세·실제 줄 압력의 근거가 아니다. body resultant는 접촉 상대를 식별하지 못한다.

## 찾지 못했거나 범위가 제한된 사례

### Back-facing 실제 하중 패드: unavailable

사전 조건은 **실제 assigned body가0.01N 이상 loaded이고, 같은 유효 패드 표본의 cell/lateral/height가 통과하지만 그 표본들이 모두 normal cosine0.1 미만으로 facing을 실패하는 경우**였다.2,479개 정적 판독과 선언한 저장 static 범위에서 이 조건을 찾지 못했다.

방향을 뒤집거나 손등에 새 표본을 넣지 않았다. 현재 등록된 palmar 패드의 facing-negative 증거가 없다는 뜻이다. 모든 손등 접촉을 배제했거나 모든 physical orientation negative를 검증했다는 뜻은 아니다. other_higher는 full finger2/3 virtual surface source를 사용하므로, 이 assigned-pad 검사만으로 다른 손가락 source 전체의 방향성을 검증하지 않는다.

### 짧은 접촉: 실제 정적37.5ms 구간만 있음

static_free_B의 row0, physics343~352에서 실제 candidate 구간37.5ms를 찾았다. 해당 목표의 최초접촉 기준 tau는50ms이므로 이 구간의 진행률은0.75이고 **그 구간만으로 full tau를 채우지 못한다.** 부분 진행 보상을 허용하는 설계이므로 무조건 보상0이어야 하는 사례가 아니다.

하지만 원곡 시각은 고정됐고 원장을 지급하지 않았다. 같은 전체 궤적의 다른 접촉은50ms를 넘었다. 따라서 실제 음악 episode에서 부분접촉만 하고 미달성한 부정 사례나 부분 지급의 실측 증거로 사용하지 않는다. 기존 실제 원장24개에서도 final progress가0과1 사이이고 미달성인 episode는 찾지 못했다. 실제 원래 음 창에서의 short-only 증거는 미완료다.

### 해제: candidate 소실만 확인

static_fixed_B row1의 physics4028→4029,16.7875초에서 release 명령 구간 중 candidate가true→false, positive=false가 됐다. 그러나 wrong=true이고 body resultant는**1.153→1.110N**으로 여전히 loaded다. 이 행은 이미 손목 shadow 실패를 지난 상태다.

따라서 올바른 셀의 기하 candidate 소실만 확인했으며, 실제 접촉쌍 해제·하중 소실·살아 있는 음악 episode의 정상 해제를 입증하지 않는다. [원시 해제 관찰](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/release_observation.json)에 이 구분을 남겼다.

## 실제 원장 positive와 이번 정적 사례의 관계

[Positive 출처 구분](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/positive_evidence_scope.json)을 별도로 저장했다.

- 기존 full-DLS, press-local3초 원장에서는 검지·약지·소지가 포함된6/24 달성이 있었다. 지정4축도 teacher가 제어한 조건이다.
- 새 fixed-wrist **incremental** v2 reference는 중지3/4 달성(env1/2/3)이며 성공 행은 episode 요약만 있다. 저장된 env0 raw는 wrong100%·clean0이다.
- 별도 **position** reference도3/4 달성이나 성공 행은env0/2/3이다. **position env0은 clean1·달성이며 q/body_state/net_body_force/candidate가 포함된 native raw trace가 있다.** env2/3은 요약만 있다. incremental env0의 실패를 position env0에 적용하지 않는다.

이들을 동일 teacher 조건에서 네 손가락의 실제 raw positive를 모두 검증했다고 합치지 않는다. 실제 원장 지급 산술 검사, 정적 geometry/wrong 판정, physical negative 실행은 서로 다른 증거다.

독립 검수는 판정 논리와 대표 원자료 동일성에 문제가 없음을 확인했다. 남은 back-facing·실제 short-only·live physical release 때문에 **단계2 전체 검증 상태는 partial로 유지**한다.

position positive 출처의 잘못된 초기 설명은 [이전 버전 보존본](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/negative_snapshot_audit/before_position_evidence_correction/README.md)에 남겼고, 위와 같이 조건별로 수정했다.
