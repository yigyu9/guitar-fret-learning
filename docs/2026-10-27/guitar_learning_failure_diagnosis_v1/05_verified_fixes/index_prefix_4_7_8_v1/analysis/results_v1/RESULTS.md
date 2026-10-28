# 검지 source4→7→8 실제 prefix 결과

원 각음 수용 기준의3개 AND: **False**. 네 첫시도 중3음 모두달성 0/4.

| 원 source | 달성/4 | clean/wrong | 물리/손목실패 | env0 음중표본 | body1/2/3 평균N | actual4 ° | target4 ° | wrist mm/° | candidate/wrong |
|---|---:|---|---|---:|---|---|---|---|---|
| event-000004/string-3/note-4 | 4/4 | 1.000000/0.000000 | 0/0 | 11 | 7.6808, 0.0000, 0.1468 | 39.2074, 16.8895, 54.4703, 24.0621 | 39.3069, 27.7555, 54.4847, 24.0676 | 0.8215, 0.2312 | [11, 0] |
| event-000007/string-2/note-7 | 0/4 | 0.000000/1.000000 | 0/0 | 46 | 10.5059, 0.0000, 4.7248 | 38.5366, 16.5732, 53.9877, 23.9995 | 39.3069, 27.7555, 54.4847, 24.0676 | 17.3911, 1.9275 | [0, 46] |
| event-000008/string-2/note-8 | 0/4 | 0.000000/1.000000 | 0/0 | 21 | 9.7058, 0.0000, 1.9862 | 38.9104, 16.7375, 54.1573, 23.9728 | 39.3069, 27.7555, 54.4847, 24.0676 | 18.0258, 2.1135 | [0, 21] |

| source | 음중 CPU6gate | 몸체별 wrong flag합계: other_higher/fret/string | 해당음창 source4 candidate |
|---|---|---|---|
| event-000004/string-3/note-4 | [11, 11, 11, 11, 11, 0] | [0, 0, 0] | 11 |
| event-000007/string-2/note-7 | [46, 0, 0, 0, 0, 46] | [0, 46, 46] | 46 |
| event-000008/string-2/note-8 | [21, 0, 0, 0, 0, 21] | [0, 21, 21] | 21 |

4 episode 원9보상 키/finite 확인; reward−9항합 최대잔차 5.83786743e-07. dtype/physics수/9항·합계규모 기반 float32 참고척도 이내: True(정식상쇄오차증명·새음악gate 아님).

wrong flag는10몸체별합계로동시중복가능하며candidate개수/접촉쌍인증이아니다. 원6gate 순서는 loaded/position/position_facing/positive/candidate/wrong이다.

원67행과선택3음/offset2.4497/354tick상한을보존했다. 각음수용기준은기존4/4·clean≥.70·wrong≤.10·fail0이고전체는세개AND이다. 다른finger5/6/9/10 제외조건부/noNN/고정기타/동일seed7의4환경이다. 9보상은각episode원합계이며음별재분배하지않았다.

목표wrist는Aend→B공유press 사이선형전환, 원2초초기ramp/quat/arm12/선택4reference는유지한다. source7/8무음gap에서강제해제하지않았다. 원native released/release_s와60Hz candidate-off는 comparison.json에별도보존했으며해제를새성공gate로쓰지않았다.

CPU6gate·nearest scalar잔차·팔requested/target/actualbounds·PIP/DIP실제각/목표gap은comparison.json에기록했다. env0의60Hz자료범위이며다른3환경상세힘/nativeqd/240Hz기하나접촉쌍·현압력은추정하지않는다. 단음긍정자료와이번3음전환결과를구분하며NN학습·자유기타/J33·전곡·자연성·생산채택으로확대하지않는다.
