# Root 검증 기록

이번 source batch는 실행 1회·exit0·22.297370119초로 종료됐다. 숫자 제안74개 중 범위 위반6개를 geometry 전에 제외했고68개를 평가했다. Source9검사, 직접 입력72개·동일 SHA 사본72개, 저장 분석11검사를 확인했다. AST 검사는 새 search/wrapper/native adapter/analyzer에 대해 통과했다. Reviewer의 코드 읽기에서 blocker 없음 통지를 받은 뒤 실행했으며 독립 숫자검산은 실행 종료 뒤 완료됐다. 리뷰 문서가 이 순서를 구별한다.

범위 제외는 Thorax_x −.025/−.05와 Thorax_y +.05rad가 seed마다 세 개다. 제외 행은 HG/cross/self 결과가 null이며 raw float32 초기/held 목표와 위반 bound가 있다. 결과가 비어 있는 clear 조건으로 집계하지 않는다. 나머지68개 모두 HG 교차가 남았고, cross/self1188은 clear, palmup 최솟값은0.9255544726258649다. 손가락 상대 계층·upstream pose·비변경 mesh·offset·다른 초기/held 목표 검사는 통과했다. XML Thorax subtree는26body/20collisionbody다.

원 seed에서 최대 HG LP 반경이 가장 작은 조건은 Thorax_y+.025rad의2.212092533120751mm다. Wrist_y−.1rad seed에서는 Thorax_z+.025rad가1.2315757769876514mm로 가장 작지만 palm–G1.0795155131835124mm를 포함한5쌍이 남는다. Thumb2–G 보고 pair가 없는10조건도 다른 HG pair를 남긴다. 이것은 시험한 조건에 대한 관측이며 전체 가동범위의 불가능성을 뜻하지 않는다. LP 공통내접반경을 PhysX 침투 깊이나 접촉 거리로 해석하지 않는다.

Clear 후보가 없어서 proposal/source_prediction/native/native_execution은 생성하지 않았다. 새 native 초기화·physics·actor·학습은0, 이번 조건의 실제5초 안정성은 미측정이다. 기존152개 영상과 이전 산출물은 보존한다. 산출물 도표는 저장 source 계산이며 실제 Gym 렌더가 아니다. 이전 실제 초기 프레임을 재사용할 경우 실행 출처를 명시한다.

다음 단계는 SOURCE_HAND_ARM_CONTINUOUS_PLAN.md의 bounded 조합 탐색이며 아직 미실행이다. ±.15rad arm12/두 seed/총800평가/한 actual 검증 상한, 기타 fullstate·고정 LA·PD·몸통9목표·root하체·최종66권한, 기타고정/손부착/post-start state 덮어쓰기 금지를 유지한다. Source-only 호환과 임시 지표를 본래 자유 기타 안정화·물리 보정·연주 전환의 성공으로 승격하지 않는다.

최종 봉인은 source/artifact/analysis 전후 SHA, 독립 review, main3문서 prefix 보존과 이전 선언 파일·영상 보존을 확인한다. 봉인 실행의 stdout을 phase 내부 열린 로그로 수집하지 않아 미완료 로그 SHA를 inventory에 넣지 않는다. Producer 원문과 invocation은 실행 전에 복사·SHA 대조한다.

Root가 실제 arm_source_geometry.png를 열어9panel·모든 y값 포함·두 seed baseline·원자료 단위와 범례/캡션 가독성을 확인했다. 그림은66개 비baseline 점과2개 seed baseline의68계산조건을 표현한다. 공유 x축 formatter 때문에 producer가 의도한 tick의 † 문자는 표시되지 않는다. 제외는 NaN 공백이며 Thorax X−.05/−.025와Thorax Y+.05가두seed에서각각빠져있다. README와누적설명에정확한위치를명시하고소비된그림/producer를재생성하지않는다. 값의누락/0위장/데이터불일치는아니다.
