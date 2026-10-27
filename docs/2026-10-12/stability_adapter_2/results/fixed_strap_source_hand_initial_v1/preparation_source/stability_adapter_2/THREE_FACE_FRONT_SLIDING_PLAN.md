# 넥 전면에서 손가락 위치 이동을 허용하는 초기 배치

검지·중지8 초기각을 더한25좌표 검색의 세 후보도 모두 source 교차로 제외됐다. 엄지 오차5.648908~8.808955mm/손바닥7.766016~11.664586mm였다. 초기 손바닥 목표는 기존 anchor에서 GY +17.294243mm 이동을 요구하지만, 두 fingertip의 전면 목표XY를 기존 초기 위치로 유지한 항은 손의 이동을 방해할 수 있다. 이는 현재 항 설계의 가능한 충돌이며 실패의 단독 원인으로 확정하지 않는다.

다음 variant는 이전 소비source를 exact SHA 대조·보존한 후 별도 경로에서만 진행한다.

- 팔12·엄지5·검지/중지8의 같은25좌표 및 bounds, 나머지56초기각, 절대81목표/G p·q/LA/gain/solver/material, thumb1462·clearance0.3mm/palm 목표와 모든 기존 hard gate는 그대로 둔다.
- 전면 목표는 각 source FK 평가의 현재 fingertip GXY에서 넥 전면 허용영역(X끝3mm,Y끝5mm 여유)으로 제한한 점이다. 높이는 source 전면 바깥11.230006mm +0.3mm다. 영역 안에서는 X/Y 방향 이동을 제한하지 않고 표면 접근과 source 법선 방향만 부드럽게 선호한다. 약지·소지 초기각은 유지한다.
- 저장 half, 앞25좌표 검색의 previous_near 결과, 새 projection task residual의12×25 선형 추정값 세 개를 비교한다. 선형 행렬은 point motion Jacobian이 아니라 **task residual derivative**이고 전면XY 항은 현재 지점을 따라 이동한다. 투영 경계 밖의 이동 항과 전면 높이 항을 구분해 기록한다.
- 전체 교차/상향조건/엄지·손바닥 유한 패치와 거리구간/후면 witness 검사로 source 통과를 결정한다. 전면 soft 접근만으로 실제 grip 성공을 주장하지 않는다. 통과 후보 최대2개 actual5초와 초기값/전신·손151frame을 기록하며, source에서 모두 거절되면 native0이다.

독립 검수 도구 한도 오류는 아직 해결되지 않았다. Root 사전 자체검증과 결과 재계산을 완료한 뒤 독립 검수 보류 범위를 별도로 기록한다. 기타 자유 물리 및 최종양쪽66 권한,몸통9 목표/root하체 물리고정/기타고정·손부착·반복pose 덮어쓰기 금지는 유지한다.

- [ ] source 입력 보존·12×25 residual derivative·같은25 bounds 사전 검증
- [ ] 세 source후보/통과최대2actual5초
- [ ] 이미지·설명·자체 검증·보존/독립검수 상태
