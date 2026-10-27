# 검지·중지 초기각 소단계 실행 계약

[기본 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FRONT_FINGER_INITIAL_PLAN.md:1)은 그대로 보존한다. 직전 near 검색 source SHA를 실행 기록과 대조해 새 phase에 exact 복사했다. 이전 source·결과·그림·문서 및 공용 모델은 수정하지 않는다.

- 초기각 범위는 팔12 ±0.05rad, 엄지5 ±0.20rad, 검지·중지8 ±0.10rad의25좌표다. native/Aug19 손가락 한계, 팔 C02 ±0.30rad, 기존 절대 PD 목표 차이 ±0.30rad의 교집합과 float32 제출 가능 범위를 적용한다. 나머지56 초기각과 절대81 PD목표/G world p·q/LA1.1018469719600776m/gain/solver/material은 유지한다.
- 후면 엄지 지점1462, 목표 간격0.3mm, 후면패치 왼쪽 변의2mm inset +0.5mm 여유, 기존 손바닥 목표(GY45mm/GZ4.5mm)를 유지한다. 검지·중지의 기존 source facet 지점은 초기GXY에 가장 가까운 넥 전면 안쪽(X경계3mm,Y끝5mm 여유)과 source 전면 바깥높이11.230006mm +0.3mm를 부드럽게 선호한다. 선택 facet 방향은 −GZ를 부드럽게 선호한다. 약지·소지 초기각은 고정하며 기존 source 높이를 부드럽게 유지한다.
- 초기 추정값3개는 저장 half q81, 직전1462/0.3mm 후보 q81, 네 지점12×25 source Jacobian의 bounded 선형 fit이다. 선형 추정은 기존 범위 안의 source 초기 추정값이며 실제 자세/접촉/지지 성공이 아니다. 각각 독립 후보로 기록한다.
- 기존 검지·중지의4 source 겹침 쌍에 대한 face-plane 분리 항을 유지한다. 전체human–guitar/양손/비인접왼손의 최종 LP 교차 검사와 손바닥 위쪽 반구, 엄지·손바닥의 유한패치 여유/거리구간/후면 지지 방향 검사를 유지한다. 검지·중지 전면 접근은 이번엔 soft 항이며 별도 실제 접촉 증거 없이 세 면 grip 성공으로 판정하지 않는다.
- 통과 후보가 있으면 중복 q를 제외해 최대2개 actual5초 실행한다. 초기값·actual81q/Gp·q/velocity/PD/physics/strap, 전신·손0~5초151frame30fps를 기존 runner로 남긴다. 통과0이면 source거절 기록만 남기고 새 native실행0을 명시한다.

사전 독립 검수와 이전 결과·그림 최종 검수 재시도를 요청했으나 에이전트 도구가 `agent thread limit reached`를 반환했다. 이번에는 root가 문법, 이전거리helper 동일성,25좌표 bounds/추정값/목표 일치와 저장 결과의 기하를 자체 검증한다. 독립 검수 완료로 표시하지 않으며 다음 작업 단위에서 다시 시도한다.

최종 양쪽66 제어권/몸통9 목표/root하체 물리고정/자유기타·중력·충돌·수동strap은 같다. 기타 고정·강제 손 부착·반복 pose 덮어쓰기·기타목표 힘은 없다. 초기 배치 후 손가락 목표를 바꾸는 실제 유지 제어 비교는 별도 소단계다.
