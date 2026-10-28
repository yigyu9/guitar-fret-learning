# 실제 사전 대조의 해석

음악·A 해제·두 기준의 AND는 reference에서 모두 통과했다. 이는 새 정책의 성과가 아니라 참고 명령의 도달 대조다. 세 장면384첫시도·1152음에서 물리·손목 실패는 모두0이며, 실패를 빼거나 zero/random의 달성을0으로 고치지 않았다.

| 명령 | A4/B7/B8 달성/각128 | 세 음 모두/128 | A native 해제/128 | 음악/해제/AND |
|---|---|---:|---:|---|
| reference | 128 / 128 / 128 | 128 | 128 | 통과 / 통과 / 통과 |
| zero | 0 / 0 / 0 | 0 | 0 | 미달 / 미달 / 미달 |
| random | 10 / 15 / 18 | 1 | 9 | 미달 / 미달 / 미달 |

reference의 각음 평균clean은0.99369220/0.99530654/1.0, wrong은 모두0이다. A 원 native 해제 시각은 음 끝 뒤 최소4.70ms·중앙21.37ms·최대29.70ms였다. 이 원 latch는 이전 candidate가 사라진 판정이며 피부 전체 분리나 전환 내내 무하중이라는 뜻이 아니다. 이번 자료에는 기존 release 실험의240Hz 사건·집계가 새로 저장되지 않았으므로 그 재접촉 수를 이번128환경의 측정값으로 옮기지 않는다. B7/8 공유 press/release와 무음 간격도 그대로이며 강제해제하지 않았다.

| env0 명령·음 | 음중60Hz 끝점 | body1/2/3 합력 평균N | 손목 오차 평균mm | candidate/wrong |
|---|---:|---|---:|---|
| reference A4 | 11 | 7.682 / 0 / 0.145 | 0.823 | 11 / 0 |
| reference B7 | 46 | 13.008 / 0 / 0.245 | 0.998 | 46 / 0 |
| reference B8 | 21 | 13.059 / 0 / 0.284 | 1.116 | 21 / 0 |
| zero A4 | 11 | 8.475 / 0.243 / 0 | 1.651 | 0 / 0 |
| zero B7 | 46 | 10.970 / 0 / 2.648 | 14.296 | 0 / 46 |
| zero B8 | 21 | 10.701 / 0 / 2.604 | 14.299 | 0 / 21 |

reference env0의 CPU6gate는 각 음에서 loaded/position/position-facing/positive/candidate가11/46/21개 모두 켜지고 wrong0이다. MCP z의 목표−실제 평균 차이는10.87/10.69/10.70도로 남는다. 높은 음악 성공이 요청각 완전추종이나 손 전체의 낮은 하중을 뜻하지 않는다. zero의 B7/8은 원 A candidate가 음중46/46·21/21로 남았고, index3의 own-wrong-fret와 own-wrong-string CPU flag가 각각 전부 켜졌다. 이것은 저장 env0의 기하·순힘 증거이며 특정 접촉쌍이나 모든128환경의 실패 원인으로 일반화하지 않는다. random env0의 B7/8은 distal 합력이0이고 음중 candidate0이었다. 다른 환경의 상세힘은 미저장이다.

각 조건의 first-attempt guard 관찰은354×128=45,312 control이다. reference는 현재목표A에서 양의DIP증분1,235개를 억제했고 B7/8에서는0개였다. random은 A/B7/B8에서942/920/647개, zero는 전부0개였다. 유한·기존실패·reset·candidate/wrong에 따른 eligibility와 음/영 증분 보존, target memory/scene/observation/rate를 저장 sidecar에서 대조했다. current_goal=-1의 wrong은 안전한 A열 gather값일 수 있어 현재목표 오압현 통계에 쓰지 않았다. report의 전체 episode control 집계와 first-attempt NPZ는 별개다.

원9보상은384 episode의 원 지급값이며 reward−9항 합 최대절대잔차는5.112559392728144e-6이다. 60Hz 기하로 보상을 재지급하거나 음별로 재배분하지 않았다. candidate/wrong CPU 재구성 및 height/distance의1µm 초과 잔차는 이번 env0 세 조건에서0이었다. 미저장 native nearest sample/normalcos, native qd, 다른127환경 상세힘을 복원했다고 주장하지 않는다. 몸체 합력은 접촉쌍 압력·모터 토크·240Hz 최대값이 아니다.

참고 N 일정은 reference에만 주입됐고 zero/random은 비NN 대조다. 같은 seed7의128환경이지128seed가 아니다. 세 음의 조건부 고정 기타 진단으로, 다른 손가락을 제외한 범위·원67행의 선택mask·wrist 안내·0.25Nm/90쌍 조건을 유지한다. strict checkpoint를 읽는 학습/평가는 별도 단계이며 모델/RNG fingerprint를 이번 대조에서 측정했다고 주장하지 않는다. 새 NN의 성공·능동 해제·자연성·자유 기타/J33·전곡 개선은 아직 결과가 없다.
