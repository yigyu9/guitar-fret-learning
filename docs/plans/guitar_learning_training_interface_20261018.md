# 자유 기타 학습 인터페이스 구현

사용자가 미구현 관측·음악 목표·타현 판정·보상/비용·종료·네트워크/PPO 연결과 문서화를 요청했다. 현재 Root 고정/하체 유한/105·97·8/자유 기타/준비2초/정책39행동을 유지하며, 검수된 05_BN2-131-B_solo의 명시한 단일음/짧은 구간부터 실제 입출력을 연결한다. 곡 전체 인터페이스도 제공하되 완주 학습 성과를 주장하지 않는다. 장시간 학습은 시작하지 않고 필요한 최소 native rollout/update로 연결을 확인한다.

- [x] 기존 코드와 곡 정본을 확인하고 변경 전 소스/검사를 archive에 봉인한다.
- [x] 음악 목표/누적 이력과240Hz 기타 상대 타현 검출을 연결한다. 실제 압현 후보·목표 후보 소실·기하 타현을 구분한다.
- [x] 명시한 관측 필드/차원/스케일과39출력 계약, 음악 보상·안정성 비용·에피소드 종료를 구현한다.
- [x] 제안한 중간규모 네트워크와 PPO/rollout/체크포인트를 연결한다. 실제 시뮬레이션 자료와 CPU대조를 구분한다.
- [x] 단위/통합검사 및 최소native수집·업데이트를 검수 후 수행한다. 완료된 초기자세 실험은 반복하지 않는다.
- [x] 현재API/차원/단위/보상식/종료조건/네트워크파라미터/실행법/실제결과/남은한계를 문서화한다.

소유권: worker1 음악/타현/측정, worker2 정책/PPO/collector와 해당검사, root 관측·학습환경·CLI·통합/실행·문서와 최종봉인. 검수는 별도change-reviewer. 기존공용자산/과거코드/원자료를수정하지않는다. 변경 전보관→현재import전환→검증→비사용구버전보관원칙을준수한다.

결과: CPU84 PASS. 상태468/행동39/medium1,931,600params, 실제PhysX CPU수집96단계/384표본·reset2회 각2초(총물리5.6초), PPO1update/analyticKL.001617/전후파라미터변화확인. 첫목표시간표완료·strict/lenient0·미스1이며연주학습성과아님. SHA1564개변경0/import누락0/원소스parity오류0. 사전두finding(해제창토큰/새음악wrapper분류)은native전에수정했다. full선택의정본event42 alternate_restrike는명시거부,기본큰행동범위/장기학습/병렬수집/정책하체출력은남은범위다. 현재 문서 [TRAINING](/home/ajou/yigyu/3/guitar_learning/TRAINING.md) · [실제결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/README.md).
