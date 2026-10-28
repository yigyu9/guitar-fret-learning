# 음악성과와 중간해제의 구분

같은고정기타/noNN4환경에서원닫힌이동prefix는A4/4·B7/B8각0/4였고, 이번staged일정은세음각4/4·clean1/wrong0·물리/손목실패0으로전체4/4였다. 원67행/선택3음·음시계·.70/.10수용기준·9보상은그대로다. 다만손가락일정과Cartesian목표이동속도66.8405mm/s(기존44.6176의1.498배)를함께바꿨으므로개선을해제하나의분리된인과효과로확정하지않는다.

A의원native released는4환경모두True이고score release_s는 `[5.6413666667,5.6413666667,5.6705333333,5.6372]`초다. 최초candidatefall clock은 `[766,766,773,765]`로A end후약 `[21.37,21.37,50.53,17.20]`ms이며원end+.10초창안이다. 이때candidate와assigned-loaded는모두False였다. env3의distal순힘은0.007093N,나머지3환경은0이었다. 이는원candidate/load기준사건이며피부전체분리/다른접촉해제나실제현압력을인증하지않는다.

N을유지하며wrist를이동한106개native끝점에서는원A candidate·assigned-loaded가각환경 `[22,22,28,26]`개에서다시관찰됐다. B7/B8의wrong계수도각각같은개수였지만집계만으로240끝점별일치를독립재생한것은아니다. 이동중distal합력최대는각 `[4.347076,4.278462,4.390571,4.829537]`N이었다. 따라서N이이동구간내내무하중을유지했다고말할수없다. 다음ref복귀구간29개native끝점에서는4환경모두candidate/loaded/wrong0·distal최대0이었다. 이계수는핀된원observer의bounded240집계를그대로대조한값이며,저장하지않은240전체표본이나연속접촉구간을독립재생한값이아니다.

| env0 음중 | 기존닫힌이동 | staged |
|---|---:|---:|
| B7 wrist평균 mm/° | 17.391050 / 1.927508 | 1.005731 / 0.473061 |
| B8 wrist평균 mm/° | 18.025791 / 2.113452 | 1.094760 / 0.300778 |
| B7 distal평균N | 4.724783 | 0.242059 |
| B8 distal평균N | 1.986223 | 0.296612 |
| B7 proximal1평균N | 10.505933 | 12.994020 |
| B8 proximal1평균N | 9.705799 | 13.072027 |

staged의B7/B8음중CPU6gate는각46/21표본모두loaded/position/position_facing/positive/candidate이며wrong0이었다. 같은B음창의원A candidate는0/46·0/21로,기존46/46·21/21잔존과달랐다. 저장candidate/wrong과CPU복원불일치0·height/distance>1µm잔차0이다. 가까운패드샘플tie·native sample/normalcos미저장한계는원래대로남는다.

B7에서PIP/DIP평균actual은54.371546/23.949286°,B8에서는54.451832/24.061304°로원target54.484707/24.067577°를추종했다. MCP_z target−actual은아직10.691669/10.699687°였다. B7음중Wrist_y요청/target하계체류는46/46이지만actual팔의action경계체류는0이었다. B8음중요청/target/actual경계체류는0이었다. 요청경계와실제관절·손목추종·가동범위해결을혼동하지않는다.

B7/B8의원released는여전히모든환경False/0이며공유press/release·무음gap에서새강제해제를넣지않았다. 최종음악성공을전체음의자연스러운release나음향성공으로확대하지않는다. distal하중은낮아졌지만proximal1은증가했고body순힘은pair압력·motor effort가아니다. 원cap0.25 readback을손전체저하중보장으로부르지않는다. 이번결과는유한명령/teacher조건의3음진단이며NN학습·자유기타/J33·전곡·자연성·생산채택은미완료이다.
