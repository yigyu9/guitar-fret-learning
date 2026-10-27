# 안정성 우선 pilot 런타임 독립 검수

요약 판정: **문제없음.** 완료된 초기 평가·정책 이관·실제 PPO 갱신 증거와 설명이 일치한다. 장기 학습 완료·안정화 성공·음악 성공·production reward 인증은 검수 대상이 아니다. 검수자는 저장된 파일의 읽기 전용 분석과 CPU 체크포인트 tensor 대조만 수행했으며 추가 물리 실행·추론·학습은 하지 않았다. 이 새 보고서 외 파일은 변경하지 않았다.

## Critical

없음.

## 확인 사항

- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/README.md:9)와 [검증 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/verify_priority_runtime_v2.py:46)는 위치 −8/초·회전 upper proxy −4/초·60 Hz 적분을 구분한다. 저장된 ON454개/OFF982개 controls로 독립 재계산한 최대 ledger 오차는 각각 약4.44e−16/1.11e−16으로, NumPy producer의 오차0 기록과 부동소수점 허용 범위에서 일치한다. scaled 합과 native return의 차이도 최대4.27e−14였다. 전체 scalar가4배라는 주장은 없다.
- [runtime 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/runtime_verification_v2.json)의 producer SHA와 입력12개 SHA를 현재 파일과 독립 대조했고 동일했다. 두 초기 CP를 원본 CP와 CPU tensor로 대조해 Actor·log_std·RMS를 포함한 모든 noncritic tensor exact, 기존 Critic과 새 Critic의 값 차이, 빈 Adam, updates/transitions0을 확인했다. Critic의 fresh 초기화 방식은 [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/review_preflight_v1.md)에 확인되어 있다.
- 검증 snapshot의 ON6회/1536전이·OFF1회/256전이와 같은 UTC의 실제 training 로그 행이 각각 존재했고 `optimizer_steps=1`이었다. 이는 새 보상에서 실제 PPO 갱신을 했다는 증거다. 진행 중 append 로그 전체가 동결되었다는 뜻은 아니다.
- [초기 결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/README.md:28)은 새 보상 학습 전 이관 정책의 결과임을 밝힌다. ON은1816physics/454control/7.5667초에서 `R_Elbow_y` 실제 속도99.6634903rad/s로 안전 종료했고 음악 성공0·정산15이벤트였다. OFF는3928physics/982control/16.3667초의 계획 구간을 끝냈지만 음악 성공0·정산42이벤트였다. 저장 controls에서 재계산한 control-endpoint 위치 이탈률53.524229%/95.112016%가 설명과 일치한다.
- 완료 초기 평가의 native report는 baseline 불변·금지 API 없음·입력 불변을 기록한다. 실제 force call은 ON23,608=13×1816, OFF0이었다. 영상4개의 SHA를 독립 확인했다. capture는 ON228프레임의0→1816physics, OFF492프레임의0→3928physics를 기록하며 마지막 실제 종료까지의 영상이다. README에 쓰인 ON t0/종료 PNG를 직접 열어 기타 배치와 마지막 지지 상실 장면을 대조했다. 케이블 경로 투영을 천 스트랩 mesh로 설명하지 않는다.
- [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/CHANGED_FILES.md:5)의 절대 링크·실제 줄 번호와 네 main 추가 기록 시작 위치를 확인했다. README의 절대 이미지/MP4 링크도 존재한다. main 및 전체 과거 파일의 최종 봉인은 root 담당이며 이 보고서는 그 완료를 대신 인증하지 않는다.
- [최초 실패 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/runtime_verification_v1_failure.json)은 NumPy bool 직렬화 실패와 결과 파일 미생성을 명시한다. 보존된 v1→v2 diff는 checks의 Python bool 변환과 새 출력 경로만 바뀌었고 측정 수식은 같다. v2는 offline 분석이며 물리·학습을 추가하지 않는다.

## Warning

새 수정 요구 없음. [README:35](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/README.md:35)의 ON 조기 종료 검열과 ON92/OFF127 출발 이력 때문에 이탈률을 스트랩 효과나 보상 개선으로 비교할 수 없다. [README:51](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/README.md:51)는 마감을 비선점 호출의 hard deadline으로 인증하지 않고, 진행 중 학습과 pilot 한계를 구분한다. 이 제한을 최종 사용자 설명에서도 유지해야 한다.

## Suggestion

없음. 후속 성능 판단은 새 보상 갱신 후 완료된 별도 평가와 최종 실행 상태에 근거해야 한다.
