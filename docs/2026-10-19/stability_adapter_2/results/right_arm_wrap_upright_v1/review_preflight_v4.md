# 상완45%·Thorax 완화 V3 변경 사전 검수

요약 판정: **문제없음**. **Critical: 0 / Warning: 0 / Suggestion: 0**. Source V3 CPU 탐색으로 진행 가능하다. 새 V3 변경만 검수했으며 이전 scope/source/native를 다시 실행하지 않았다.

## 확인 근거

- [search_right_arm_wrap_upright_v3.py:59](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:59): 기존12/20/24° 몸통 목표에 초기 기타 inset10/25/35mm를 적용한다. Hip 높이 함수·actual delta·상대 hand/elbow 목표와 나머지 bounds/보존 계약은 기존 방식이다. 새 leaf의 현재 조건과 일치한다.
- [search_right_arm_wrap_upright_v3.py:84](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:84): 상완 근위 segment를0~45%로 바꾸고 final 측정도45%다. Thorax0.8mm 강제 근접 잔차·최대4mm 수락·Thorax negative G_X 조건은 제거됐고 최소 비겹침 잔차/capsule gate는 남는다. Chest30mm·Torso/Spine20mm·전완12mm·whole source clear·waist·natural/model/finger 조건은 유지된다.
- [search_right_arm_wrap_upright_v3.py:119](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:119): 별도 `proximal_upper_arm45_witness`·`.45` fraction·legacy note를 추가한다.30/65 키는 같은 실제45 witness의 호환 alias라고 명시한다. 기존 controller가30 키를 읽어도 실제 witness/local goal을 사용하므로 실행은 연결되지만 결과를30/65% 측정이라고 설명해서는 안 된다. 새 분석기의45% 통계를 사용한다.
- [search_right_arm_wrap_upright_v3.py:123](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v3.py:123): 새 config의 Thorax cap10N/depth4mm와 상완10N/4mm가 계획과 같다. `right_block_effort_v6.py`가 허용하는 `(10,.004)` 조합이며 K/D·body9 PD/gravity·left 추종·model effort cap·81 목표를 바꾸지 않는다. 이는 실제 human virtual request 설정 변경이며 측정된 접촉력이나 기타 직접힘으로 설명하지 않는다.
- [analyze_right_arm_wrap_upright_v3.py:30](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_upright_v3.py:30): 실제로 읽는 fixed-lower XML을 before/after 입력 SHA에 추가했다. R_Shoulder의 첫 geom은 비영 `fromto` 축의 capsule이어서 native contact local 좌표를 같은 축에 투영할 수 있다.98~105행은 body0/1의 실제 shoulder localPos를 골라 raw0~45와 endpoint-clamped0~45 및 positive raw lambda를 따로 분류한다.45 분류가 기존30 통계를 덮어쓴 것은 아니다. trunk/Chest raw와 uniform G39 translation 방식은 유지된다.
- 원래 readonly wrapperV2는 SHA 불변이다. Source의 leaf 및 모든A Python before pin에 새 V3 source/분석기가 포함된다. Source1/2와 consumed 파일을 수정한 변경은 아니다.

## 검증과 제한

새 source/분석기 AST 및 controller 지원 설정 대조 통과. R_Shoulder capsule 축 존재/길이>0 확인. 검수 시 `search_v3` 출력은 없었고 Source/native/producer를 실행하지 않았다. 실제 source 수락·상완45 접촉·trunk 지지·정지/파동 성능은 후속 검증이다. raw45와 clamp45를 원자료 의미대로 보고하며 지속 감싸기·Thorax 접촉·손 없는 유지·연주 성공을 선험적으로 인증하지 않는다.

검수 SHA256:

- Plan V3: `6f9f22a49e3a165c84b1f4f7bae87ee9b2cbd48730e1ac302fcced264f451468`
- Source V3: `50293fd37a4d55486518419d39cdbab1c1fffb65f3fd3dfa9e8c594e1bbb6e80`
- 분석기 V3: `5d800036446619eb8459aad2ee99b9e88cf1fe7895a8d72b67d807f8fe8ab07b`
- unchanged wrapperV2: `773f7f982c5f8dc5075839bfe373b75ae184210ddfa9cd45fec920696a504ee1`

지정된 이 검수 파일만 생성했고 다른 담당자 파일은 수정하거나 되돌리지 않았다.
