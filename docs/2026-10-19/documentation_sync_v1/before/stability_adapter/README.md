# StabilityAdapter 기본 환경 실행과 검증

공용 humanoid와 기타의 초기 배치에 원본 스트랩을 연결한 새 기본 환경이다.
기타 고정은 해제했고 humanoid root와 기준 자세는 유지한다. 정책 없이 3초 WAIT만
실행하며, REACH·GRIP·TRANSPORT·보상·PPO는 아직 구현하지 않았다.

## 파일 역할

- `base_config.json`: 공용 자산 경로, 시간 간격, 노이즈, 자세 유지 계수, 원본 스트랩 설정.
- `environment.py`: 장면 생성, 물리 텐서, 초기화·부분 reset, 자세 유지, 스트랩 힘 적용, WAIT 시간.
- `strap.py`: quaternion 회전과 당기는 힘만 발생시키는 스트랩 계산.
- `run_base.py`: 물리 검증, 보고서·상태 기록, 깊이 기반 가림을 적용한 검은 스트랩 렌더.
- `tests/test_strap.py`: 힘·모멘트 보존, 느슨한 스트랩, 감쇠·장력 상한·배치·퇴화 구간 검사.

기존 StabilityAdapter 구현을 실행하거나 상속하지 않는다. 공유 모델·자세·gain 데이터와
검토한 원본 스트랩의 경로·물리 수식만 사용하며 외부 백업은 실행 의존성이 아니다.

## 실행 방법

프로젝트 루트에서 `rl38` 환경으로 실행한다. 이 단계는 학습 명령이 아니다.

```bash
conda activate rl38
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR=/tmp/torch_extensions_stability_adapter
python -m stability_adapter.run_base --render --out docs/2026-10-12/results/base_environment_v1/final
```

노이즈와 부분 reset 검사는 `--num-envs 8 --noise`로 실행한다.
별도 출력 폴더를 지정하면 기존 결과를 덮어쓰지 않는다. 검사가 실패하면 보고서를
저장한 뒤 종료 코드 1을 반환한다. 단위 테스트는 다음과 같다.

```bash
python -m unittest discover -s stability_adapter/tests -v
```

## 검증 결과와 보완 사항

2026-10-05 GPU 물리 실행 결과다. 단일 환경 16개, 노이즈 8개 환경 21개 검사와
스트랩 단위 테스트 7개가 통과했다. 초기 속도 0, 원본 관절 자세와 목표 자세,
위치 노이즈 축별 ±2mm·회전 축별 ±0.5°, 3초 WAIT, 유한한 상태, 고정 root,
스트랩 장력과 다른 환경을 보존하는 부분 reset을 확인했다.

공용 gain 그대로는 3초 동안 최대 관절 오차가 3.44°로 자세 유지 검사를 실패했다.
상체의 복원 강도를 6배, 감쇠를 √6배로 조정하되 기존 토크 상한과 초기 자세는
유지했다. 최종 최대 오차는 단일 환경 0.97°, 노이즈 8개 환경 0.94°였다.
이는 기준 자세 유지용 설정이며 향후 제어 관절의 학습 성능을 검증한 값은 아니다.

기타 실제 로드 질량은 약 4.65kg이다. 이전 실험의 3kg 보정은 사용하지 않는다.
최대 스트랩 장력은 단일 환경 약 60N, 노이즈 8개 환경 약 54N이었다.
원본 모델의 보이지 않는 엄지 지지 proxy는 충돌에서 제외했으며 실제 넥·손 충돌은 유지했다.

결과는 `docs/2026-10-12/results/base_environment_v1/`에 있다. `baseline/`은
자세 유지 검사에 실패한 비교 기록이고 `final/`과 `noisy8_validation/`이 통과 결과다.
영상은 무자막 30fps·90프레임·3초이며 첫 장면은 첫 제어 step 이후인 1/60초,
마지막 장면은 정확히 3초 상태다. 초기 상태값 자체는 물리 진행 전에 보고서에 저장한다.

공용 모델에서 visual geom 로드 경고 6개가 남아 있고 일부 외형은 단순 형상으로 보인다.
짧은 WAIT 검증은 장시간 무충돌 실행이나 세그폴트 해결을 보장하지 않는다.
접촉 부위·힘 진단, 초기 관통 판정, 33관절 제어와 접근·그립 성능은 다음 단계에서 검증한다.
