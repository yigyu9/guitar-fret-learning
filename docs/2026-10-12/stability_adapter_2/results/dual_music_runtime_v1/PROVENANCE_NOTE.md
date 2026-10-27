# 실패·후처리 보존 기록

- run_dual_music v1은 CPU10검사에 소비됐다. 독립검수가 빈 recorder.frames cleanup/zone 우회/marker metadata 문제를 발견했고 v1은 수정하지 않았다. v2에서 보완, CPU12 반례를 통과했다.
- v3은 source history 역변환 오차와 COM 속도 상속 범위를 추가했다. 최초 pair100_v3은 Ninja PATH 문제로 scene/attempt 기록 전 import에서 실패해 물리/추론0이다. 해당 로그·빈 출력 디렉토리·CPU source SHA를 보존한다. 같은 입력경로를 상수로 옮긴v4와 PATH 보완 후 pair100_v4에서 실제실행했다.
- analyze_preload_v1은 이전 baseline의human_body_names 필드가 없어 실패했다. 계산 중 입력SHA를 얻었지만 예외 전에 별도 manifest를 저장하지 못했다. 파일은 수정하지 않았으며 최종inventory의현재SHA를 실행시점봉인으로 설명하지 않는다. 새v2가 실제 baseline schema를지원하며 입력SHA/동일초기상태/원자료수치검사를보존한다. 두분석시도는 물리실행0이다.
- preload artifact producer v1은 실행 성공 후 행제목 잘림/제목·범례 겹침을발견했다. 원 producer/PNG/manifest/note를그대로보존하고 소비SHA를대조한뒤 새v2를생성했다. v2 그림만현재설명용으로사용한다. 원본nativePNG는두후처리모두바꾸지않았다.
- 초기보정실행2회와동시연주실행1회가새native3회/3324물리step이다. 기존neutral0는재사용이다. source 추론111tick, 학습업데이트0이며 후처리/CPU검사는native실행집계에서제외한다.

이전산출물보존과main4의append-only검사는final_verification.json에서최종확인한다.
