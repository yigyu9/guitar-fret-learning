# 자세 실험 영상 보관 · v2

이 v2는 이미 복사된 영상을 다시 쓰지 않고, manifest v1에서 발견된 source→destination 대응 오류만 수정합니다. v1에는 22행이 있었지만 목적지는 4개뿐이어서 과거 진단 영상 18개가 native 12 후보 파일로 잘못 연결되어 있었습니다. v2는 세 원본 manifest의 source SHA·label·view와 provenance v1의 61개 복사 기록에서 각 실제 destination을 다시 결합했습니다. 새 manifest에는 22개 고유 source와 22개 고유 destination이 있으며 source SHA, copy SHA 및 실제 파일이 모두 일치합니다.

완료 영상은 후보 native 11/12 전신·손 4개와 이전 완료 진단 시험 1–7·9–10 전신·손 18개입니다. 후보는 동일 초기조건의 5초 유지 자료일 뿐, 움직이는 연주 강건성이나 학습 성공이 아닙니다. 과거 시험의 해석은 [v2 영상 INDEX](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md)와 [자세 설명 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md)에 정리했습니다.

미완료 native 8은 첫 step assertion 실패로 physics 0, 1 frame/약0.034초입니다. 완료 영상 22개에 넣지 않았습니다. [원본 whole_body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/whole_body.mp4), [원본 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/hands.mp4).

[정정 manifest v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json) · [v2 입력·보존·출력 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/provenance_v2.json). v1 files, MP4 bytes와 source 실험 자료는 변경하지 않았습니다.
