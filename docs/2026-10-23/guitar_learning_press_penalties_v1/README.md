# GPU 왼손 감점 개선 v15

오압현·누락 감점을 음 길이와 손가락별로 정규화하고, 미달성 감점은 그 음의 최장 연속 clean 시간에 따라 완화했다. 오압현 판정은 보존하면서 원인 몸체·프렛 범위와 모호성·다음 음 준비 여부를 분리해 기록한다. 실제 GPU/native 물리나 학습은 이번에 실행하지 않았다.

## 감점

`D=end−onset`, `b=전체 음 수/(등장 손가락 수×해당 손가락의 음 수)`다. 아래는 단계 계수를 곱하기 전 값이다.

~~~text
wrong   = −Σ b × wrong_dt / D
missing = −0.5 × Σ b × missing_dt / D
best    = max(지금까지의 audible 연속 clean 시간)
deficit = clamp(1 − best/required_clean, 0, 1)
missed  = −0.5 × Σ 이번에 미달성으로 종료된 음 × b × deficit
~~~

wrong/missing은 기존처럼 audible onset~end의 인접240Hz 끝점을 사다리꼴로 적분한다. 진단 원장의 wrong/missing 시간은 초 단위로 남기고, 보상 계산만 D로 나눈다. 같은 실패 비율이면 음 길이가 달라도 같은 기준이며, 손가락별 전체 목표 수의 편중도 b로 보정한다. 계수는 wrong1, missing0.5, missed0.5를 유지했다. 길이 정규화로 특히 짧은 음의 기존 감점 크기가 달라지므로 성능 개선을 검증했다고 해석하지 않는다.

기존 음수 단계 가중치를 그대로 적용한다. wrong은0.15/1/1, missing·missed는0.1/0.35/1이다. b=1인 음을 완전히 잘못 누르면 단계0에서−0.15, 완전히 누락하면−0.05다. 한 음이 거의 달성되어400ms 문턱 중399ms를 연속 채웠다면 missed 원시는−0.00125, 단계0에서는−0.000125다.

best는 누적 clean과 구분한다. 접촉이 끊겨 현재 clean_streak가0이 되어도 best는 남고, 짧은 접촉을 여러 번 합쳐 best를 키우지 않는다. 달성 문턱·달성 보너스 한 번 지급·이분법적 left/left_missed 음 수는 유지한다. 거의 달성해 감점이 줄어도 달성 음으로 세지 않는다. 준비 구간에는 wrong/missing을 새로 감점하지 않는다.

## 오압현 원인 기록

기존 판정 `higher OR (!pad_positive AND (lower OR assignment))`를 유지한다. higher는 올바른 패드가 있어도 현재 목표를 방해하고, lower/assignment는 올바른 패드가 없을 때만 기여한다. 새 진단은 이 판정에 실제 기여한 source 표면 샘플을 다음과 같이 기록한다.

- 목표 ID·줄과 원인 몸체10개(엄지 및 네 손가락의 finger2/3), higher/lower/assignment별 audible 시간.
- 해당 몸체의 기여 샘플 source 프렛 번호 최소/최대.0은 경계라 내부 프렛을 정하지 못한 샘플이다. 원인 시간이 있는 항만 해석한다.
- 프렛 내부의 기하 근거가 있는 wrong 시간과 그런 근거 없이 경계 assignment만 있는 모호한 wrong 시간. 두 시간은 기존 wrong 시간을 분할한다.
- 방해 샘플이 미래 음의 finger/string/interior fret와 맞으며 그 음의 press−2~onset 준비 구간인지 여부. 이때도 현재 음을 방해하면 감점한다.

몸체·원인은 겹칠 수 있으므로 원인 시간을 합쳐 감점하지 않는다. 실제 wrong 감점은 목표별 원래 boolean 시간으로 한 번 계산한다. 기존 higher/lower/assignment의 press~end 진단도 남으며 새 audible 기록과 혼동하지 않는다. 다음 음 준비를 자동 면제하거나 모호한 접촉에 새 감점을 추가하지 않았다. net body force는 접촉 상대·실제 현 압력·음향을 인증하지 않으므로 supported도 기하상 근거라는 뜻이다.

진단은 GPU의 고정 크기 누적 텐서로 유지하며 매tick CPU 복사나 접촉 로그 append를 하지 않는다. 프렛 범위는 int16로 처리해 큰 sample×target 임시 텐서가 int64가 되는 것을 피했다. 실제 CUDA 메모리 피크·처리량은 이번 CPU 검사로 확인하지 않았다.

## 보존과 계약

전체 보상v15, 표면 보상v7, 원장v6, wrong 진단v1이다. 표면 관측v4와544상태/24열event/8우선slot/3331커리큘럼은 유지한다. 기존v14 이하 strict resume를 거부하고 동일v15 전체 계약끼리 복원한다. B의 약한 휴지 자세 보상·엄지 포함 손가락 움직임 비용0·손목영역·최초접촉·clean유지/달성·물리·제어·PPO·초기035/v14는 보존한다.

변경 전448Python과16문서, 총464원문은 [보관 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261023_before_press_penalties_v1/manifest.json)에 보존했다. [이전v14 결과](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_preparation_B_v1/README.md)와 기존 이미지·과거 결과는 수정하지 않았다.

## 검증

메모리 자료형 조정 이후 최종 CPU 회귀27모듈265개가 모두 통과했다(기존247+신규 감점10+원인진단8). 독립 change-reviewer가61개 CPU검사를 실행했고 별도 scalar 계산으로 원인810개boolean·프렛 범위270개cell·지원/모호/다음준비27개조합이 일치했다. 기존 _contacts는 새 진단 호출 한 개를 제외하면 원문과 AST가 같고, 진단 입력도 변경되지 않는 것을 확인했다. 남은 검수 지적은 없다. [검사 원문 목록](cpu_tests.json)과 [보존 검사](preservation.json)를 기록했다. GPU/native 구동·장기학습 성능을 검증한 결과는 아니다.
