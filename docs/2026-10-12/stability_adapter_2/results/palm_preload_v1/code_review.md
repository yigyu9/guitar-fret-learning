# PALM_RATE 초기 길이 조합 실행 전 검수

검수일: 2026-10-07. 대상은 `prepare_palm_preload_references.py`, `PALM_PRELOAD_COMPARISON.md`, 새 세 설정과 초기 audit, 기존 runner의 reference 소비 범위다. 다른 코드·동결 기록·원자료를 수정하지 않았으며 reviewer native 초기화·rollout·source query는 없다.

## 요약 판정

**문제없음. 실행 전 검수 완료. 남은 Critical / Warning / Suggestion 없음.** 생성 reference는 검증된 초기/제어 기대값이며 해당 길이의 rollout 측정 결과가 아니다.

## 입력·reference 경계

- 새 0/1/2N 설정을 기존 LEFT_WRIST_STRAP 입력과 byte/SHA 대조했다. JSON은 절대 rest length만 다르고 초기 q·기타 Z+5mm·회전·나머지 조건은 같다. `LA=L0−T0/6000`의 명목 초기 0/1/2N 값을 확인했다. Runtime 일정 장력이나 동적 길이를 뜻하지 않는다.
- 저장 initial audit의 세 record는 각각 기존 9개 계약·source/LH 조건을 통과했다. Generator가 이 acceptance를 검사하며 baseline의 runner 필수 초기/제어 필드 8개와 audited LA만 가져온다(:38–48). 기존 native runner는 q/name·설정·물리·목표·bounds를 다시 검사한다. 기대 reference에는 max error 등 측정 통계를 복제하지 않는다.
- Raw5는 원래 quiescent 자료의 읽기 symlink이며 새로운 길이의 PI/PALM rollout으로 표시하지 않는다. Reference role와 origin report/audit record를 명시한다. 0N 성능 비교는 실제 기존 readback 0.1초 및 sensor 0.5초 자료를 별도로 재사용하는 계획과 구별된다.

## SHA 보완·순수 검증

병합된 audit SHA가 origin의 stale SHA를 가릴 수 있던 Warning은 해소됐다. 각 맵을 먼저 current 검증하고 겹치는 경로의 충돌을 거절한다(:25–30). Raw5의 resolved path와 SHA를 입력에 추가하고 각 symlink의 link/resolved 경로·SHA를 manifest에 기록한다(:33–35·52–59).

실제 helper CLI를 새 `/tmp` 출력에 실행해 세 expected-invariant reference, 필드 8개·LA·11개 초기/origin 검사와 측정 통계 미복제, 15개 symlink 및 명시 SHA를 대조했다. 별도 임시 baseline의 겹치는 origin SHA만 stale로 만든 regression은 출력 생성 전 nonzero exit로 거절됐다. 이는 저장 JSON 변환 검증이며 native 실행이 아니다. 최종 loop 전 mkdir 한 줄도 확인했고 모두 거절된 임시 fixture는 빈 references/raw_links manifest만 남겼다. 기존 출력이 있으면 중단하는 guard도 유지된다.

## 실행 범위·동결

계획은 기존 승인된 PALM_RATE와 고정 초기 길이의 새 조합이다. 통과한 1/2N의 0.1초·새 어깨 접촉이 없는 조건의 0.5초만 비교하며 최대 네 새 rollout이다. PD·gain·box·rate·기타 p/q 목표·제어권·모델 변경이나 1초 연장은 포함하지 않는다. Source 조건은 cooked clearance·지지 인증이 아니며 contact 행은 힘·인과 증거가 아니다. 실제 native 계약·각 길이 short prefix·장력·성능은 실행 뒤 별도로 검수해야 한다. 이 preflight 기록을 동결한다.
