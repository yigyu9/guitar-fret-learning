# assets/ — 전신 파이프라인용 확정 에셋 (2026-07-07)

전신 기타 연주 환경이 사용하는 에셋의 단일 출처다. 휴머노이드와 기타는 분리 액터로 로드한다.

| 파일 | 내용 | 출처 / 재생성 |
|---|---|---|
| `smpl_mpl_hands_body.xml` | SMPL 전신 + MPL 디테일 손 결합 휴머노이드 (66바디/106관절/73.3kg, 자유 root Pelvis) | `guitar/assets/smpl_mpl_hands_body.xml` 사본. 재생성 = `guitar/assets/merge_hands.py` |
| `guitar_asset.xml` | 독립 기타 (프렛 22 박스 + 너트 + 현 마커 12 + 시각 캡슐 6 + 넥 메시 + 바디 박스 + G:pluck_range). 로컬 프레임 = identity — **앵커 포즈는 env config에서 주입** (정본 O4: pos `0 0 0.89`, quat `0.5573 -0.18685 0.57969 0.56433`) | `smpl_mpl_hands_guitar_o4.xml`의 guitar 서브트리 추출 (파일 헤더 주석 참조) |
| `mesh/` (37개) | MPL 손 STL 34 + 넥 OBJ 2(winding 수정본, 2026-07-07) + wristx.stl | `guitar/assets/mesh/` 사본 |

## 주의
- **이 디렉토리에는 최종 사용 파일만 둔다** — 검증용 결합 씬(seated_scene*.xml), 태그별 자세, 테스트 리포트 등 재생성 가능한 산출물은 `../_gen/`에.
- **humanoid XML의 zero-width 관절 range 8개**(L/R Knee·Toe y/z): MuJoCo 3.x는 로드 거부(ε-확장 필요), **Isaac Gym은 정상 로드** — 학습에는 영향 없음(기존 F1 0.918 검증).
- **G1(자유 기타) 전 필요 작업(P7)**: G:string* 마커 바디가 질량 0 — free actor 로드 전 관성 부여·확인. `guitar_asset.xml` 헤더 주석 참조.
- 손 geom `condim=1`(무마찰)은 XML 선언일 뿐 Isaac PhysX가 무시할 수 있음 — P2에서 실측.
- Isaac Gym 로드 시 `fix_base_link`: 기타 G0=True, G1/G2=False. 휴머노이드=False.
