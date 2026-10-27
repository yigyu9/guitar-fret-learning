# 연구에 사용하는 기타와 휴머노이드

2026-10-13에 프로젝트의 실제 자산과 저장된 물성 자료를 확인해 정리했다. 현재 형상은 **OM 바디 기타**와 **하체가 고정된 81관절 휴머노이드**다. 이 디렉토리는 모델 사양과 파일 사본을 모으며, 진행 중인 자세 실험이나 제어 설정을 변경하지 않는다.

## 문서와 실제 파일

| 자료 | 내용 |
|---|---|
| [기타 사양](/home/ajou/yigyu/3/paper/object/GUITAR.md:1) | 도면 기반 외형, 치수, 충돌 형상, 넥·프렛·현, 질량·관성과 좌표 |
| [휴머노이드 사양](/home/ajou/yigyu/3/paper/object/HUMANOID.md:1) | 몸통·팔·손 구조, 105→81관절 변경, 신체 치수, 질량과 충돌 |
| [81관절 표](/home/ajou/yigyu/3/paper/object/JOINT_SPECIFICATIONS.md:1) | 관절별 로컬 축, 각도 제한과 XML의 gain 선언 |
| [기계 판독용 사양](/home/ajou/yigyu/3/paper/object/specifications.json) | 관절, body 계층, 형상, 치수와 저장된 native 물성 |
| [원본·사본 대응](/home/ajou/yigyu/3/paper/object/provenance.json) | 각 파일의 원래 위치, 사본 위치, SHA-256과 크기 |
| [검증 결과](/home/ajou/yigyu/3/paper/object/verification.json) | 파일 일치, 모델 의존 경로, 관절 수, 문서 링크 확인 |

현재 모델 사본:

- [OM v3 기타 XML](/home/ajou/yigyu/3/paper/object/models/stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml)
- [하체 고정 휴머노이드 XML](/home/ajou/yigyu/3/paper/object/models/stability_adapter_2/assets/humanoid_fixed_lower.xml)

비교용 원본 사본:

- [기존 기타 XML](/home/ajou/yigyu/3/paper/object/models/tab2body/assets/guitar_asset.xml)
- [원본 105관절 휴머노이드 XML](/home/ajou/yigyu/3/paper/object/models/tab2body/assets/smpl_mpl_hands_body.xml)

## 사본을 여는 방법과 범위

`models/` 안에 프로젝트의 상대 디렉토리 구조를 유지했다. XML 4개와 이들이 선언한 메시 의존 파일을 포함한 108개 파일은 원본과 바이트 단위로 같다. **XML만 따로 옮기지 말고 `models/` 전체를 함께 옮겨야 한다.** 기존 넥·손 메시와 OM 바디 충돌 메시의 상대 경로가 함께 유지된다. 원래 실행 경로는 이 사본을 사용하도록 바꾸지 않았다.

사본은 모델 자산 묶음이다. 시뮬레이션 실행 코드, checkpoint, 초기 자세 선택, 충돌 필터 설정, runtime 질량 보정은 포함한 자산만으로 자동 재현되지 않는다. `evidence/`에는 확인에 사용한 기존 XML manifest·native readback·초기값·출처 문서를 복사했다. 이 JSON 안의 절대 경로와 과거 생성 의존성은 원자료의 이력이며, 이동한 사본의 실행 경로로 재작성하지 않았다.

## 사양을 읽는 기준

1. **XML/메시 사양:** 현재 형상의 크기, body 계층, 관절 범위와 선언값이다.
2. **저장된 native 물성:** `left_neck_near_initial_v1/native_hold_v4`에서 실제로 읽은 질량·COM·관성·shape 속성이다. 기타 외형의 재질이나 실물의 실측값을 뜻하지 않는다.
3. **실행별 제어:** PD gain, POSITION/EFFORT 소유 관절, 스트랩, 초기 q/p/quaternion은 실험별 조건이다. 진행 중인 실험의 최신 제어 설정을 모델 고유 사양으로 고정하지 않는다.

원본 자산·기존 실험·메인 스레드의 코드와 설정은 변경하지 않았다. 출처 표기는 [복사한 기타 attribution](/home/ajou/yigyu/3/paper/object/evidence/guitar_ATTRIBUTION.md:1)과 [원본 자산 설명](/home/ajou/yigyu/3/paper/object/evidence/original_assets_README.md:1)을 함께 보존한다.
