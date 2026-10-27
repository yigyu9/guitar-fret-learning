# 정책 준비 구간 전환 독립 검수

**최종 판정: 문제없음.** 최종 접촉시간 보상 버전의 코드·CPU·초기 실제 평가·PPO 연결·저장 모델 평가와 최종 문서를 검수했다. 미해결 Critical·Warning·Suggestion은 없다. 구현 소스와 기존 결과는 수정하지 않았으며 이 보고서만 작성했다.

## Critical / Warning / Suggestion

현재 확인된 미해결 항목 없음. 구현 동작이 확인됐다는 뜻이며 새 시작 계약의 연주 정확도가 개선됐다는 판정은 아니다.

## 코드·계약 검수

- `environment_v5.py`는0초 또는 기존1~2초만 허용한다. 다른 제어 인수 검증·물리 step·gain·action codec은 기존 v4를 재사용한다.0초에서는 정착while을 실행하지 않고 첫 정책 행동부터4개 native 표본을 만든다.
- 실제 MRO는 새 Persistent→새 Contact→v5→기존 Persistent→기존 Contact→v4다. persistent session 소유권·reset 실패 cleanup·contact snapshot·기존 guard가 보존된다. 반복 reset은 같은 scene/sim을 유지하면서 episode 경계에서만 상태를 복원한다.
- 새 계약은 native0초+policy7초/pre-roll3초다. 원 score/목표 provenance는 보존하며 reset부터 첫 onset4.12초와 총 물리 길이7초는 기존 native2+policy5와 같다. 기존505 필드/scale과39출력·손별 inactive0은 유지한다.536개 timing history의 필요한 시간/count scale은 새7초에 맞는다.
- 첫2초 LH 추가 보상은 **원래 목표 candidate가 이전·현재 실제 표본 모두 양성인 구간×.2/s**다. 고립 양성 표본은 시간이 없고 [0,2] 경계를 clip한다. tick 진입 전 측정을 보존해 첫 substep부터 정확히 계산한다. RH 추가 접촉보상은0이고 기존 guide를 유지한다. 기존 timing 성공을 바꾸거나 보상을 중복 추가하지 않는다. 실패tick의 모든 추가 양성 접촉보상은0이다.
- Actor 이전은 알려진 native2/pre1→native0/pre3 변경만 허용하고 역할·stage·물리/행동/안전·원목표·reward 변경을 거부한다.536차원 중 scale이 바뀐 열에 W_new=W_old×scale_new/scale_old 보정을 적용한다. 같은 raw 입력의 보정이며 실제 새 초기조건/시간 token의 성공 보장은 아니다. strict resume는 완화하지 않는다.
- 새 worker는 원 compact logger를 먼저 import해 fresh spawn의 자기참조 재귀를 피한다. runner/evaluator patch는 context 종료·중단 시 복원한다. 보상 후처리 예외는 추가 물리 진행을 차단한다.

거리 proxy를 되살렸던 초안은 폐기·보관하고 최종 접촉시간 보상으로 변경했다. 초안 또는 소스 작성과 겹친 검사는 최종 인증에 사용하지 않았다.

## CPU·원본 보존

최종 freeze 뒤 신규18검사를 독립 실행해 통과했다. 전체 CPU의 정본 `cpu_tests_v1.log`도 **256개 통과**를 확인했다. `source_before_native_v1.json`의 활성115개 Python 소스 SHA가 모두 일치한다. 환경/이전 archive manifest의 원본·보관본20건도 SHA가 일치한다.

## 실제 초기 평가와0초 reset

양손 초기 모델 평가는 각각2/2 안전7초·현재±.5초 단계 성공이며 source_unchanged=True다. 각 episode는420tick/1,680physics, 앞2초는120tick/480physics이고 첫 표본은 native step1~4·반환u=1/60초다. 목표 onset은4.12초다.240Hz 비용 적분은 episode 비용과 부동소수 오차 안에서 일치한다.

reset00의 실제 gym sim time와 scene.steps는 모두0이다. reset01은 같은 native identities/create_sim1/create_env1/load_asset2를 유지하고, 직전1,680step 뒤 scene.steps0·실제 sim clock≈7.000000365초다. 코드상 정착while 미실행과 함께 추가 준비 물리 시간이 없음을 확인한다. lifecycle에는 simulate/fetch 호출 카운터가 없으므로 그 API의 호출 수0을 주장하지 않는다. 숨은 PhysX solver/contact cache의 완전 복원도 인증하지 않는다.

앞2초의 정책 행동은 모든 초기 평가에서120/120 nonzero다. 초기 LH 접촉 보상은 두 회 모두0이며 native candidate 구간을 별도로 적분해도0이다. 따라서 행동·관측·비용의 학습 참여는 확인됐지만 이 모델이 앞2초 조기 접촉 보상을 실제 획득했다고 말할 수 없다. 초기 RH 최초/최소 오차는 각각57.984515ms와104.186051ms로, 이전 native2초 정착 조건의12.285673ms보다 악화됐다. 넓은 현재 단계2/2 성공과 엄격한 타이밍 정확도를 구분해야 한다.

## PPO의 첫2초 실제 포함

양손 스모크는 각각1업데이트·420전이, completed=True·failure=None·changed_inputs[]·cleanup_errors[]·persistent audit 오류[]다. 실제 `rollout_first.pt`의 state shape은(420,1,536)이고 정책 시각은 첫0,119번째1.983333초,120번째2초다. 첫120개 state의 목표 mask가 모두True다. 앞2초120개의 nonzero 행동·보상·비용이 일반 PPO 전이에 포함된다. LH 추가 접촉보상은0, RH 첫2초 guide는약.02846836이다.

실제 source/initial checkpoint 텐서를 비교했다. 양손 모두 source counter12→새 counter0, Actor/Value optimizer state0이며 활성 Actor는 선언된1 또는1.4 scale 보정과 정확히 일치한다. 해당 std도 같다. 최종 스모크 checkpoint의 counter는1이다. 이전 optimizer/counter를 새 계약에 이어 붙인 실행이 아니다.

## PPO 이후 실제 평가와 성능 한계

양손 최종 평가는 각각1/1 안전7초·현재 단계 성공,420tick/1,680physics이며 source_unchanged=True다. LH 원음 구간 접촉후보 coverage는1.0이다. RH 최초/최소 목표방향 오차는86.215483214ms로 같다. 같은 새 계약의 초기 첫회57.984515415ms 대비 **28.230967799ms 악화**했다. 초기 두 번째104.186050873ms를 골라 개선으로 설명하지 않는다. 이전 native2초 조건의12.285672521ms보다도 크다. 현재±.5초 단계 성공은 엄격한 타이밍 성능 보존을 뜻하지 않는다.

최종 첫2초도120/120 nonzero 정책 행동과 실제 비용이 기록됐고 LH 접촉 준비보상은0이다. 최종 기타 최대 이동은LH5.383777mm/RH.855415mm, 발 최대 이동은LH2.168004mm/RH.059171mm다. score_time=u−3·native/측정 step 정렬과240Hz 비용 적분을 별도 재검산해 일치했다. 원 joint music50/100ms는0/0이며 RH down/up/down의 추가 동작도 남아 있다.

초기 및 최종 전체6개 평가의 앞480개 native 표본을 reset의 실제 관절값과 비교했다. 첫2초 활성 관절 최대 변화는 초기LH.147343/.146955rad·RH.093458/.093629rad, 최종LH.147049rad·RH.094248rad로 문서 수치와 같다. 모든 평가240Hz 표본의 any-support 및 both-feet 접촉률은1.0이다. 이는 삼중 접촉 유지라는 주장이 아니다.

## 최종 문서·보존 검수

phase README·초기/최종 분석·새 `ACTIONABLE_PREPARATION.md`와 기존 README/TIMING/AGENTS 변경 diff를 확인했다. 문서3개의 변경 전 archive SHA와 변경 후 SHA가 `documentation_update_v1.json`에 모두 일치한다. 최종 확인 시에도115개 Python 소스는 native 전 freeze SHA와 같았다.

최종 설명은 native0+policy7, 절대 onset4.12초 보존, 첫120개 PPO 관측·행동·비용, 최대.4의 candidate 접촉 보상과 실제 관측0, 엄격한 이전, 현재 단계 성공과 RH 정밀도 악화, 단일 업데이트·단회 최종 평가의 한계를 구분한다. 구현 연결 검증을 조기 접촉 준비·타이밍 학습 완성·압력/음향·전곡·양손 결합·일반화 성공으로 확대하지 않는다.

원본 거리 proxy 초안은 native 전에 보관했고 최종 인증은 candidate 보상 freeze 이후18개 독립 검사·전체256개 검사와 실제 native/PPO 원자료에 근거한다. 보고서를 최종 확정하며 이후 추가 수정 없이 보존한다.
