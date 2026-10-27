# 준비점 일치 3조건 독립 검수

검수 대상은 aligned·wider·compensated의 저장 native 초기값/controls/trace/report/입력 및 사본, [analysis_three](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/analysis_three/summary.json:1), 결과 README/CHANGED_FILES와 이번 main 추가분이다. 이 파일만 작성했으며 물리·actor·IK·분석 producer·봉인 producer를 실행하지 않았다. 과거 phase 전체 inventory 재감사와 후속 automatic-start 실제 평가는 포함하지 않는다.

## 원자료와 제어 범위

- 세 조건은 각각 1200 physics steps·300 controls·151 native 표본·15 runtime checks 참이다. 전부 PREPARE 종료/actor0/실패 없음이며, 분석의 policy 거리 null·source motor phase 목록 빈 값과 맞는다. task 초기 READY 값0 유지와 정책이 실제로 관측한 phase0은 구분한다. 외부 gate에 도달하지 못한 결과를 source 정책 능력 평가나 연주 성공으로 확대하지 않는다.
- 초기 native 상태와 81각은 세 조건 exact, aligned/wider의 PD도 exact다. compensated는 오른팔12 stiffness4배/damping2배, 그 외 properties는 exact다. wider는 준비 반경만 .3→.6rad이며 compensated는 gain·반경·errorgain .5가 함께 달라져 단일 요인의 효과로 분리할 수 없다.
- 900 controls의 requested→float32 rate/native clip→최종81목표를 독립 재조립해 exact를 확인했다. PREPARE cap은 .8rad/s이며 metadata PLAY3.2rad/s는 미사용 설정이다. 기록된 IK goal+errorgain×(IK goal−actual)의 준비 반경/native clip도 요청 오른팔12와 exact, held other36은 unchanged다. 최종 오른쪽30 목표→native bounds 기반 source history의 float32 역변환도 모든 행에서 exact다. `prep_target_W_m==ready_W_m`은 모든 행에서 참이며 stand-off0 기록과 일치한다.
- 범위 참 표본113/295/93과 최소 준비거리17.060964818/28.334010513/33.711651264mm를 controls에서 대조했다. 초기 raw 기타 p/q 기준 최대 위치 변화46.353645732/52.839307264/104.212738740mm와 SO(3) 최대 회전7.095454906/8.258380828/22.635531765°를 독립 계산했다. 이는 저장 표본의 변화량이며 모든 물리 시점의 연속 안정성 인증이 아니다.

2초 값은 aligned17.874040436mm/region 거짓, wider28.341782288mm/참, compensated185.879104028mm/거짓이다. [README:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/README.md:13)의 이전 '나머지 두 조건 참' 표현은 이 값으로 정정됐고, 수정 전 문서는 `doc_before_t2_range_fix`에 보존됐다. aligned의 Euler 표현은 raw q로 [-89.415183404,87.162105802,.368031538]°이며 등가 분기 [90.584816596,92.837894198,180.368031538]°도 X/Z 상한 밖이다. main의 범위 실패 설명과 일치하며 특정 Euler 분기를 바꿔 범위 안이라고 만들지 않는다.

## 입력 보존과 미디어

각 실행의 closure997개·after unchanged/changed0과 사전 source 사본253개 SHA를 해당 before manifest에 대조했다. 세 실행의 runner 사본 SHA는 모두 `779717bfd9622276049fbb3bf4af249808ce0d5aae87b241af98b535b49fa04c`다. 최종 analyzer 직접 입력19개는 현재 SHA exact/after unchanged, summary SHA는 `4dfad243c083e1e9f63dab1e18afdb4b2d0965b59bf10df3601c038a86f28510`이다. 이전 analysis_aligned/analysis_final을 덮어쓰지 않고 analysis_three와 구분했다.

906 PNG SHA와 각151 capture rows/render readonly를 확인했다. 전신/손 영상 총6개는 현재 SHA·실제 ffprobe가 저장 metadata와 exact이며151프레임/30fps/5.033333초다. 마지막 native 시각은5.0초다. compensated2초 전신 PNG를 직접 확인했다. 이 결과 정리에는 새 그림 producer나 native 재실행이 없다.

## 문서 판정

[결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/README.md:3)의 actor0/정밀 준비 진단, [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/CHANGED_FILES.md:19)의 이전 분석 보존과 [main PLAN:218](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:218)/[main README:1523](/home/ajou/yigyu/3/stability_adapter_2/README.md:1523) 결과 표현을 대조했다. 두 결과 문서의 모든 절대 링크는 존재하며, 각 실행 source_before의 main 두 문서는 현재 파일의 exact prefix다. main232/1537의 후속 진행 기록은 이번 세 조건의 actor 실행이나 타현 성공으로 합치지 않는다. 현재 근접 초기배치와 source/실제 물리 인증 범위, 무스트랩·자유기타·root하체고정·손바닥 지속접촉 불필수 및 후속 계획 구분은 일치한다.

Critical 없음. 2초 범위 표기의 Warning은 원문 보존 후 문서 정정으로 해결됐다. PASS는 저장 결과·제어 경계·보존·문서 검수이며 연주 성공이나 후속 실행 인증을 뜻하지 않는다.

확인한 최종 문서 SHA: README `ef031bae126d3f0488dec93d42955a35e5b4d896abf625399b235e7f1cd49f35`, CHANGED_FILES `cfef9f7fbee511bc747a082090050ca966111a97a5bfee4e3362878e6a50e388`.

최종 판정: PASS
