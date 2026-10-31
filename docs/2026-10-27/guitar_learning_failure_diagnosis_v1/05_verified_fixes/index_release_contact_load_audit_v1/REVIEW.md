# 실제 접촉 하중 감사 독립검수

2026-10-28 **PASS**, actionable finding 없음. 소유한 검수문서만 생성했고 원자료·분석코드·소스·산출물을 수정하지 않았다. 새 GPU/native/NN 실행0이다.

`audit.py` SHA는 요청한 `ff6ccd1cebbd42fad7088ec5c8b79a9477a9e90cc4c0ee713814c813ce275fdc`와 같다. 출력 쓰기를 메모리로 가로채어 CPU에서 읽기전용 재실행했다. 원입력14개 SHA가 전후·현재 모두 같고5개 검사가 재현됐다. `verification.json`은 재실행 결과와 동일하다. `analysis.json`의 count/boolean/string은 동일하고 일부 부동소수점 값297개만 최대7.45058e-9 차이가 났다(가장 큰 항은 nearest gap mm). 판정·분모·결론에 영향이 없는 반올림 수준이며 분석 JSON 전체 byte exact라고 주장하지 않는다.

실행 당시 두 V2 run의 inputs_after가 verified이고, 감사가 읽은 contact/environment/finger_skill_environment/scene 네 소스 SHA가 실제 run pin과 같음을 확인했다. 저장 training contract의 위치·하중·방향 기준도 감사와 일치한다. 원 판정은 동일 표본에서 lateral≤3mm, inset2mm fret cell, signed height[-1,3]mm, facing cosine≥0.1을 함께 통과하는 표본이 하나 이상 있고 distal body norm≥0.01N이며 wrong가 아닌 것이다. 최근접 거리3mm cut으로 잘못 바꾸지 않았다. source_valid128개가 모두 유효하므로 감사의 전체표본 계산이 원valid mask와도 맞는다.

두 조건×세 음의 전체354개 저장끝점에 재구성한 candidate가 원trace와 일치한다. noisy env0 audible78끝점의 누락은 A4/B7/B8 각각1/6/4개이며11개 모두 exported distal body resultant norm이 정확히0N이다. 그11개는 위치·방향을 통과하고 wrong도 아니다. env0..3 A audible44끝점에서15개 누락(환경별1/6/2/6)도 geometry/facing 통과·unloaded다. 해당 surface행은 valid_snapshot이며 post_failure가 아니다. deterministic은 동일env0 audible78끝점과4환경A44끝점에 누락이 없다.

원 source의240Hz substep에서 현재·직전 candidate가 모두 참인 audible overlap만 clean/streak에 적산되고 끊기면 현재streak가0으로 초기화된다. required=min(D,max(0.05,0.4D))에서 문서의0.06812/0.31116/0.13932초가 맞다. release는 ever가 있고 음 끝~끝+100ms 안에서 true→false edge가 생길 때 latch된다. 음 끝 전부터 계속 false인 경우 released가 안 켜질 수 있다는 설명이 맞으며102/128 latch를 나머지26개의 지속압현으로 해석하지 않았다.60Hz 저장만으로 모든240Hz 접촉이력을 복원하지 않았다는 한계도 명시됐다.

scene의240Hz/substeps1/CC_LAST_SUBSTEP, net contact force refresh 및 logical human body 복사, reset force mask 경로를 확인했다. 합력0은 exported resultant의 관측이며 pair-contact 부재·접촉 파트너·현 압력·음향의 직접 인증이 아니다. eligible source plane gap를 실제 cooked collision penetration으로 해석하지 않았고, loaded/unloaded 범위의 겹침과 네축 동시교란을 보존했다. 독립 축부호·under-compressed 확정·필요 preload mm를 추정하지 않은 결론이 자료 범위에 맞는다. 다음 학습/유한 preload 방향은 조건부 제안이며 이 감사에서 검증된 해결책으로 쓰지 않았다.

`review.json`에 원14입력, 실제 run contract/input audit,240Hz caller와 분석 산출물의 SHA 및 독립 확인사항을 기록했다.
