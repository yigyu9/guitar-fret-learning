# APPROACH 진입 감쇠 비교 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / 미해소 Suggestion 없음. 새 native 실행 없이 저장 코드·원자료·영상·문서를 검수했다.

- 완료 기록은 1200 physics steps, controls 300개, native report 20계약 통과다. trace는 camera-aligned 151표본에 terminal 추가표본을 더한 **152개**이며 영상은 각각 151프레임이다. PREPARE/PLAY/HOLD 제어 표본 `49/54/197`과 source 종료 `1.716667초`를 대조했다.
- `run_strike_approach_damping.py:126–146` 및 `PD_approach_properties.json`: step304/1.266667초 actual source phase1에서 RShoulder/Elbow/Wrist 9개 damping만 0.25배로 변경한다. 전체81 properties의 나머지 값·native readback·state 보존 기록이 일치한다. 이 버전은 RECOVER에도 낮은 감쇠를 유지한다.
- switch 이전 controls76개와 switch 시점까지 전체 native trace39개를 기존 timed EXIT와 직접 재대조했다. phase/목표/actor observation/action/history/time과 비교 입력6 SHA가 exact다. 실행 closure1051개는 현재 파일1049개와 실행 당시 정확한 source 사본2개로 모두 해결됐다.
- 실제 raw pulse를 합산해 READY1, target/physical hit1, accepted release1, physical release5, miss1, wrong4를 확인했다. 1.35초 hit는 adapter key `[0,2,1]`의 **zero-based event0, string2 DOWN**이며 이후 source index1이다. timing sample `+44.484798ms`와 RECOVER wrong 시각 `1.5/1.683333/1.7초`가 일치한다. clearance lifted/reached/scheduled completion은 모두0이다.
- 기타 위치 최대/끝 `46.353646/39.461086mm`, 회전 최대/끝 `7.095455/5.414131°`, 사용자 범위 안 전체/policy 표본 `292/300`, `49/54`를 저장 trace/controls와 대조했다. 마지막 running F1은 `0.285714`다.
- 두 MP4의 SHA와 실제 ffprobe `1280×720/30fps/151프레임/5.033333초`를 확인하고 1.7초 손 근접·5초 전신 native PNG를 직접 보았다. README/CHANGED의 절대 링크와 자료 출처를 확인했다.

해소한 문서 권고: README:17/27은 hit 대상 event0와 타현 후 index1을 구분한다. 이전 timed EXIT의 다른 scheduled event보다 clock hit가 이르다는 관측을 같은 음표 성능 개선으로 해석하지 않는다.

검수 SHA256: runner `f8c3e6ec4fb4f4a2619a428ac51be7933a2ebed3d891dabf6ea2034a7f0109ce`; 분석기 `8e6feb45a03eea77dffd979f80178101bad0b5bb2a3feb8ea83e664457b39594`; summary `4f842f4f2b0cabb8459ca790a8964a49ef2ef11625550819a37168b4584df3e6`.

최종 범위: 5초 저장 완료와 음악 완료는 다르다. source 종료 이후는 HOLD 자유 물리/녹화다. 짧은 PLAY 부분 F1과 단발 hit는 성능 승리·전체 연주 성공의 근거가 아니고, 감쇠와 회복 실패의 인과도 확정하지 않는다. 현재 조건 미채택이라는 문서 판정은 적절하다. 남은 actionable finding 없이 이 기록을 동결한다.
