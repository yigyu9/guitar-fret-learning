# V6 분석 준비 코드 독립 검수

**요약 판정: 문제없음 — 코드·준비 범위에 한정.**

Critical / Warning / Suggestion: 확인된 항목 없음.

- `analyze.py:11–18`: 봉인 V5 helper SHA를 import 전에 확인한다.
- `analyze.py:61–116`: 실제 초기 평가의 모드·128시도·384음·원장·freeze·계약·checkpoint를 검사하고 CPU 텐서로 fresh/fit의 69+2 차이를 재확인한다.
- `analyze.py:68–99`: cost weight 1과 4096개 유한 표본을 요구하고 비용 advantage/value/target/loss의 정확 0 여부를 별도로 기록한다. 양의 실제 비용을 신호 0으로 추정하지 않는다.
- `analyze.py:197–232`: 양쪽 PPO300 및 각각 9평가의 파일·완료 보고를 선행 요구하며 최종 검증 파일이 있으면 덮어쓰기를 거부한다. 입력 SHA를 전후 비교한다.

실제 `rl38` Python 3.8.20, `CUDA_VISIBLE_DEVICES=''`에서 기존 16검사를 독립 재실행해 모두 통과했다. 재실행의 `cpu_verification.json` 쓰기는 메모리로 가로채 기존 증거를 보존했다. 초기 실제 4평가와 fresh/fit 텐서를 읽었다. 최종 checkpoint 누락을 모의한 진입 차단과 임시 디렉터리의 합성 보고·3그림 생성 연결도 통과했다. 합성 출력은 삭제했으며 성과 증거가 아니다. GPU·NN 실행 0회, 실행 중 PPO 로그 읽기 0회.

검토한 `analyze.py` SHA256: `3b5a5d7ed944e865ffc5b8f7d7a5af5da8fe756dca3882221de6dc9b54b38eec`.

이 판정은 최종 학습·평가 결과 승인이나 개선 주장에 해당하지 않는다. 모든 최종 입력 완료 후 분석을 실행하고 그 시점 소스/산출물 SHA 및 실제 그림 3개와 최종 영상은 별도 검수해야 한다. 전체 runtime/생산 코드 pin 재검사는 이 분석 준비 검수의 범위가 아니다.
