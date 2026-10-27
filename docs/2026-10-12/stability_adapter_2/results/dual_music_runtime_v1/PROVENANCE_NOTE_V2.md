# 실패·후처리 보존 기록

- run_dual_music v1은 CPU10검사에 소비됐다. 독립검수가 빈 recorder.frames cleanup/zone 우회/marker metadata 문제를 발견했고 v1은 수정하지 않았다. v2에서 보완, CPU12 반례를 통과했다.
- v3은 source history 역변환 오차와 COM 속도 상속 범위를 추가했다. 최초 pair100_v3은 Ninja PATH 문제로 scene/attempt 기록 전 import에서 실패해 물리/추론0이다. 해당 로그·빈 출력 디렉토리·CPU source SHA를 보존한다. 같은 입력경로를 상수로 옮긴v4와 PATH 보완 후 pair100_v4에서 실제실행했다.
- analyze_preload_v1은 이전 baseline의human_body_names 필드가 없어 실패했다. 계산 중 입력SHA를 얻었지만 예외 전에 별도 manifest를 저장하지 못했다. 파일은 수정하지 않았으며 최종inventory의현재SHA를 실행시점봉인으로 설명하지 않는다. 새v2가 실제 baseline schema를지원하며 입력SHA/동일초기상태/원자료수치검사를보존한다. 두분석시도는 물리실행0이다.
- preload artifact producer v1은 실행 성공 후 행제목 잘림/제목·범례 겹침을발견했다. 원 producer/PNG/manifest/note를그대로보존하고 소비SHA를대조한뒤 새v2를생성했다. v2 그림만현재설명용으로사용한다. 원본nativePNG는두후처리모두바꾸지않았다.
- 초기보정실행2회와동시연주실행1회가새native3회/3324물리step이다. 기존neutral0는재사용이다. source 추론111tick, 학습업데이트0이며 후처리/CPU검사는native실행집계에서제외한다.

이전산출물보존과main4의append-only검사는final_verification.json에서최종확인한다.

## 마감 시 추가 사항

- 독립검수가 Strike goal/grip 기대SHA 검사가pair v4에없음을발견했다. 실제v4입력은checkpoint와exact일치했다. v5에서document/inputSHA·source action/observation 순서guard를추가하고4CPU검사와native재실행을했다. v4와v5의controls/trace/초기값/음악판정은exact같았다. 마감집계는native4회/4248물리step, 두pair추론222tick,학습0이다.
- pair artifact producer v1은최초validator의문자열117/int117 비교로실패한뒤 같은경로source를수정하고성공했다. 이는실패소스보존절차에서예외다. 실패시별도source/실행SHA가봉인되지않았으므로원tool원문으로재구성한 producer_pair_artifact_v1_failed_reconstructed.py를당시보존원본이나당시SHA검증으로간주하지않는다. pair_artifact_attempt_v1.json에근거/한계를남겼다. 성공v1source/출력은현재manifest로대조한뒤보존했고새v2를생성했다. 이예외는물리/학습결과를바꾸지않는다.
- 산출물README의영문/행동·관측표기문제는실행입력에소비되지않은검토초안이었다. 초안보존후한국어최종문서로정정한다.
