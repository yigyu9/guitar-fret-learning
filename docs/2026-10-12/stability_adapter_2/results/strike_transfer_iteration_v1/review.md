# Strike 전달 진단 1차 독립 검수

검수 범위는 `base_v2`·`rate`·`gain_v2`의 저장된 초기값/controls/trace/report/입력 보존본, [최종 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final/summary.json:1), 결과 문서와 이번 main 추가분이다. 이전 전체 inventory 재감사 및 후속 alignment/hybrid 실제 검증은 포함하지 않았다. 검수자는 이 파일만 작성했으며 물리·actor·분석 producer·봉인 producer를 실행하지 않았다.

## 실제 자료 대조

- 세 최종 실행은 각각 1200 physics steps·300 control rows·151 native 표본, 실패 없음·15 contract checks 참이다. 정책 표본은 180/180/174개, PLAY 시작은 2.0/2.0/2.1초다. 초기 native 상태와 81각은 세 조건 모두 exact이며, base/rate의 초기 PD 및 첫 120 controls·0~2초 61 native 표본도 exact다.
- gain_v2의 초기 PD는 오른팔12 stiffness 4배·damping 2배이며 나머지 properties/69축 PD는 baseline과 exact다. 환경 생성 후 첫 physics step 전에 변경한다. 최종 목표의 native bounds·rate tolerance·held other36을 900 controls에서 대조했고, 최종 오른쪽30 목표에서 저장 source history로의 독립 float32 역변환 최대 오차는 0이다. 체크포인트/source 판정 변경이나 원 actuator와의 동등성을 뜻하지 않는다.
- actor 표본의 사용자 기타 범위 참은 67/180, 20/180, 7/174다. 정책 중 최소 READY 거리 11.229763/6.891144/10.848061mm, 기타 최대 위치 변화 59.444609/59.444609/60.411330mm, 최대 회전 46.687600/45.509466/42.705181°를 원자료에서 대조했다. raw 기타 p/q로 위치·SO(3) 회전 최대값을 독립 재계산했다.
- source motor phase는 base/gain `[0]`, rate `[0,1]`이며 source의 1=APPROACH 정의와 맞는다. target hit·physical target hit·accepted release는 모두 0이다. running score와 step pulse는 미완료 episode의 부분 결과이며 전체 곡 F1·연주 성공으로 확대하지 않는다. rate 조건의 접근 개선과 기타 범위 악화, gain 미채택 설명은 저장 결과와 일치한다.
- analyzer의 관절 목표-실제각 오차는 같은 시각 native 표본의 실제각과 그 시각에 제출한 최종 목표를 비교한 값이다. 연속 물리 모든 시점의 오차 측정으로 확대하지 않는다. 최종 분석 입력19개 SHA는 현재 exact, after unchanged이며 요약의 정책 수/범위 수/각 pulse 합계를 controls에서 독립 대조했다.

## 보존·미디어·문서

최종 실행 closure 989/992/993개에 대해 before 개수와 after unchanged를 확인하고, 각 사전 source 사본245/248/249개의 SHA를 해당 manifest와 대조했다. 세 실행에 소비된 runner SHA는 모두 `2df780046842a3c43567d08ae2f50c5ead04fa637b2ed561bf022e9c213a092f`다. float64 rate 배열은 과거 scalar cap과 미세하게 다른 산술이므로 새 base_v2 비교이며, 과거 준비 baseline의 byte-exact 재현이라고 하지 않는다.

첫 base는 Ninja import 실패, task_error와 로그를 보존했으며 비교에서 제외했다. 첫 gain은 5초 native 결과를 보존하되 `inputs_after.changed`의 `run_strike_ready_alignment.py` 한 파일 변경으로 closure 검증 실패였다. 이를 물리 실패나 clean 최종 조건으로 포장하지 않고 gain_v2와 구분했다. 현재 문서의 `analysis_base.log`가 clean base_v2 분석이라는 정정도 확인했다.

각 조건의302 PNG SHA·151 capture rows/render readonly를 대조했다. 전신/손 영상 총6개는 현재 파일 SHA와 실제 ffprobe 결과가 저장 metadata와 exact이며 모두151프레임·30fps·5.033333초다. 마지막 native 표본은 sim 5.0초다. rate 마지막 전신 PNG를 직접 확인했다. 그림 producer 추가나 원native 이미지 변경은 없다.

[README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/README.md:7)의 정책 구간 최소거리·Kp4/Kd2 표현, [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/CHANGED_FILES.md:16)의 실패 이력과 [main PLAN:200](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:200)/[main README:1505](/home/ajou/yigyu/3/stability_adapter_2/README.md:1505) 결과 링크 정정을 확인했다. 두 문서의 절대 링크는 모두 존재한다. phase before 및 alignment `main_before_progress`와 비교해 main 두 문서의 기존 prefix가 보존됐다. main의 alignment 완료 관측과 hybrid 미실행 경고는 이 phase의 타현 성공으로 합치지 않는다.

## 확인한 최종 SHA

- README: `06b74babe5309dcd356c48a72b072cb3bbb11ff2250705a9450e406419a2911c`
- CHANGED_FILES: `d4cd052bd9d065026d6aaba8883fc6eae2606ae5b1750710b4828106d90dfe26`
- analysis_final/summary.json: `04e0b8e6b0a60f815427de7695ae1159f92c53b1220344b2be1ccaeeeb94bc71`
- analyzer: `9f0e9facc6dcb099f7808bd5ca959c61e7dc0c670c673ce40c223beeda38e264`
- preservation wrapper: `13b0ad1c7469c5c13dce190f8a25a6f1014c280299159a5cdfc8177ce5d4ed0b`

Critical 없음. 문서의 gain/거리 구간/실패 로그/결과 anchor Warning은 수정으로 해결됐다. PASS는 기록·비교·제약 표현 검수이며 연주 성공, 기타 경계 복귀 제어 또는 원source 물리 동등성 인증이 아니다.

최종 판정: PASS
