# 같은20° 초기값의 상완 가상점 설정 검수

요약 판정: **설정·실행 진입은 문제없음, 후속 분석 표기 수정 권장**. Critical: 0 / Warning: 1 / Suggestion: 0. 상완20N/8mm를 먼저 실제 정지 비교로 진행할 수 있다. 이 검수는 설정 diff/지원 계약만 확인했으며 native를 실행하거나 재실행하지 않았다.

## Critical

없음.

## Warning

- [analyze_right_block_cradle_v7.py:43](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v7.py:43): 기존 분석기는 두 reference의 **최대 cap**을 구한 뒤156행의 `Thorax_cap_N`으로 저장한다. 이번 Thorax10/상완20 또는40 설정에서는 실제 Thorax10을20/40으로 잘못 표시하게 된다. 제어에는 영향이 없다. 이전 consumed analyzer는 수정하지 않고 후속 새 분석/문서에서 `two_block_configuration.json`의 body별 reference를 읽어 Thorax10/상완20·40을 구분한다. 이 caveat는 새 trial 시작의 차단 사유가 아니다.

## 설정 확인

- `upper20_static.json`과 `upper40_static.json`은 수락20° config에서 `proximal_point_parameters.R_Shoulder`의 cap/depth만 각각20/.008,40/.016으로 바꾼 값과 exact하다. 기존 candidate/reference SHA 검증을 통과했고 q_ref·native joint limits가 기준과 exact하다.
- Thorax10N/4mm·상완 witness/초기기타p/q·body PD/gravity·left 추종·model effort cap·81목표·amplitude0·strap OFF 조건은 유지된다. 추가 source fitting이나 다른 제어 코드 변경은 없다.
- [right_block_effort_v6.py:29](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:29):20N/8mm 및40N/16mm는 기존 구현의 허용 쌍이다.31행은 해당 body의 목표 깊이와 cap을 각각 reference에 연결한다. 현재 G 기준의 virtual request를 human proximal3/6 및 body9 소유권/cap 안에서 적용하며 기타 직접힘·부착·pose 덮어쓰기 설정이 아니다.
- CONTROL_PLAN은 기존 두 native의 완료5초가 아닌 보호 부분종료를 명시하고 source 근접과 actual 접촉을 구분한다. 이후 좋은 정지 결과만 파동으로 이어가는 순서와 설정/기록 보존 조건이 타당하다. 실제20/40 설정의 안정성·접촉은 아직 검증하지 않았다.

## 검수 SHA256

- Control plan: `a77b14828f3e1cc4b5d92ae4efbfc2b637f302dfa0da290dd7d41af5e97512e6`
- 상완20 설정: `0d7b82dbd9b50c5e56ae4e8cbc5ba69039db33453d3b2aaaae5e2e34d6d6ee99`
- 상완40 설정: `417efd108203d3ad170b5b8056b034dad8569850ed299921429d7ad977bd6b2d`

지정된 이 검수 기록만 생성했으며 다른 담당자 파일과 이전 소비 버전을 수정하지 않았다.
