# 최신 왼손 사이클 산출물 최종 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 원래물리/영상은보존했고발견된비단위쿼터니언계산오류는새V2 CSV/그래프로수정했다. 최종선호문서는artifacts_v2/README_final_v1.md와영상README_final_v1.md의왕복연결이다. 최종봉인실행은root의후속단계다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 영상과 프레임 검증

-3MP4와4native손프레임을원본/복사/manifest SHA로대조해모두exact다. 직접ffprobe로3영상모두1280×720/30fps/481frame/16.033333초를확인했다. 물리16초에초기0초프레임을포함한길이이며마지막정착을freeze프레임으로만든자료가아니다.
-4PNG는각1280×720,실제frame105/195/315/420→3.5/6.5/10.5/14초다. 네장면비교PNG를직접열어원본손프레임과배치/캡션순서를확인했다. Thumb/index접촉과분리판정은이미지눈대중이아닌nativequery근거다. Caption은형상밖에있으며비물리적기타줄선표시를설명한다.
-기존V1물리/영상/원본프레임을수정하지않고새계산/문서만추가했다. V1와V2각24개입력의before/afterSHA및모든derived산출SHA가현재파일과일치함을확인했다.

## 발견한 수치 오류와 수정 검증

- V1producer는nativequaternion을단위화하지않고dot/rotation공식에넣었다. 전체최대값차이만작았으며전체시계열을독립대조하니최대pointwiseSO3오차.058342465°(.016667초CSV0대Scipy.058342465),BB오차.000247441mm가있었다. 반올림오차로만부르면안된다. 이V1 CSV/그래프는과거이력으로보존하고권위자료에서제외했다.
- 새V2는SciPyRotation.from_quat으로모든nativequaternion을정규화해실제endpoint와localBBcentre로재계산한다. 리뷰어가원시pose를다시읽어별도코드로3841개시점전체를대조했다. 최대절대차이는시간0,BB0mm,SO3약1.3×10⁻14°로수치허용오차1e−10이내다. Global최대도37.2875096278mm/14.5157322932°로기존권위분석과맞는다.
- 새CSV/그래프를실제V2생성후pin/manifest와대조했고그래프PNG도직접열었다. 첫해제의큰회전과후기재배치가숨겨지지않았다. 이과정에서물리재실행/접촉분석/원본영상변경은없다.
- Final_pose_summary도원래initial/finalrawpose로독립계산했다. 종료36.929892597mm/3.404356644°는전체peak37.288mm/14.516°와다르다. root문서가최대와종료/구간시작기준을구분한것이정확하다.

## 선호 설명과 링크 정합성

- RootREADME→새artifactfinal문서↔새videofinal색인의절대경로가연결된다. 세문서17개전체Markdown목표가모두존재하며기존요약으로되돌아가는stale권장링크가없다. 생성된V2README의상대링크는과거생성자료로보존하고최종문서가절대경로를사용한다.
- 준비0–2초의388/480왼손접촉과엄지/검지동시잡기0을구분하고,두hold는실제thumb3/index3동시positive360/360씩,두open은실제240/240및720/720free라고설명한다. 모든손가락이완전히펴지거나네손가락모두접촉했다는과장을제거했다.
- A/B평균유지손목넥축차이41.418mm를이동구간변위나대각분리포함전체extent119.794mm와구분한다. 마지막3초.445mm/.213°정착과전체37.288mm/14.516°변화를함께보존한다.
- Chest/상완/허벅지접촉의변경을설명하고rawlambda를힘N/힘폐쇄로해석하지않는다. 손grab/release수행은확인됐지만초기자세계속유지·강한안정성·학습곡성공으로확대하지않는다.
- 원래native1287beforepin과물리/코드검수결론은유지한다. AGENTS에추가된권장문서쌍과quaternion정규화/전체pointwise검사규칙은실수재발을줄이기위한문서갱신이며실제물리입력변경이아니다.

## 검수 SHA256

- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/README.md`: `090a085c982e281176408a9a543aaba337a11b8fc4acf4df7c16f530c953176d`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/README_final_v1.md`: `8af3293f3ae3375b2cd11eb92bd795f69a9dee5256cb2515f3aa3641cc1281e3`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/README_final_v1.md`: `04f206df40b47e5e053af88429c176dc39bdc62e7e96b9c23358d486261a960d`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/copy_manifest_v1.json`: `e8edf44d04be7365c415f6c0761cecd1530f5ba836586694a7c826514c54d07b`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/copy_manifest_v2.json`: `aa13eb95aa529236163109c9c3daebec79d134beaea69d0e4bca36674271f6ce`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/motion_samples_240Hz_v2.csv`: `53bc62892c4815212d416426ec92ead07602677463d08ad78ae042accbee2ffc`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/final_pose_summary_v1.json`: `9341551f7b24421bbd388e1166e1cec5b76ca39410023a7663b0da95cef1172c`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/final_document_v1.json`: `deb8787eece07bc326beb0a24dd881863d88c7f0a55701417e66cb490ebaa182`
