# 전신 세 시점 접촉 시각화 코드·원자료 최종 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 원래16초물리결과를그대로재현하고실제contactfeature를세native카메라에정합적으로투영했다. 산출물복사/최종문서/봉인감사는후속단계다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 물리 재현과 입력 보존

- Native는3840physicsstep/16초완료,forbidden0/inputs_unchangedTrue다. 원래chest_left_grip_cycle/native의initial_values·전체60Hztrace·3840actualcontacts가JSON값뿐아니라파일바이트도같음을직접확인했다. 새카메라/조회가물리결과를바꾸지않았다.
- Nativebefore1288개입력을현재파일과직접대조해변경0이었다. wrapper의source/leaf/reference/config/설치primary문서beforemap과원래helper/config/XML전체mesh/물성pin구조를유지한다. 기존실험/제어/데이터를수정하지않는다.
- Worldfeature는actualhuman–Gquery만사용한다. rawbody0/body1이름과localPos순서를따라각bodypose를적용하고G쪽feature를표시하며raw행/positiveλ/두featuregap을남긴다. read-onlynativeeq와render-preserveflags가있다.

## 좌표·카메라 독립 대조

-481프레임의7912개표시G-sideworldpoint전체를독립계산했다. initial고정G링크offset+현재nativeGrootpose에서재구성한point와최대차이는3.24×10⁻7m다. Nativefloat링크pose재구성범위와일치한다. 기록에있는humanbodypose6769개feature는직접local→world대조에서차이0이었다. 누락된human말단pose까지직접검증했다고주장하지않는다.
- 모든rawlambda는finite/nonnegative이고positiveflag가실제λ>0과일치했다. 두bodyfeaturegapmax는.000141880mm다. 이는feature좌표일관성검사이며압력/접촉면적/침투깊이또는보정된힘N을뜻하지않는다.
- Frame별실제view/projection행렬로직접row-vector투영을재계산해세시점모든point가finite·camera전방·1280×720안에있음을확인했다.1443annotatedframe의out_of_frame은모두0이다.
- Front/side/top표시는각+Y/+X/거의수직위카메라에대응한다. 실제3.5초3view합본,5.333초정면및14초위frame을열어전신구도와body색/point위치를확인했다. 앞/옆/위모두잘린장면을전신으로오인시키는문제를발견하지못했다.

## 표시 의미와 실제 접촉

- 색은human부위별이며positiveλ채운원/zeroλ빈원이다. 고정7pxpoint와X-ray가림무시표시를형상아래footer에명시한다. 힘크기/압력면적이나음영처리된실제접촉patch로해석하지않는다. 같은group2mmvoxel병합은가독성표시만줄이며모든raw행은보존한다.
-3.5초는thumb/index와상완/오른허벅지positive,왼허벅지는zeroλfeature다.5.333초A해제중은오른허벅지query자체가없고왼thumb/index/pinky·왼허벅지·오른상완positive가보인다.14초는Chest/오른상완/오른허벅지이며왼손표시가없다. 이시각별요약이실제metadata와일치한다.
-7912는30fps표본의feature행수이며독립contactevent수나3840물리스텝수와같지않다. 원래240Hz검증과30fps시각화의coverage를구분한다.

## 영상·이미지·후처리 무결성

- Renderer의1451before입력현재SHA와1443annotatedPNG SHA를직접대조해모두일치했다. Native원본1443PNG를기록된capture.image_sha256과대조한가드가생산소비전에적용됐다.
- 실제ffprobe검사결과3개개별영상은1280×940,combined는1920×470이며모두30fps/481frame/16.033333초다.6snapshot은3840×940이고기록SHA/치수가모두맞다.
- Footer는native720높이밖에추가되며원본형상을가리지않는다. Combined영상은각패널을정확히절반축소해비율변형이없고개별fullresolution영상과fullresolution3viewPNG도남긴다.
- 직접physics추가실행은0회다. 이번결과는현재동작의실제접촉위치시각화이며기타초기pose유지성공·수동평형·힘폐쇄·곡연주성공을새로입증하지않는다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_contact_three_view_v1.py`: `63adc78e3b4dafaa7dd4206ee3cadb600ad9ab2ad8440b61193f0842d2ae0b08`
- `/home/ajou/yigyu/3/stability_adapter_2/render_contact_three_view_v1.py`: `23631c8ad5cbe99787016a588e0b5890a8ad23b203e13f52b383adc2b9990b73`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/reproduction.json`: `db7ce0c752fff0bdb7d02e79213e69aedafb1ab70b08fda402531b382227ac01`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/native_v1/report.json`: `81767023db34d1cfcc291968860bd948d2685015b97045de73bac14540888a06`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/visual_v1/report.json`: `97dda388ab3c9659c845be06a71dea4c752f4d9abf7efb07147de7bff06c2596`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/contact_summary_v1.json`: `db167327af64b939f800f95581dd2487523b0cc1233eeaa72e1ca0378a522fc5`
