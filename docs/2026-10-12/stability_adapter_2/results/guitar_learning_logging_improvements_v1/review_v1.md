# 학습 로그 개선 독립 검수

**사전 판정: 문제없음.** 동결된 구현에서 미해결 소스 차단 문제는 없다. 실제 native 실행·최종 전체 CPU 결과·최종 결과 문서는 아직 검수 대기다. 검수자는 구현·기존 봉인 자료·타인 변경을 수정하거나 되돌리지 않고 이 보고서만 작성한다.

## 범위와 불변성

변경 전 보관본과 parallel/train 실행기·종료 요약·평가 metadata·PPO 변경을 대조하고 새 metrics/journal/format/report/recovery 모듈을 읽었다. 보관 manifest157개 snapshot은 SHA가 모두 일치했다. 생산 변경은 신고된 로그 연결8개 파일에 한정하며 보상·성공·관측·제어·물리 환경 소스는 보관본과 같다. 동결169개 원경로와 source_v1 사본169개도 모두 SHA 일치한다.

PPO 진단은 optimizer 입력·순서·RNG를 바꾸지 않는다. 원 PPO 대비 model·optimizer·RNG·기존 반환 scalar의 정확한 동등성 검사3개를 독립 실행해 통과했다. 새 metadata는 정책 계약 바깥에 두고 원 strict checkpoint identity/load를 변경하지 않았다. epoch/mini-batch 평균과 마지막 값, latent entropy와 행동 entropy, 활성 채널과 비활성 placeholder를 구분한다.

## 해결된 발견 사항

- **Critical — 기록된 prefix의 요약 누락:** journal에 유효 행을 쓴 뒤 예외가 나면 metrics.observe 전 중단돼 logged/durable/CRC재생1행인데 summary.transitions0·reward_terms{}가 되는 것을 CPU fault fixture로 직접 재현했다. 현재 `train_parallel.py`는 logged 증가를 확인해 그 행을 공통 record_logged_row로 반영하고 원 IO 예외를 보존한다. 수정 후 회귀는 summary.transitions1·reward1과 buffered0/discarded1을 확인한다.
- **Warning — 종료 시 메모리 재누적:** 새 종료 요약이 episodes 전체를 읽고 전역 에피소드 metadata를 계속 쌓던 경로를 지적했다. 현재 standard는 counters/groups와 episode 파일 경로/SHA를 사용하고 상세 배열은 diagnostic/legacy에 한정한다. 전역 metrics도 counters/groups로 바뀌었다. recovery CLI의 window 목록 역시 closed episode를 쓴 뒤 정리한다.
- **Warning — raw 선택의 활성 손/오류 범위:** RH 진단이 비활성 LH fretting 변화만 따르던 경로를 지적했다. 현재 LH 분류와 RH accepted/unprepared/extra/blocked/ready/recovered/wrong 전환을 구분해 선택한다. 보상·성공에는 관여하지 않는다.
- **Warning — 평가 seed 의미:** 설정 seed를 실제 reseed처럼 기록하던 필드를 configured_seed로 바꾸고 설정 출처·strict checkpoint RNG 복원 범위를 명시했다.
- **Warning — 정리와 회계의 예외 경계:** stream flush/fsync 실패에도 close를 finally로 보장한다. collector buffered prefix와 journal의 sampled/discarded 정본 수를 분리해 기록 후/집계 전 실패에서 두 수가 다를 수 있음을 명시한다.

## 최종 코드에서 확인한 동작

60개 control tick마다 닫힌 gzip member와 file fsync 경계를 만들며 sampled/logged/durable/PPO committed/discarded를 분리한다. CRC가 검증되지 않은 마지막 member는 recovery에서 성공 행으로 반환하지 않는다. 기존 단일-member gzip도 읽지만 잘린 파일의 복구 가능 prefix가0일 수 있음을 명시한다. recovery는 새 디렉토리만 쓰고 PPO commit/모델 유효성을 추정하거나 자동 재개하지 않는다.

새 240Hz 안전 요약은 끝 표본으로 대체하지 않고 네 하위 표본의 극값·이탈 시간과 tick 경계를 연결한 최장 연속 이탈을 계산한다. 역할별 품질·목표·단계·완료/시간제한/미완료·성공별 분모를 구분하고 누적 quality 값을 매 tick 다시 합하지 않는다. 해제 시각은 실제240Hz 관찰 표본이며 지속 해제 완료·late 접촉 점유와 별개다.

standard는 환경 info를 복사해 기록만 축소하고 full terminal episode를 별도 stream에 남긴다. 매 tick 중복 timing/긴 문자열/행동·feature 상세를 줄이되 첫 tick·활성 판정 전환·물리 실패의 raw 근거를 보존한다. diagnostic은 상세 compact·선택 first rollout을 제공한다.

최종 요청 업데이트의 중복 periodic 저장을 생략하고, wall budget 등에서 마지막 periodic의 model/optimizer/RNG/identity까지 현재 상태와 정확히 같을 때만 hardlink한다. metadata는 alias manifest에 분리한다. RNG 또는 모델만 달라도 full save하며 원 checkpoint를 수정하지 않는다. journal/최종 checkpoint 검사10개를 독립 실행해 통과했다.

정상/실패 종료의 준비·품질 summary는 finally에서 생성하며 부차적 summary 오류를 원 예외 대신 내보내지 않는다. 직접 실행한 real-runner CPU fixture2개는 정상 final-only/일치 회계와 기록 후 실패의 prefix·원 OSError·복구 상태 보존을 통과했다. root의 최신 통합25개 PASS(0.954초) 로그도 확인했다.

## 남은 검수

최종 전체 CPU와 제한 native 실행 결과, 실제 저장/회계·재개·평가 산출물 및 문서의 성능 주장을 확인한 뒤 이 보고서만 확정한다. 현재 코드 검수만으로 속도 개선·I/O 병목 해소·학습 성과를 주장하지 않는다.
