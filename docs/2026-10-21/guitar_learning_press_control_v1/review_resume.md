# 100→101 실제 재개 독립 검수

요약 판정: **문제없음 — checkpoint 복원·추가 업데이트·구계약 거부 범위 PASS.** 정책 성능 개선 또는 중단된 물리 궤적의 연속 복원을 의미하지 않는다.

## 범위와 검증 방법

`resume_verification.json`, `verify_resume.py`, 실제 smoke100/final 및 smoke_resume1/initial/final checkpoint, fresh initial checkpoint, 입력 pins, 설정·계약·report·종료 scene·journal/raw gzip, 재개 GDB/검증 로그와 프로세스 결과를 확인했다. 새 Python 프로세스에서 CUDA를 숨기고 checkpoint를 CPU로 읽어 독립 비교했다. `verify()`도 파일 출력 없이 CPU에서 재검사해 저장된 검증 JSON과 결과 전체가 동일함을 확인했다. GPU·GL·영상·N4 ablation은 실행하거나 검수하지 않았다.

## 확인 결과

- 선택된 smoke100/final과 재개 직후 initial은 **metadata를 제외한 전체 tree가 바이트 수준으로 동일**하다. identity/model/양 optimizer/cost weight/update counter/Python·NumPy·Torch·CUDA RNG payload가 포함된다. 비교는 dtype·shape 및 tensor 원시 byte를 확인했다.
- selected/initial은 업데이트 **100**, 최종은 **101**이다. 최종 모델 56개·actor optimizer 54개·value optimizer 57개, 총 **167개 tensor가 finite**다. 왼손 actor 17개 및 value 관련 19개 tensor가 바뀌었고 두 optimizer 상태도 실제로 갱신됐다.
- 비활성 오른손 actor 17개 tensor, 오른손 log_std 여섯 축, 해당 Adam moment tail이 보존됐다. fresh initial→최종 및 재개 initial→최종 대조가 일치한다. CPU 검증기의 partner 상태 보존 검사도 통과했다.
- curriculum은 **3,331개 float64** 상태로 복원되며 유효성 검사를 통과한다. 이번 추가 32 control tick에서는 종료 곡이 없어 최종 curriculum도 initial과 같다. 이를 새 episode에 의한 진급 검증이라고 부르지 않는다.
- 실제 GPU runner가 strict load한 뒤 추가 **1회 / 32,768전이**를 수행했다. report의 optimizer 101, local update 0, native GPU1024 및 정상 종료 scene이 일치한다. 물리 **128 step**이고 simulator는 닫혔다. GDB 정상 inferior 종료와 프로세스 exit 0이 확인된다.
- 재개 raw gzip은 CPU에서 끝까지 읽어 **32행**의 local update 0 / tick 0..31을 확인했다. journal sampled/logged/durable/committed는 모두 32,768이고 discarded/pending은 0, 정상 closed 상태다.
- smoke **580개**, 재개 **581개** 현재 입력 SHA를 직접 대조했다. 재개 입력은 실제 선택 smoke100/final SHA를 필수로 포함한다. 두 실행의 계약·PPO·곡·초기 std·large/N1024/H32/left/seed 설정은 같고 요청된 추가 업데이트 수만 1이다.

## 이전 동일 codec checkpoint의 거부

이전 incremental smoke100/final은 모델 차원/역할과 누적 제어 codec이 동일하지만 reward v3 및 surface observation v1이다. 새 실행은 reward v4 / surface observation v2다. 이전 파일은 실제 `PPOTrainer.load`의 **identity equality guard**에서 거부된다. 이 guard는 모델·optimizer·RNG 설치 및 CUDA topology/RNG hook보다 먼저 실행된다.

CPU 재검사에서 그 거부 사유와 모델·양 optimizer·counter·cost weight·host RNG 무변경, CUDA hook 미호출이 다시 확인됐다. 이는 source SHA만 보고 거부한 검사가 아니며, 동일 tensor 차원·동일 codec이라도 달라진 목표·보상 의미의 checkpoint를 이어 쓸 수 없다는 계약을 검증한다.

## 해석 한계

새 CUDA checkpoint를 CPU `PPOTrainer.load`로 정상 복원했다고 주장하지 않는다. 새 strict load의 실제 증거는 GPU runner 실행과 그 직후 initial snapshot이다. CPU 도구는 모델/optimizer 직접 binding과 payload 비교를 수행하며 CUDA RNG를 GPU generator에 설치하지 않는다. CUDA RNG **저장 byte의 정확한 복원**과 실제 generator 설치/새 물리 궤적 동일성은 구분한다.

재개는 prepared pose의 새 물리 episode에서 시작한다. 중단 시점의 q/body/contact 궤적 복원이나 완전히 연속된 물리 실행을 인증하지 않는다. 기존 visual-geom 시작 진단을 원인 해결로 해석하지 않는다. 이 PASS는 앞선 고정 0/100 정책의 음 달성 회귀 판정을 바꾸지 않으며 압력·음향·일반화 성과를 의미하지 않는다.

Critical / 수정이 필요한 Warning: 없음.

검수한 `resume_verification.json` SHA256: `80b771a734bc44fdae7caa5ce96473569c4ca1aebc1e5fbb471a1a99c9f0d608`.

이 문서만 새로 작성했으며 원자료·활성435소스·기존 도구 변경 없이 작성 종료했다.
