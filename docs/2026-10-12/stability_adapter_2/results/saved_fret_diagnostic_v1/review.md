# 저장된 전체 Fret 진단 독립 검수

## 사전검수

**요약 판정: 문제없음(사전검수).** 새 producer는 기존 완료 native 실행을 읽기만 하여 표시/영상/수치를 재구성한다. fresh live 진단 3회의 실패를 완료로 바꾸지 않으며 새 physics 실행은 0회다.

- **Critical:** 없음.
- **Warning:** 없음. 처음 확인한 v2 `initial_values.json`의 직접 입력 SHA 누락은 [build_saved_fret_diagnostic.py:87](/home/ajou/yigyu/3/stability_adapter_2/build_saved_fret_diagnostic.py:87)에서 실행 전 보완됐다. 현재 실제 `analysis/attempt.json`에도 해당 입력이 포함돼 있다. 초안/개정본은 별도로 보존됐다.
- **Suggestion:** 없음.

검수 대상은 `SAVED_FRET_DIAGNOSTIC_PLAN.md`와 새 `build_saved_fret_diagnostic.py` 및 직접 재사용하는 frozen packet 해석 함수다. 작성 권한은 이 review 한 파일뿐이며 원본/producer를 수정하지 않았다. 독립 **AST PASS**.

시점 정합성: 원본 capture와 native trace의 같은 step을 대응하고 PLAY 관측은 해당 step의 다음 제어 직전 `observation`을 사용한다. terminal 관측은 마지막 control의 4step 뒤 별도 `terminal_observation`으로 연결한다. 목표 조회가 기록되지 않은 준비 구간과 마지막 contact는 미측정으로 둔다. live 평가 전 목표와 저장된 pre-integration 목표를 혼동하지 않는다.

관측 해석: `O_hand_geometry`의 top-body local marker와 `O_target_geometry`의 기타 local 목표벡터 합을 world p/q로 옮긴다. packet 목표는 원본 source에서 손가락별 assigned target 평균이지만, 이번 baseline 전체 PLAY controls에서 같은 손가락에 동시에 여러 현이 배정된 경우는 **0개**임을 독립 확인했다. native 실제 top-body와 packet local marker의 1µm 이내 정렬을 producer가 검사한다. 손목의 목표벡터 길이는 표시용 손끝 거리·pad 압착·음악 성공과 구분한다.

표시 근거: 카메라는 v2의 같은 초기상태·고정 camera matrix를 재사용하고 source SHA 및 공통 raw RGBA prefix를 검사한다. depth는 없으므로 설명선을 모두 투시 점선으로 표시하고 가려짐 판정을 하지 않는다. 접촉 원점은 표면 접촉점으로 설명하지 않는다. 전체 렌더의 baseline 정렬, 픽셀 대조, 수치/캡션/영상 coverage 및 입력 불변은 완료 결과에서 후속 검수한다.

## 후속 결과 검수

**요약 판정: 문제없음(저장 자료 후처리 범위).** Critical/Warning/Suggestion 없음. 신규 live full 진단 성공을 뜻하지 않는다.

- 원본 report는 `completed_recording=true`·모든 source check 참·첫 `source_terminal`을 기록한다. 이는 녹화 완료이며 `music_success=false`, press/stable-press success 0, `failure_termination=true`, `finger_back_termination=true`다. 새 제어·학습·physics 실행은 0회다.
- 독립 SHA 대조: 후처리 입력 **864개 변경 0개**, 표시 PNG **778개 불일치 0개**, 기존 보호파일 **1327개 변경 0개**. 실제 소비된 producer와 direct helper가 입력 manifest에 포함된다.
- 저장 frame은 **389개**, step **0~3100**, 물리시간 **12.916667초**다. 8step 간격에 마지막 4step 종료 frame을 추가했다. 두 MP4를 독립 `ffprobe`로 읽어 각각 **1760×720 / 30fps / 389frame / 12.966667초**를 확인했다. 영상 재생 길이와 마지막 물리 시각은 다른 양이다.
- producer의 정렬검사는 최대 top-body/packet marker 차이 **9.4506e−8m**로 1µm 조건을 통과했다. v2 고정 camera와 초기 상태/source SHA, 공통 **31frame×2view** raw RGBA 픽셀 exact 검사도 통과했다.
- 원본 trace에서 위치 box와 최단 상대 회전을 독립 재계산하여 이탈 **53frame**, 최대 위치 초과 **15.0053mm**, 최대 상대 회전 **50.2480°**를 확인했다. 이는 회전 허용집합·안전 형상 인증이 아니다.
- t0 전신, 2초/종료 손 근접, 5초 전신 및 timeline을 실제로 열어 캡션/row 수치·투시 점선·마지막 접촉 미측정 표시를 대조했다. timeline 범례가 실제 표본을 가리지 않고 손목 목표벡터와 손끝 marker 거리 단위를 구분한다. 손목 벡터 범위는 **155.197~221.632mm**지만 목표 frame이 바뀌므로 하나의 고정 목표 오차 증가로 단정하지 않는다.

2초 PNG의 `PREPARE`는 원본 raw capture가 handoff 직전이라는 뜻이다. 표시하는 frame 0의 packet은 같은 native pose에서 handoff 후 첫 PLAY 제어 직전 관측이다. 이 시점 차이를 결과 설명에도 명시하도록 root에 전달했다. 준비 구간 목표 미기록과 terminal goal frame 번호 미제공을 실제 source 목표가 없었다는 뜻으로 해석하지 않는다.

## 최종 문서·상대운동 검수 종료

**최종 판정: 문제없음.** README·FILE_INDEX·interpretation·추가 상대운동 수치를 대조했으며 Critical/Warning/Suggestion 없음. 결과 README는 2초 capture/packet 시점 차이, fresh live 3회 실패, 기존 완료 실행 재사용, raw lambda·투시 표시 한계 및 MP4/물리 시각 차이를 명시한다. 원본 terminal의 `episode_success=false`, `goal_finished=false`, 지속 성공 0/27, index finger_back 실패와 일치한다. 2초/8초 marker 수치 및 2.7초 world Z 하한 방향 최대 이탈도 저장 row와 일치한다.

`relative_wrist_motion.json`의 2/5/8/10/종료 5개 행을 원본 native trace와 body 이름 목록으로 독립 재계산했다. world 손목/기타 root 변위, handoff 대비 최단 회전, `R_G^-1(p_wrist−p_guitar)`의 상대 변위 모두 저장 값과 **차이 0**이다. 2→8초의 **18.355mm / 44.393mm / 47.906° / 59.372mm**는 README의 반올림 값과 맞고 해당 입력 SHA도 변경 0개다. 이 상대 변위를 마찰 미끄럼·표면 접촉점 이동 또는 목표 오차로 해석하지 않는다.

FILE_INDEX의 source 함수/class 및 상위 PLAN 667행·결과 README 573행·VISUAL_REPORT 2313행을 실제 현재 줄과 대조했다. 세 phase README 및 saved FILE_INDEX의 실제 링크는 모두 존재하며 미생성 최종 봉인 산출물은 예정 경로로 구분돼 있다. 이 기록을 끝으로 검수 파일을 닫으며 최종 SHA 봉인은 root가 수행한다.
