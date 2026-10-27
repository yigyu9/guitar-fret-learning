# 초기 자세에서 손별 PPO 시작

2026-10-20. 새 기본 실행은 **확정한 초기 자세 복원 → 왼손/오른손 선택 → 새 정책 PPO → 모델 저장**이다. 별도 설정 파일, 이전 BC/전문가 모델, 과거 성공 평가4회를 준비하지 않는다. 실제 좌우 학습·저장·재개와 관련19검사는 통과했다. 전체 회귀 검사는 기존 직렬화 경로의 SIGFPE로 끝까지 완료하지 못했다.

```bash
cd /home/ajou/yigyu/3
python -m guitar_learning.train --hand left --out /absolute/new_left_run
python -m guitar_learning.train --hand right --out /absolute/new_right_run
```

Isaac Gym이 설치된 rl38의 PATH/LD_LIBRARY_PATH/PYTHONPATH 환경 설정은 [학습 안내](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다. 기본2환경·100업데이트·420정책 tick/수집·medium 모델이며 `--updates`, `--num-envs`, `--horizon`, `--size`, `--seed`로 예산을 지정할 수 있다. `--device auto`는 CUDA 사용 가능 시cuda:0, 아니면CPU를 선택하고 실제 선택값을 저장한다. 명시적cuda:0 요청은 자동 대체하지 않는다.

## 실행 연결과 유지하는 조건

- [train.py](/home/ajou/yigyu/3/guitar_learning/train.py): 기본 진입점.
- [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py): 기본 설정·손 선택·작업자·정책 연결. 과거 actor 초기화/성공 gate 래퍼를 호출하지 않는다.
- [train_parallel.py](/home/ajou/yigyu/3/guitar_learning/train_parallel.py): 기존 병렬 수집·PPO·로그·모델 저장을 재사용한다. 새 진입점의 정규화된 설정은 출력 settings.json에 먼저 저장하여 영구 경로의 실제 바이트를 pin한다. 임시 설정 파일을 제거해 입력 pin을 끊지 않는다. 기존 --settings CLI는 유지한다.
- [quality 환경](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality_environment.py)과 기존 native worker를 사용한다. 상태563·행동39, 왼손33/오른손6 중 선택한 손만 정책이 제어하고 반대 손은0잔차다.
- 확정035/v14 prepared snapshot을 에피소드 경계에서 한 번 복원한다. 22초를 다시 적분하지 않고 실제 물리 시각0부터 정책이 제어한다. native 정착0초, 목표가 보이는 준비3초를 포함해 에피소드7초다.
- 기본 과제는 검수 번들의 첫 단음이다. 왼손은 압현·유지·해제, 오른손은 타현을 학습한다. 240Hz 실제 접촉·안전 측정, 60Hz 정책·유한 제어·관절 제한·자유 기타·중력ON·스트랩OFF는 유지한다.
- 호환되는 checkpoint의 --resume은 기존 PPO의 계약·optimizer·RNG 복원을 사용한다. 기존 전문 실험 경로의 BC/gate/strict 검사는 그대로이며 새 기본 실행을 위해 전역 완화하지 않았다.

## 실제 물리 실행

모든 단기 실행은 rl38·CPU 정책·small 모델·1환경·1추가 PPO 업데이트로 수행했다. 음악 성공은 좌우 각각0/1이며 아래 결과는 새 실행 흐름과 저장·재개 연결의 검증이다.

| 실행 | 수집 전이 | 최종 PPO 업데이트 | 완주 episode | 결과 |
|---|---:|---:|---:|---|
| [왼손 새 학습](native_left_v1/report.json) | 420 | 1 | 1 | 모델 저장·persistent/source/물리 검사 통과. auto 기본값 추가 전 실행 |
| [오른손 새 학습](native_right_v2/report.json) | 420 | 1 | 1 | auto가CPU 선택. 모델 저장·persistent/source/물리 검사 통과 |
| [왼손 재개](native_left_resume_v2/report.json) | 20 | 2 | 0 | 이전1업데이트 모델을 strict load하고1회 추가, 부분 episode는 완주로 세지 않음 |

왼손/오른손 fresh 입력 pin에 이전 .pt 모델은 없었다. 실제 reset 기록에서 preparation_seconds=0, prepared_physics_step=0, 원snapshot step5280을 확인했다. native/asset/PD·모델과 기존 PPO 구현을 수정하지 않았다.

[재개 payload 비교](resume_parity.json): 재개 직후 initial.pt는 이전 final.pt와 metadata를 제외한 identity·모델·양 optimizer·cost_weight·업데이트 수·Torch/NumPy/Python/CUDA RNG가 정확히 같고, 최종 업데이트 수만1→2로 이어졌다.

## 검사와 원본 보존

[CPU 관련 검사](targeted_tests_v2.log)19개 통과. 새6검사는 이전 모델 불필요, 손별 실제563계약과 반대 손0, native/tensor 설치 없이help, 장치 자동 선택, 실패 시 연결 복원, 영구 설정/현재 소스 pin을 확인한다.

[전체 회귀 로그](full_tests.log)는 SIGFPE(exit136)로 중단됐다. [종합 검증](verification.json)의 completed=false는 전체 회귀 통과를 주장하지 않는다는 뜻이다. [현재 소스 SHA](source_manifest_final.json)의385개 Python과 현재 파일 집합·SHA가 정확히 같으며 native190·tool18 provenance, 보관본·CAS 원문을 검사했다. [독립 검수](review.md)에서 새 소스 결함은 발견되지 않았다. 초기 CPU 검사에서 Pool MagicMock 상속 fixture가 의도한 중단을 만들지 못해 실제 fakeclass로 수정했다. 검증 조건이나 제품 동작은 완화하지 않았다.

원래 train_parallel 및 문서는 [작업 전 원문](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_simple_start/manifest.json), 첫 native 실행 소스는 [smoke V1](/home/ajou/yigyu/3/guitar_learning/archive/20261020_simple_start_smoke_v1/manifest.json)에 보존했다. 새 train.py가 이전 원래 경로를 재사용하므로 역사 회귀의 “삭제 경로” 선택만 같은 보관 manifest의 여전히 보관된 audit_v1로 바꿨다. 해당 검사 원문은 [별도 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261020_simple_start_historical_test/manifest.json)에 있다. 모든 원문은 원래 경로/SHA로 CAS에도 보존했으며 과거 defaults/versions는 그대로다.

전체 검사 두 실행은 기존 전환 fixture의 raw JSON 기록에서 SIGFPE로 종료했다([첫 로그](full_tests_sigfpe.log), [두 번째 로그](full_tests.log)). 해당 검사만 실행해도 `transition/probe.py:92 → json.dumps → json.encoder`에서 재현됐다([스택](transition_repro.log)). 새 검사와 함께 순서를 달리한17검사는 통과했다([재검사](order_repro.log)). capture 이후 모듈을 따로 실행한 [나머지 검사](remaining_tests.log)도 기존 `test_transition_refinement_serialization_v2.py:170`의 float 표현 비교에서 SIGFPE로 중단됐다. 따라서 분할 검사 전체도 통과했다고 주장하지 않는다.

기존 읽기 전용 observer를 넣은 [진단](fpu_diagnostic.log)은240tick/483관측에서 정상 mask와 완주를 기록했으며, mask·직렬화 backend나 제품 코드는 바꾸지 않았다. 이전 실패 순간이나 근본 원인을 확정하지 않는다. 두 번째 진단(fpu_suite_diagnostic.log)은 작업 중 중단한 불완전 기록으로 통과 근거에 포함하지 않는다. 이 작업은 새 초기 실행 연결을 완료했으며, 기존 직렬화/native 부동소수점 오류의 원인 규명·수정은 남아 있다.
