# 전환 실패에서 확인한 범위

이번4환경에서 A(source4)는4/4·clean1/wrong0, B(source7/8)는각0/4·clean0/wrong1이었다. 물리/손목 종료 실패는0이며3음 전체달성은0/4이다. B7단독4/4 도달 기록과 달리, 선택4각을유지한 이번 A→B 이동은 성공하지 못했다. 이는 고정teacher/noNN 조건의 결과이며 B 위치 자체의 불가능 증명이 아니다.

| env0 음창 | 표본 | 선택distal 평균N | 손목 위치/회전 오차 평균 | 원A candidate 표본 | CPU index3 잘못된 fret/string flag |
|---|---:|---:|---:|---:|---:|
| A4 | 11 | 0.146849 | 0.821488mm/0.231189° | 11/11 | 0/0 |
| B7 | 46 | 4.724783 | 17.391050mm/1.927508° | 46/46 | 46/46 |
| B8 | 21 | 1.986223 | 18.025791mm/2.113452° | 21/21 | 21/21 |

B7/B8의 CPU6gate는 각각 `[46,0,0,0,0,46]`/`[21,0,0,0,0,21]`로 assigned distal loaded는 있으나 목표 position geometry·positive candidate가 없고 wrong이 관찰됐다. 원 wrong provenance의 index3에서 own_wrong_fret와 own_wrong_string이 같은 표본에 함께 켜졌으며 other_higher와 다른몸체 원인 flag는0이었다. 이는 저장60Hz actual body/force의 원 helper 재구성이고 native240Hz 원인로그나 특정 접촉쌍 인증은 아니다. 저장 candidate/wrong 불일치 및 height/distance>1µm 잔차는0이었다.

원A candidate는 두 B 음창의 저장표본 모두에서 남았다. 다만 두 음창 사이에는 저장 candidate-off가 있으므로 전체 이동동안240Hz 연속접촉을 주장하지 않는다. A4의 첫 저장 off는 score7.3997/local4.95초로 A end5.62/local3.1703초보다 훨씬 늦으며 원 release의 end후0.1초 창 밖이다. 모든4환경/3음의 원 released=False·release_s=0을 그대로 보존했다. B7/B8의 end후 처음저장 off는 이미False였던 상태의 표본이며 새로 떨어진 전이로 해석하지 않는다. 공유press/release·무음gap에서 강제해제는 하지 않았다.

B7음중 팔 요청/제출target의 Wrist_y 하계 체류는1/46이고 actual Thorax_y가action상계 이상인표본은16/46이다. B8음중에는 요청/target/actual의action경계체류가없었어도 손목 위치오차약18mm가 남았다. 따라서 한축 요청clamp만으로 전체 실패를 설명할 수 없다. 여기서 actual의action구간비교는native물리limit초과판정이 아니다. 전체축의 request−target·target−actual 차이는 comparison.json에 보존했다.

B7/B8의 PIP/DIP 평균actual은각 `[53.9877,23.9995]`°/`[54.1573,23.9728]`°이고 target은 `[54.4847,24.0676]`°였다. MCP_z 평균gap은11.1823°/11.0180°였지만, 별도 B7단독 성공에서도12.6043° gap이 있었으므로 이 gap만으로 실패원인을 확정하지 않는다. 같은손가락의 원A candidate 잔존·잘못된줄/프렛 flag·큰 손목추종오차·변한순힘이 함께 관찰됐다는 범위까지 확인했다. 몸체힘은접촉쌍/현압력이아니며 팔feedback·접촉/마찰·다른관절중 어느기여인지 이번자료로분리확정하지않는다.

다음에는 gap 안에서 유한하게 선택손가락을풀고→손목을옮기고→원reference로닫는 순서를 별도진단으로 검토할 수 있다. 다만 대기각이 실제패드를표면에서떼는방향인지는 기존native또는검증된기하증거부터 필요하며 MCP2축fullFK나임의각도를가정하지 않는다. 이번 단계에서 새grid·속도증가·판정/힘문턱변경·producer수정·추가GPU는없다.
