# 이전 Stability 실험 보관

현재 안내는 [설계·결과](../STABILITY_UNIFIED.md), [학습 커맨드](../../../stability_adapter/development/pinch_curriculum/README.md)다.

중간 실험325개 자료 중 최종·필수8개만 활성 폴더에 남겼다. 이전 상세 보고서와 중간 자료는
[압축 보관 파일](../../archive/stability_20260914_history.tar.gz) 하나로 통합했다.
정리 전362개 파일의 원본을 담고 있으며, 파일별 SHA256 대조로 보관본 내용을 검증했다.
압축 파일 SHA256: `3cae250fa5e14c3c06a267b746745c908f4e3ac334ed6d4769a2ecec709e5175`.

필요할 때 별도 디렉토리로 풀면 원래 프로젝트 상대 경로를 확인할 수 있다.

```bash
mkdir -p /tmp/stability_history_20260914
tar -xzf /home/ajou/yigyu/3/docs/archive/stability_20260914_history.tar.gz \
  -C /tmp/stability_history_20260914
```

보관 대상에는 이전25개 Stability 문서, PPO 전환 계획, 대규모 실행 분석, 측정 템플릿,
상세 통합 보고서와 문서용 실험 복사본이 포함된다. 보관 당시 수치·명령을 현재 설정으로 사용하지 않는다.
