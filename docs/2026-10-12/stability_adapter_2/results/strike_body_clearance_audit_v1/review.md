# 독립 검수 — source 손 형상·기타 앞면 여유

요약 판정: **문제없음(PASS)**. 현재 남은 Critical / Warning / Suggestion 없음. 정적 source 계산과 문서 범위를 검수했으며 새 native 초기화·physics 실행은 하지 않았다.

- [analysis.py:36](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/analysis.py:36)의 binary STL 16개, asset scale·geom pose·저장 body pose 변환 및 Gbody box 앞면 법선을 확인했다. 앞면 Gz −1.7mm와 READY/ENTRY/EXIT/lift 간격 22/12.5/12.5/24mm를 위치 좌표와 구분한다. 최소 signed projection과 XY footprint는 native cooked 형상 거리·접촉 인증이 아니다.
- [analysis.py:194](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/analysis.py:194)의 보존 FK 함수가 현재 함수 AST와 동일하다. Python 3.8에서 기록된 AST SHA도 정확히 일치했다. 별도 STL 파싱과 저장 1.2/2초 자세의 순수 FK로 네 관절 후보·앞면 projection·평행이동 식·free12 RMS를 재계산했고 기록과 일치했다(대표 projection 차이 0mm).
- EFFORT 1.2초 pick 간격 10.462374mm에서 네 M/R hinge +0.2rad 후보의 middle/ring/pinky 최소 간격은 17.105693/5.781159/2.694470mm였다. POSITION은 21.981193/6.521126/−0.191376mm였다. pick 위치·pinch9·나머지77 좌표 보존을 확인했다. 후보 free12 RMS 0.126692/0.120716rad와 개별 source residual ±0.22rad는 별도 기준이다. 원래 pinky 및 늦은 ENTRY projection의 음수 간격은 남는다.
- [README:52](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/README.md:52)의 최근접 저장 시각·5초 상태와 4.983333초 접촉 기록 구분, [README:87](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_body_clearance_audit_v1/README.md:87)의 source/native·raw lambda·원인 추론 한계를 확인했다. 네 관절의 정적 후보는 실제 제어 결과나 grip/타현 성공을 증명하지 않는다.
- 34개 입력의 현재 SHA, 4개 기록 검사, Python 3.8 문법을 확인했다. **해소된 Warning:** geometry 최초 읽기(:119–124)는 SHA 수집(:132)보다 앞선다. README:12/89가 수집 이후 종료 대조라는 범위를 명시했고 수정 전 README를 보존했다. 소비된 코드·summary는 변경되지 않았으며 최초 읽기 전 봉인으로 소급 인증하지 않는다.

검수한 SHA256: analysis.py `4a344f2a6cb3c4ae605833760f471d09552b2451099d5a63040041a38949227e`; summary.json `f63b5da100a305d39a3279f29daaf623581424539e16b6e6a4d79d1878d10565`; 최종 README `4c291ab0b4e77cb4f2e78239e0442080ab47a59120bf77c40afcd866fcb3c9d4`.

검수 완료 범위는 저장 자세의 source 형상 계산·대표 순수 수치 대조·출처 및 문서다. native 후보 자세/접촉, importer margin, 전체 경로 충돌 해소, 안정성·성공 또는 별도 curl 실험의 결과는 인증하지 않는다.
