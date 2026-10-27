# 고정 0/100 정책 및 이전 실행 비교 독립 검수

요약 판정: **평가 실행·자료 무결성은 문제없음. 압현 학습 개선 판정은 실패.** 최종 정책의 전체 첫 곡 평균 달성은 0/67이며, 이를 개선된 정책 또는 장기 학습 준비 완료로 표현할 수 없다.

## 검수 범위

`smoke_checkpoint_evaluation.json`, 두 `evaluation_smoke_{initial,final}_1024`의 report/native 종료 scene/lifecycle/targets/first_episodes/입력 pins, `smoke_evaluation_analysis.json`, `compare_baseline.json/md`, 해당 비교·평가 도구 및 실제 실행 로그·프로세스 결과를 읽었다. 별도 CPU 코드로 원장과 집계를 재검산했다. 활성 source와 기존 결과는 수정하지 않았으며 GPU·GL·평가 main·비교 main을 실행하지 않았다. 진행 중인 N4 정책 ablation 결과는 범위에서 제외했다.

## 실행 및 원자료 대조

- 실제 고정 checkpoint 0/100을 각 **1,024환경**에서 deterministic하게 평가했다. 두 report/combined가 일치하고 lifecycle은 각각 `report_written`이다. 프로세스 결과는 exit 0이며 GDB 로그의 정상 inferior 종료 및 completed 출력과 일치한다.
- 각 원시 JSONL에는 env ID 0..1023의 첫 종료 곡이 정확히 한 번씩 있다. env ID로 정렬한 원장과 report의 episodes가 정확히 대응한다. 67개 target 순서·각 원장 배열 길이·음별 성공 합계·clean 문턱을 독립 재검산했다.
- 두 정책의 67음별 all-first/full-safe 분모, 성공/near/contact 비율, clean/contact/wrong/missing/near 시간 평균을 실제 원장으로 재계산해 per-note report와 일치함을 확인했다. 집계와 비교 JSON도 대응한다.
- 두 simulator가 실제로 닫혔으며 종료 scene 파일과 report가 같다. 각 1,969 control tick / **7,876 physical step**, GPU physics·GPU tensor pipeline·N1024가 일치한다. 초기 **586개**, 최종 **587개** 입력 SHA와 활성 Python **435개** SHA를 현재 파일과 직접 대조했다.
- 도구는 strict checkpoint load 뒤 저장된 curriculum을 복원하고, PPO update나 curriculum advance 없이 각 행의 현재 관측으로 정책을 실행한다. 저장 업데이트는 0/100, 두 curriculum progress는 **0.0**이다. 동일 곡/초기 자세/저장된 자체 curriculum 조건의 평가이며, 독립 seed 일반화나 모든 관측을 같게 고정한 가중치 인과 실험은 아니다.

## 실제 성과

| 고정 정책 | 안전 완주 | 물리 종료 | 전체 첫 곡 평균 달성/67 | 성공음 합계 | 전곡 과제 성공 |
| --- | ---: | ---: | ---: | ---: | ---: |
| initial 0 | 1,024 | 0 | 3.8046875 | 3,896 | 0 |
| final 100 | 1,021 | 3 | 0 | 0 | 0 |

초기 3,896개 성공은 모두 검지 목표이며 다른 손가락은 0이다. 최종은 네 손가락 모두 성공 0이다. 최종 물리 종료는 guitar displacement 2곡, guitar rotation 1곡이다. 두 정책에서 모두 안전한 **1,021개 ID**로 좁혀도 초기 평균 **3.800195886→최종 0**이므로 세 실패 곡이 전체 감소의 주원인은 아니다.

학습 실행이 100회 정상 완료됐다는 사실과 정책 성과는 구분해야 한다. 이번 관측은 새로운 압현면·tracking 보상을 적용한 최종 정책의 음 달성 회귀이며, 개선 효과는 입증되지 않았다. 두 정책 모두 단계 0에 남았다. 단일 실행의 이 결과로 원거리 보상 감쇠 등 특정 원인을 확정하지 않는다. 이 결과를 근거로 2,000회 확대 실행을 권장하거나 그 효과를 예측할 수 없다.

## 이전 봉인 결과와의 비교

이전 incremental phase의 `result_manifest.json` SHA256은 지정값 `1f743895bd7685e9885ed4264477d581113c3b1ac4c653d6c62f5279c7906f52`와 일치한다. **850개 봉인 파일의 SHA와 크기를 모두 독립 재확인**했다. 파일은 읽기만 했고 옛 소스를 import/실행하지 않았다. `compare_baseline.py`의 역사 Python pin은 봉인 `source_training` 사본으로 해석하고, 나머지 입력은 실제 파일 SHA를 검증하는 방식이 적절하다.

이전/현재 각 initial/final의 원시 첫 곡으로 all/safe 및 교차·실행 내 공통 안전 ID 분모와 달성 평균을 다시 계산했다. 교차 initial 공통 1,023개는 **4.201368524→3.805474096**, 교차 final 공통 311개는 **0.967845659→0**이다. 실행 내 공통 안전 ID는 이전 311개, 현재 1,021개로 서로 다른 집단이다. 같은 ID를 독립 표본 또는 같은 물리 궤적으로 취급하지 않는다.

보존된 contact/clean/success·안전·제어/PPO 계약에 관한 비교와, 달라진 wire 대 press-plane near/surface_min·새 tracking 보상·near curriculum gate 의미를 구분하는 도구의 한계 고지가 타당하다. 동일하지 않은 보상 평균을 우열 지표로 쓰지 않고, 과거 절대 제어 2,000회 점수 8.301을 섞지 않는다. 학습 수집의 변동 확률 정책 결과와 이번 고정 정책 평가도 분리돼 있다.

## 검수 결과 보존

Critical / 수정이 필요한 Warning: 없음. **무결성 PASS는 학습 개선 PASS가 아니다.** 로그의 기존 visual-geom 로드 진단을 native 오류 전무 또는 물리 원인 확정으로 확대하지 않는다. 압력·native contact pair/witness·음향 정확성·네 손가락 도달 가능성은 이 평가로 인증하지 않는다.

- 검수한 `smoke_evaluation_analysis.json` SHA256: `b5665b2f117d1b002bcc5844e837ed7161c11d9eef1ae2b6085e3bd49a70df6b`
- 검수한 `compare_baseline.json` SHA256: `ba9414c350cec7fc687fb9fc99d5eefb88292756ebb8781c17832b02b1cf8298`

이 검수 문서만 새로 작성했으며 작성 종료했다.
