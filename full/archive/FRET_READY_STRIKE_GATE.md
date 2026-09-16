# Fret-ready·Strike gate

> 상태: **SUPERSEDED**
>
> 이 문서의 기존 atomic chord gate와 공통 고정 deadline 초안은 폐기되었다. 현재 규범은
> [`master_plan/05_synchronizer.md`](../../master_plan/05_synchronizer.md)와
> `tab2body/full/synchronizer.py`다.

현재 G0 규칙의 핵심만 남기면 다음과 같다.

- offline `Canonical PlayEvent`와 하나의 cursor/score clock을 사용한다.
- Fret readiness는 target string의 effective sounding fret이 한 control frame 동안 연속으로 맞아야 성립한다.
- release boundary는 event 중심이 아니라 가장 이른 traversal crossing이다.
- 지연은 configured 최대 2 frame과 다음 event가 허용하는 safe cap 중 작은 값만 사용한다.
- 단일 string이 deadline까지 준비되지 않으면 skip/miss한다.
- multi-string event는 deadline에 준비된 audible target만 점수 대상으로 삼되, 계획된
  traversal 전체는 물리적으로 허용한다. intervening/protected string crossing은 readiness
  분모에 넣지 않지만 motor traversal 완료 판정에는 사용한다. 준비된 audible target이
  하나도 없으면 skip한다.
- 닫힌 gate에서 발생한 crossing은 기록하되 event 성공으로 소비하지 않는다.
- 기타 안정성 판정은 향후 StabilityAdapter/physical task가 제공하며, Synchronizer는 그 certificate를 소비할 뿐 직접 관절을 제어하지 않는다.

현재 구현은 CPU에서 timing/action 계약을 검증하는 단계다. 하나의 Isaac simulator에서
Fret·Strike detector와 common EMA/PD를 연결한 physical `FullG0Task`는 아직 구현 전이다.
