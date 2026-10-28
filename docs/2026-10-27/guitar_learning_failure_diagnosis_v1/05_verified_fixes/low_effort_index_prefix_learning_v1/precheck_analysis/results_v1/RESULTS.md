# 검지 3음 학습 전 실제 대조

| 명령 | source4/7/8 달성률 | 전체3음 달성률 | A release | 음악/해제/AND | 물리/손목실패 |
|---|---|---:|---:|---|---|
| reference | 1.000000, 1.000000, 1.000000 | 1.000000 | 1.000000 | True/True/True | 0/0 |
| zero | 0.000000, 0.000000, 0.000000 | 0.000000 | 0.000000 | False/False/False | 0/0 |
| random | 0.078125, 0.117188, 0.140625 | 0.007812 | 0.070312 | False/False/False | 0/0 |

384첫시도·1152음 모두 실패 포함 원분모다. reference만 학습 진입 판정에 쓰며 zero/random 달성0·실패0을 강제하지 않았다. 원9보상은 episode별 그대로 기록하고 음별로 재배분하지 않았다. 음악과 원native A 해제는 별도이며 AND는 부모 사전계약을 따른다.

env0의 음창별각/목표gap·3마디순힘·손목·팔bounds·CPU6gate·wrong원인은 comparison.json에 보존했다. nearest sample/normalcos와 다른127환경 상세힘은 미저장이며 추정하지 않는다. 실패끝점은 원장과 trace에 남기고 guard의 사전실패와 동일끝점실패를 구분했다.

참고 N 명령은 reference에만 쓰며 zero/random은 NN 초기정책과 다르다. same seed128환경이고 자유기타/J33/원곡67음·자연성의 개선 증거로 확대하지 않는다. 몸체순힘은 접촉쌍압력·토크가 아니고 candidate-off/native release는 피부전체분리 인증이 아니다.

actual source+수치 통합 독립검수 전에는 train gate를 열지 않는다.
