# 독립 검수 — Strike incremental approach v1

판정: **문제없음(PASS)**. Critical / Warning / Suggestion: 남은 항목 없음. 구현 사전 검수에 이어 저장 원자료·목표 수식·입력 SHA·native 미디어 및 최종 한국어 README/CHANGED_FILES를 대조했다. 신규 native 초기화·physics 실행·공유 코드 수정은 하지 않았다.

- 1,200 physics steps·24개 계약·300 controls, PREPARE/PLAY/HOLD 49/169/82를 확인했다. Trace 152행은 step 872·3.633333초의 PLAY/HOLD 중복을 포함하며 카메라 151프레임과 구분된다.
- PLAY 169행 모두 R9 이전 제출 목표+2δ, 적분 0 유지, 최종 float32 native/rate clipping이 일치한다. 요청 목표의 반올림 차이는 최대 5.9541e−8 rad다. READY/닫힌 APPROACH/열린 APPROACH/RECOVER는 28/4/27/110행이며 손가락 policy와 free4 residual의 기존 소유권을 보존한다. 속도·5 mm servo 보정을 재계산했고 다른 NumPy 환경의 보정 차이는 최대 1.74e−18 m였다. Native pick anchor 84개도 저장 실제 pose와 일치했다.
- 첫 열린 APPROACH 전 controls 77개·sampled native states 39개 및 해당 actor observation/action을 이전 waypoint-velocity와 대조했다. 이 prefix가 전체 궤적 동일성을 뜻하지 않는다. Native 입력 1,103개는 현재 파일 및 보존된 main 문서 2개로 연결되며 분석 7개·goal audit 6개 SHA도 일치한다.
- Zero-based event 0/1/2/3의 string 2 DOWN 적시·physical·accepted hit 4회와 timing +16.481113/−17.500996/−0.714421/−3.153205 ms를 확인했다. Scheduled recovery 완료 4회(1.516667/1.8/2.65/3.25초), release 8·miss 2·wrong crossing 4가 문서와 일치한다. Source terminal 3.633333초 뒤 physics와 카메라는 HOLD로 5초까지 계속된다.
- 기타 최대/종료 회전 43.828938°/43.582017°, 위치 46.353646/28.668464 mm와 region 전체 153/300·PLAY 107/169를 대조했다. RH:pinky3의 첫 양의 raw-lambda 기록은 3.633333초이며 최대 24.441927이다. Terminal 및 HOLD 기울기와의 동시 관측을 접촉 인과성으로 해석하지 않는다.
- PNG 302개 SHA/시점/읽기 전용 capture 기록, MP4 2개 SHA와 actual ffprobe(1280×720, 151프레임, 30 fps, 5.033333초), 대표 terminal hands/종료 whole-body 이미지를 확인했다. 문서의 hit control 시각과 직후 카메라 프레임 구분도 정합하다.

검수 SHA256: runner `bdf142469647b884a3844d99730f57334c7158390f5fec5ab6b9224a534f00e9`, wrapper `10c4aa9d5a8ec2e85bc0fb2be5189636b5bcadb1e9be2b2ff6e10199313d1e31`, analysis summary `38b6a5304f8a006714ce140bcc291b211c5c9301807aebbf20fbb85c59c9ab75`.

한계: 적시 타현·회복 진전 4회는 전체 곡 완주나 종료 후 안정성의 인증이 아니다. Source drive 동등성·접촉 원인·HOLD 안전 후퇴 효과는 확인되지 않았다. 후속 terminal-retract는 별도 단계이며 Root 최종 보존 감사·봉인 완료를 이 기록에서 주장하지 않는다.
