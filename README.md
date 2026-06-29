# 제품 DB 매칭 엔진 (SG_proj_012)

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI_MCDA-orange)

## 1. 개요
MCDA(AHP/TOPSIS) 기반 다중 목적 최적화 기법을 사용하여 기성 제품을 추천하는 엔진입니다.

## 2. 시스템 아키텍처
```mermaid
graph TD
    A[Matching Request] --> B[MCDA Engine]
    B --> C[Score: Surface Energy 60%]
    B --> D[Score: Roughness 20%]
    B --> E[Constraint: Processability 20%]
    C --> F[Ranking & Selection]
    D --> F
    E --> F
    F --> G[Top 3 Recommendations]
```

## 3. 기술 스택
- Backend: FastAPI, Python 3.10
- Algorithm: AHP / TOPSIS

## 4. 참조 문서
- ADR-0001


---
## 5. 알려진 한계 및 추후 보정 과제 (Known Limitations & Future Adjustments)
- 현재 제품 매칭 알고리즘(matcher.py) 내 점수 가중치(표면에너지 0.6, 조도 0.2, 가공성 0.2) 및 특성별 오차 보정 상수(표면에너지 2, 조도 20, 가공 가혹도 10)는 초기 정합성 유도를 위해 임의로 하드코딩된 휴리스틱(Heuristic) 상수입니다.
- 추후 실측 데이터와 필드 테스트 결과를 확보하여, AHP/TOPSIS 다기준 의사결정 모델에 부합하는 일관성 지수 및 객관적인 가중치 도출 수식으로 전면 대체할 예정입니다.

---
*Updated by System: 2026-06-29 (Resolved 260627 Analysis Report priority issues)*

---
*Updated by System: 2026-06-29 (Matching DB Integration Completed)*
## 최신 업데이트 내역 (2026-06-29)
- 의사결정 모듈의 다기준 매칭 상수를 기재하여 투명성 제고.
- 구동 중 발생하던 httpx 모듈 누락(ModuleNotFoundError) 해결을 위해 의존성 업데이트 반영.
