# V7 실제 후기 실행·분석 독립 검수: PASS

이 PASS는 실행 원자료와 계산의 정확성에 대한 검수다. 원래 학습 수용 기준을 통과했다는 뜻은 아니다. 마지막 V7 평균행동·확률 평가의 stage_ready는 모두False다. 영상은 별도 검수 범위다.

구현 비참여 peer가 실제 Python3.8 CPU에서 원자료를 읽고 재계산했다. 원672개 core 입력을 포함한 source/input/output SHA는 전후 일치한다. 추가 GPU·Isaac·native·NN forward·model 생성·checkpoint 역직렬화/재개는0이며 checkpoint는 SHA만 읽었다.

PPO 감독 프로세스의 PID/startticks·argv·허용 환경·입력 및 exit0/terminal, 실제 run의 completed/closed/실패·cleanup·입력변경 없음을 확인했다.300개 update와1,228,800전이,3456완료 episode의1,223,424전이와5376열린 전이를 검산했다. 변하는 학습정책의 완료 episode all3=1132/joint685는 고정 저장본 평가 성과와 구분한다.

V6/V7 전체18개 평가에서 원128개 고유 환경·384음,mode/update/checkpoint SHA·모델/optimizer freeze를 확인했다. 원 episode JSON으로 all3/joint/A해제/실패/보상·비용과 음별 달성·해제·clean/wrong/missing/최장streak·9보상 평균을 직접 재합산했다.9보상과 A 정산 보존도 검사했다. 각 버전300지표의 실제 비용과 cost advantage/value/target/loss는 전구간 정확0이다. KL 재시도는 첫 update의2회이며 실제 actor LR는1.875e−6이었다.

|마지막300|A/B7/B8 달성|all3|joint|A 해제|
|---|---|---:|---:|---:|
|V6 평균행동|0/128/128|0|0|0|
|V7 평균행동|110/18/19|13|5|13|
|V6 확률|2/10/7|0|0|1|
|V7 확률|60/100/100|58|30|60|

분모는 각128시도다. V7 평균행동 B7/B8 오압현 평균은각0.7421875이며 확률은약0.02340/0.02344다. V7의 A 오압현은 두 mode에서0이지만 다른 음의 간섭과 해제·동시성 문제가 남아 있다. 원90% 달성/clean/all3/해제와 오압현10% 이하 기준을 재계산했으며 마지막 두 mode 모두 통과하지 못했다.

확률 결과는 V6의 마지막0/0과 V7 자신의 초기14/12보다 개선됐지만 평균행동13/5는 자신의 초기98/22보다 낮다. 마지막300을 점수와 무관하게 유지했고 좋은 중간 모델로 교체하지 않았다. 이를 전체 성공이나 단일 원인의 일반적 효과로 해석하지 않는다.

analysis/results의 source/입력·출력 SHA와 성공 verification을 확인했고3개 그림을 각각 직접 열어 축·범례·척도·표와의 일치를 검사했다. 고정 평균행동 곡선,9보상 평균,0비용 신호와 실제LR/KL가 원자료와 맞는다. 전체 holdout 가치오차 개선과 tail 악화, 같은 장면 환경분할·실현 MC의 한계도 결과에서 보존한다.

미해결 원자료/계산 검수 지적은 없다. 상세 SHA와18개 재계산 값은 actual_final_review.json에 기록했다. 영상은 별도 reviewer 대상이며 다른 seed·손가락·자유 기타/J33·원67음 목표는 미완료다.

SUMMARY.md의 수치·예산·생산 미채택 판단·미구현 다음 진단 분기도 원자료와 대조했다. 외장 원본3개 재읽기는 root 보고이며 영상 관련 진술은 이 검수의 범위가 아니고 별도 reviewer/status가 기준이다.
