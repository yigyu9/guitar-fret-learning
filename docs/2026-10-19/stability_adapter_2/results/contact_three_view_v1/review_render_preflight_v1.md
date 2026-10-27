# 세 시점 접촉 표시 후처리 사전 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 후처리는기록된nativeRGB/접촉feature/실제카메라행렬만사용하고시뮬레이터상태를변경하지않는다. 실행후실제원본과overlay위치·영상시간·프레임을검증해야한다.

## Critical

없음.

## Warning

없음.

## Suggestion

- `/home/ajou/yigyu/3/stability_adapter_2/render_contact_three_view_v1.py:44`: 병합은2mm격자cell양자화이며점간Euclidean거리≤2mm인정확한중복제거는아니다. 표시를위한같은group별2mmvoxel병합이라고설명하고원래rawcontact행은모두남긴다는범위를유지한다.

## 좌표·표시 검토

-38–40행: 이미정규화nativepose에서world로변환한point를기록된nativeview/projection행렬에기존project함수의row-vector규약으로투영한다. y화면좌표반전과camera전방/finite/화면내guard를유지한다. 기타pose를새로추정하거나원점COM을섞지않는다.
- 같은group/cell에서는positiveλ점을우선선택하고rawmetadata를변경하지않는다. Marker는고정radius7px/외곽9px이며양의lambda는채운원/0은빈원이다. 크기나색을힘N·접촉면적으로해석하지않는다.
- Native1280×720영역아래별도footer를붙여1280×940로만든다. legend/title/text가형상을가리지않고X-rayalways-visible임을명시한다. 실제폰트폭을측정해주문구661px/하단873px로가로1280안에들어감을확인했다.
- Encode는3개1280×940영상과640×470패널3개를연결한1920×470combined를출력한다. 비율변형이없고개별fullresolution영상도남긴다. Snapshot6개는최신코드에서3840×940fullresolution3view정렬이다.

## 입력·시간·검증 구조

-95–102행:481contactframes의step0..3840(step8),clean3840step/16초native완료,카메라/state보존,원래initial/trace/actualcontacts exact재현을요구한다. 실패/부분재현을실제동일영상으로표시하지않는다.
-103–111행: source/helper/font/report/reproduction/contactmetadata/capture와raw1443PNG를사전pin하고각PNG를원래capture.image_sha256과대조한다. 권장했던입력무결성gap이생산소비전에해소됐다. 성공시전체사후SHA도다시검사한다.
- Raw→overlay각frame의물리step과이미지index는연속성을앞서검사해일치한다. 선택snapshot15/105/160/195/315/420은.5/3.5/5.333/6.5/10.5/14초다. 정지scene을복제하거나마지막프레임을연장하지않는다.
- Encode는ffmpeg-n으로기존영상덮어쓰기를차단하고ffprobe481frame및count/30길이를확인한다. Native물리재실행을후처리에서하지않는다.
- 최종보고는rawcontact개수와표시된feature개수를구분하고전체worldfeature두body간gap통계를기록한다. 그gap은두feature간분리/solver상태를포함할수있으므로전부변환식오류라고단정하지않는다.
- 새PythonAST통과. 리뷰어는production후처리/물리실행을하지않았다. 실제projection위치·시점구도·pointgroup별색·캡션및최종coverage는산출후검수대상이다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/render_contact_three_view_v1.py`: `23631c8ad5cbe99787016a588e0b5890a8ad23b203e13f52b383adc2b9990b73`
- `/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py`: `a52a33eecdb943d0acbc7faffa51816ab47447c7a9c48d4036e8dd70fb7353f3`
- `/home/ajou/yigyu/3/stability_adapter_2/gym_trial_recording.py`: `f60897a175b88d8be620708f11e1fe52d61df73ef31c490fd1fda3cc8c43fb22`
- `/home/ajou/yigyu/3/stability_adapter_2/CONTACT_THREE_VIEW_PLAN_V1.md`: `2d3348158dee35be2ac3aabc0f321cd168015a80e118170e0737ba322f8ce87c`
