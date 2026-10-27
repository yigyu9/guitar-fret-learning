# 자원·준비 상태 분석 진행

- 범위: 두 손별 실행의 읽기 전용 자원 기록, 종료 후 native 재사용·reset 감사 및 모든 초기 준비 상태 비교.
- 학습 코드·설정·모델·원자료·실행 프로세스는 수정하지 않는다.
- `analyze_runtime_v1.py` 작성 완료. 이전 완료 실행의 준비 상태 328개와 worker별 재사용 기록으로 분석 함수를 확인했다. 기존 준비 상태 차이 최댓값과 접촉 집계가 이전 분석과 일치한다.
- 실행기 종료와 canonical `report.json` 최종화를 확인한 뒤에만 `runtime_analysis_v1.json`과 `runtime_verification_v1.json`을 새로 쓴다. 현재 두 실행은 진행 중이며 최종 분석 결과를 생성하지 않았다.
- run마다 서로 다른 네 worker의 현재 RSS/PSS와 부모 메모리를 별도로 집계한다. 공유 host `MemAvailable`은 합산하지 않는다. collection은 reset/step을 포함하므로 중복 합산하지 않는다.
- 모든 `audit_episode_*/initial_values.json`을 worker별 첫 준비 상태와 비교한다. 기타 위치·정규화한 회전·발 위치·관절 q/보고 qd·기타 보고 속도 및 접촉/물리 조건을 구분한다. 이 비교는 solver 내부 상태 동일성이나 정밀 V3 자세 검증을 뜻하지 않는다.

## 종료 분석 완료

- 두 실행의 부모 종료와 canonical report 생성 후 CPU 단일 thread로 분석했다. 프로젝트 import를 위해 `PYTHONPATH=/home/ajou/yigyu/3`을 지정했다. 분석기에 수정은 없으며 입력 SHA가 모두 유지됐다. `runtime_verification_v1.json`의 양 실행 finalization과 analysis integrity는 모두 True다.
- 왼손: 1802.613초, 28업데이트, 14,336전이, 완료160에피소드. 오른손: 1852.662초, 29업데이트, 14,848전이, 완료168에피소드. 둘 다 wall budget으로 정상 종료했다. 1800초 soft budget 대비 초과분은 각각2.613초와52.662초다.
- 왼손 429자원행 중 동일4worker 현재 RSS/PSS 완비426개, 오른손439행 중436개다. 60초 이후 첫 기록→마지막 기록에서 worker RSS 합은 왼손2.447918→2.448387GiB, 오른손2.448925→2.449318GiB였다. 이후60초 OLS는 각각+0.000420/+0.000128GiB/h로, 과거 약+9GiB/h의 증가 양상은 이번 창에서 관찰되지 않았다. 긴 시간의 누수 부재나 인과 비교를 증명하지 않는다.
- 왼손 현재 worker PSS 합은1.654428→1.654898GiB, 오른손은1.655684→1.745705GiB다. 오른손 PSS는 왼손 종료 직전07:13:19.702UTC에1.656077GiB였다가 종료 직후07:13:24.744UTC에1.745705GiB로 바뀌었으며 worker RSS는 두 표본 모두2.449318GiB로 동일했다. 공유 페이지의 PSS 분담 변화와 시간적으로 일치하므로 RSS 증가나 신규 누수로 단정하지 않는다. 최종14개 완비 표본의 오른손 PSS는 같은 값이었다.
- 전체 host MemAvailable 최솟값은23.411205GiB로4GiB 바닥보다 높았다. 왼손/오른손의 겹치는 host 메모리를 더하지 않았다. 각 run4개 worker PID는 서로 겹치지 않는다.
- 각8개 worker 모두 create_sim1/create_env1/load_asset2/destroy_sim1이며 reset 인덱스·누적 초기 상태 쓰기·경계별 쓰기·금지 호출0·native identity·물성 검사를 통과했다. 왼손164준비(41×4), 오른손172준비(43×4), 총336개 준비 상태 모두 삼중 지지·양발 접촉·물리 계약을 충족했다. 완료 학습 에피소드 외의 마지막 준비/진행 에피소드도 포함한 수다.
- 왼손 준비 상태의 worker별 최초 대비 최대 차이는 기타 위치0.422133mm, 회전0.00154869rad, 발 위치0.054810mm, 관절 q0.000983298rad였다. 오른손은 기록된 준비 q/qd·기타 위치/회전/속도·발 위치가 worker별 첫 준비 상태와 모두 같았다. 보고 qd의 절댓값 최댓값은 왼손0.0329479rad/s, 오른손0.0262792rad/s였다. 상태 복원이 실제 운동 정지나 solver cache 동일성을 뜻하지 않는다.
- 왼손 wall 비율: reset48.996571%, step49.354980%, PPO update0.090548%, startup0.042010%. 오른손: reset49.395890%, step49.020142%, PPO update0.092503%, startup0.038914%. collection은 각각98.342132%와98.388634%이며 reset/step과 중첩하므로 더하지 않는다. reset에는2초 물리 준비가 포함된다.
- Torch CUDA allocated peak는 왼손179.196777MiB, 오른손178.906738MiB, reserved peak는 각각228MiB다. 이는 부모 프로세스별 Torch peak이며 장치 전체 사용량·활용률 측정이 아니다. CUDA 정책 부모 두 개가 장치를 공유하며 native physics는 CPU다.
- 종료·worker·cleanup·guard·물리 조건·입력 변경 오류는 모두 빈 목록이다. 보고된 모든 child는 정상 종료했다. 이번 준비 상태 접촉 집계는 학습 중 전체240Hz 접촉 성공률과 별개의 지표다.
