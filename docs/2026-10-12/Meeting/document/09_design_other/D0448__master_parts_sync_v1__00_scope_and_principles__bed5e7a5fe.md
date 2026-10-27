# 00. 범위와 설계 원칙

## 목적

이 문서는 각각의 모델을 구현하기 전에 연구 전체의 경계를 고정한다. 오디오 해석, 음악 이벤트 생성, 손별 motor skill, 양손 timing, 기타 안정화를 하나의 학습 문제로 섞지 않고 계약이 있는 단계로 나눈다.

## 시스템의 최종 정의

`FullBodyPlayer`는 다음 조건을 동시에 만족하는 runtime 시스템이다.

```text
음악 event를 올바른 시간에 실행
AND 왼손 압현 상태가 유효
AND 오른손 pick/strum event가 유효
AND 기타의 자세·접촉·미끄러짐이 허용 범위
AND 관절·접촉·물리 안전성 통과
```

평균 reward 하나로 이 조건을 대체하지 않는다.

## 연구 경계

### 포함

- 오디오 또는 주어진 annotation에서 기타 tablature 생성
- tablature에서 왼손 finger mapping 생성
- tablature와 연주 형태에서 picking/strum plan 생성
- Fret/Strike skill prior 학습
- 공통 event timeline과 양손 timing 조정
- 자유 기타의 지지·안정화·기존 기술 보존
- 동일 구조를 여러 곡에 적용하되 checkpoint는 곡별로 독립 학습·평가

### 기본 범위에서 제외

- raw waveform을 매 physics step에서 직접 해석하는 end-to-end actor
- 기타 소리를 완전한 음향 합성으로 재현하는 문제
- hammer-on, pull-off, slide, bend 등 별도 왼손 onset·연속 pitch 모델이 필요한 특수 주법
- 인간 전신 balance까지 포함한 자유 보행
- 물리·event 입력 없이 곡의 event index만 조회하는 lookup-table식 policy

인간 root와 하체를 풀어야 하는 전신 균형 연구는 현재 seated upper-body 범위와 별도 physics/action 계약으로 둔다.

## 기준 설계 원칙

1. **데이터 의미와 관절 제어를 분리한다.** 음악 event는 관절 action이 아니다.
2. **공통 시간축은 하나다.** Fret과 Strike가 같은 event를 서로 다른 clock으로 진행하지 않는다.
3. **좌표계는 목적별로 나눈다.** 손의 연주 geometry는 guitar frame, 지지와 안정성은 body-relative frame, 중력은 world/gravity frame을 사용한다.
4. **실행 결과가 의도보다 우선한다.** policy가 strike를 의도했더라도 detector가 crossing을 확인하지 않으면 성공이 아니다.
5. **기존 기술 보존을 먼저 측정한다.** 새 adapter가 안정성을 높였더라도 Fret/Strike 성능이 무너지면 승급하지 않는다.
6. **새 권한은 작은 범위에서 연다.** 손가락보다 proximal arm, proximal arm보다 몸통 순서로 확장한다.
7. **물리 mode 변경은 checkpoint migration이다.** fixed guitar와 free guitar를 같은 episode 안에서 단순 toggle하지 않는다.
8. **모든 실험은 baseline과 paired evaluation을 가진다.** 같은 event, seed, 초기 상태에서 source와 composition을 비교한다.

## 설계 상태 표기

문서의 상태는 다음을 사용한다.

| 상태 | 의미 |
|---|---|
| `PROPOSED` | 설계 제안. 코드·성능 검증 전 |
| `CONTRACTED` | 입력·출력·단위·버전이 문서로 봉인됨 |
| `IMPLEMENTED` | 코드가 존재함 |
| `VALIDATED` | 명시된 통과 조건과 자동 검증을 통과함 |
| `BLOCKED` | 외부 결정 또는 물리 모델 부족으로 진행 불가 |
