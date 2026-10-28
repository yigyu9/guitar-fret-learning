# staged release→이동→재압현 실제 결과

각음 원acceptance3개 AND: **True**,3음모두달성 4/4. 원4episode/12note·9보상·354tick상한을보존했다.

| source | 닫힌이동 달성/4 | staged 달성/4 | staged clean/wrong | env0 distal 평균N | wrist mm/° |
|---|---:|---:|---|---:|---|
| event-000004/string-3/note-4 | 4/4 | 4/4 | 1.000000/0.000000 | 0.146849 | 0.821488/0.231189 |
| event-000007/string-2/note-7 | 0/4 | 4/4 | 1.000000/0.000000 | 0.242059 | 1.005731/0.473061 |
| event-000008/string-2/note-8 | 0/4 | 4/4 | 1.000000/0.000000 | 0.296612 | 1.094760/0.300778 |

| env | A release 원latch/time(score) | release중 A off/loadedoff 최초clock | move중 B off/loadedoff 최초clock | 최초censor |
|---|---|---|---|---|
| 0 | True / 5.641366667 | 766 | 785 | None |
| 1 | True / 5.641366667 | 766 | 785 | None |
| 2 | True / 5.670533333 | 773 | 785 | None |
| 3 | True / 5.637200000 | 765 | 785 | None |

원native released/release_s는240Hz판정그대로이며candidate/assigned-loaded off사건과별도이다. 중간사건없음도분모/음악성과에서제외하지않는다. N은A-reset사례의distal-negative목표로, proximal하중/geometry가남을수있고피부전체분리나현압력을증명하지않는다. 원release창/음시계·성공기준은늘리지않았다.

목표일정은.10s손가락N/A손목유지→.4417s N유지/wristAtoB→.12s원reference/B손목유지이다. Cartesian목표속도44.6176→66.8405mm/s와손가락일정을함께바꿨으므로효과를해제하나의인과로확정할수없다. joint4rad/s·wrist .5도cap/gain/range/원105PD·90쌍은유지한다. 실제60Hz 요청/target/q·firstmask/rate및240집계의내부clock/censor를대조했다. 저장하지않은240sample을재생했다고주장하지않는다.

원6gate/10body×3wrong원인·각도/PIPDIP·force·팔경계·원A candidate잔존은comparison.json에기록했다. 본문힘/손목상세는env0 60Hz,4환경selectedq는추가bounded60Hz자료이다. bodyforce는pair압력이아니며NN학습/자유기타/J33/전곡/자연성/생산채택으로확대하지않는다. source/raw/원1215producer를수정하거나새GPU를실행하지않았다.
