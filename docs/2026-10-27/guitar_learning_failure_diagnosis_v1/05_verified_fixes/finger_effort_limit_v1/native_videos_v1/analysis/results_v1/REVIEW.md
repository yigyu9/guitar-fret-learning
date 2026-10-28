# 기존115/114 실제 영상 독립 QA

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

CPU에서136개 직접입력·841개 실제입력(836준비핀 포함) SHA를 확인했다. 분석 출력 쓰기를 메모리로 가로채4개 JSON/CSV/README 산출물이 exact 일치하는 것을 검증했다. 새4장면의 전체16평가·모든 통계는 원 실행과 같으며,878개 env0 raw의19공통필드는 시간 외 값·dtype가 모두 같다. cap selected native qd도 해당 fullqd 열과 같다. 시간만 각16값에서 최대4.440892e−16초 차이(/60 대/240 표현)이며 새 음악·물리 오차기준이 아니다.

8MP4 전부 ffprobe를 재실행해 h264·1280×720·30fps·검지110/중지109frame과 기록 JSON의 일치를 확인했다. 각각의 음중frame91을 메모리에서 다시 디코딩해 저장 PNG와 픽셀 exact 대조했다. 첫프레임 endpoint2/local1/30초·t0 없음·검지221번째 raw만 존재·중지218번째 마지막 frame 매핑이 맞다.4scene close/8encoder exit0·원90쌍·cap105전필드 readback 근거와 baseline 별도fullarray 미저장 범위를 확인했다.

두 contact sheet의32대표프레임 및 cap검지/중지 손·cap검지 전신 음중 원본을 직접 봤다. upright·머리와 양발 여백·손마디 굴곡 방향은 보이며 넥에 가린 부분이 있다. 모든 관절·해부학 자연성·실제 접촉 압력은 인증하지 않는다. README의8MP4·2sheet 링크는 실제 존재한다.

검지20Nm3/4·cap0/4 wrong100%, 중지각4/4 원결과가 그대로다. 기존115/114 env0 영상이며 새112·학습정책·4seed·4환경 전체영상으로 확대하지 않는다. 기존 nearest-height/native sample 한계도 유지한다. GPU/native scene·새 MP4 encoder/native render 실행과 기존파일 수정은 하지 않았다. 검토43파일 최종 SHA는 [review.json](review.json)에 기록했다.
