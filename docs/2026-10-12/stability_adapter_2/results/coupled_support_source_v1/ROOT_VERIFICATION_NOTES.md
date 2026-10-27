# Root 확인 — source 검증과 연주 residual 평가 설계

현재 질문의 권장 방향은 **동결된 fret·strike 연주 목표에 공동 residual을 학습해 합성**하는 것이다.
현재 기타 G 기준 연주 정확도와 초기 world p/q 유지를 각각 평가한다.
[추가 계획31행](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:31)에
제어권, [46행](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:46)에 비교 순서를 기록했다.
기존 가중치·관측 정규화·소비된 계획은 보존한다. 학습을 시작한 결과가 아니다.

## 저장 상태 source 검사 결과

팔12+thumb/index/middle single-hinge6 조건부 모델5검사와 검색v3의7검사를 통과했다.
24×11링크=264개 검증의 최대 위치 오차는0.000262701474mm,
회전 오차는7.58811721e−7rad다. 실제 부모 pose와 현재 finger1 상대변환을 공급하는 모델이며
전역 손가락 FK/미래 PD 응답/실제 접촉 인증으로 사용하지 않는다.

4개 baseline+12개 source 제안 중 통과는0.5초 fraction0.25 하나다.
Whole-palm patch 거리 상한9.994144851→9.972901669mm로 감소량은 약21.243µm다.
원본 제출PD base, 비선택63목표, actual/target bounds와 same-left 비인접110쌍을 검사했다.
t0·5초 통과 방향이 없어 실제 PD 실행으로 채택하지 않는다.
[후속 결정](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_SUPPORT_SOURCE_DECISION.md:1)을 따른다.

v1의 t0 PD base 치환과 대표점만의 접근 판정, v2의 same-left 누락은
원본을 보존하고 새 버전에서 해결했다. 이전 버전의 checks=true를 최종 채택 근거로 삼지 않는다.
모델 실행 session31476은 exit0을 관측했으나 전체 stdout을 로컬 로그로 저장하지 않았다.
그 한계는 model_execution.json에 그대로 명시했다. 검색v1/v2/v3는 전체 로컬 로그가 있다.
로그의 plugin preload 경고도 보존한다. Native sim 생성 없이 계산한 exit0이므로
실제 Isaac Gym 물리 런타임 검증을 했다고 주장하지 않는다.

## 그림 실제 QA

Root가 생성된 PNG를 실제 열어 확인했다.16배치의 값은 search_v3.json의
각 LH:palm patch distance upper 최솟값×1000(mm)이다. 시점0/0.1/0.5/5초는
이산 snapshot이고 점을 시계열로 연결하지 않았다. Fraction4개 범례는 중복 없이 표시되며,
유일한 source screen pass의 별표가 맞는 위치에 있다. 모든 데이터가 축 안에 있고
아래 캡션·x축·범례가 겹치지 않는다. CPU source-only 표시와 물리 결과가 아니라는 설명을 확인했다.

![저장 상태에서 계산한 손바닥 patch 간격](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/coupled_support_palm_gap_by_fraction.png)

새 물리 실행·physics step·actor 추론·학습 update는0이다.
README의 Isaac Gym 영상은 이전 LA−2mm 손목 시험이며 이 제안을 실행한 영상이 아니다.
기존 영상 모음126개를 변경하지 않았다.

[독립 수치·설계·그림 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/review.md:1),
[변경 파일 추가 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/CHANGED_FILES_SUPPLEMENT.md:1)을 함께 확인한다.
