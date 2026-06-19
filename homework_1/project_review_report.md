# 🛠️ CodeBuddy 최종 코드 리뷰 리포트

## 분석 대상: mutl_center.py

## 🔴 높은 심각도 (보안 취약점 위주)

### OWASP A03:2021 – Injection / A04:2021 – Insecure Design

**[라인: main() 함수 내 `n = int(input(...))` 및 `c = int(input(...))`]**
- **문제:** 사용자 입력값을 검증 없이 바로 `int()`로 변환합니다. 매우 큰 수(예: 10,000,000)를 입력할 경우 O(n²) 엣지 생성으로 인해 메모리 고갈 및 서비스 거부(DoS) 상태가 발생할 수 있습니다. 이는 입력 기반 리소스 소진 취약점입니다.
- **수정 제안:**
```python
MAX_VERTICES = 1000  # 상한선 명시적 제한

n_str = input("정점의 개수를 입력하세요: ").strip()
if not n_str.isdigit():
    print("숫자만 입력하세요.")
    return
n = int(n_str)
if not (1 <= n <= MAX_VERTICES):
    print(f"정점 수는 1 이상 {MAX_VERTICES} 이하여야 합니다.")
    return
```

---

**[라인: `except Exception as e: print(f"오류가 발생했습니다: {e}")`]**
- **문제 (OWASP A09:2021 – Security Logging and Monitoring Failures):** 예외 발생 시 단순 출력만 하고 로깅이 전혀 없습니다. 실제 운영 환경에서는 침해 탐지 및 사후 분석이 불가능합니다. 또한 예외 메시지를 그대로 사용자에게 노출하면 내부 구조가 드러날 수 있습니다.
- **수정 제안:**
```python
import logging

logging.basicConfig(
    filename='app_security.log',
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s %(message)s'
)

except Exception as e:
    logging.error("예상치 못한 오류 발생", exc_info=True)
    print("오류가 발생했습니다. 관리자에게 문의하세요.")  # 내부 정보 비노출
```

---

**[라인: `import matplotlib.pyplot as plt` – 모듈 최상단이 아닌 중간 삽입]**
- **문제 (OWASP A05:2021 – Security Misconfiguration / A06:2021 – Vulnerable and Outdated Components):** `matplotlib`은 외부 라이브러리로, 파일 상단에서 일괄 임포트하지 않으면 의존성 관리가 어렵습니다. 또한 버전 고정 없이 사용하면 알려진 취약점이 있는 버전이 설치될 수 있습니다.
- **수정 제안:**
  - 모든 import를 파일 최상단으로 이동
  - `requirements.txt`에 버전 명시: `matplotlib==3.9.0`
  - 선택적 의존성은 try/except로 처리:
```python
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
``` ## 🟡 중간 심각도 (구조적 버그)

**[find_centers 함수 – `dp` 변수 스코프 오염]**
- **문제:** `can_place_centers()` 내부에서 사용한 `dp` 배열이 외부 `find_centers` 스코프의 `dp`와 충돌합니다. 내부 함수 `can_place_centers`의 `dp`는 지역 변수로 선언되어야 하는데, 이진 탐색 이후 `place_centers`에서 동일한 `dp` 변수를 재사용하면서 이전 탐색 결과 잔재값이 남아 잘못된 센터 배치가 발생할 수 있습니다.
- **수정 제안:** `can_place_centers` 내부에 독립적인 `dp_local = [0] * n`을 명시적으로 선언하고, `place_centers`에서는 별도 초기화된 `dp`를 사용합니다.

---

**[assign_centers 함수 – BFS 거리 계산 정확도]**
- **문제:** BFS는 일반적으로 가중치 없는 그래프에 적합하나, 여기서는 엣지 가중치(유클리드 거리)가 있습니다. 가중치 그래프에서 BFS를 사용하면 최단 거리가 보장되지 않습니다. 다익스트라(Dijkstra) 알고리즘을 사용해야 합니다.
- **수정 제안:**
```python
import heapq

def assign_centers(n, mst, centers):
    assignments = [None] * n
    distances = [math.inf] * n
    heap = []
    for idx, center in enumerate(centers):
        heapq.heappush(heap, (0, center, idx))
    while heap:
        dist, u, idx = heapq.heappop(heap)
        if dist < distances[u]:
            distances[u] = dist
            assignments[u] = idx
            for v, w in mst[u]:
                if dist + w < distances[v]:
                    heapq.heappush(heap, (dist + w, v, idx))
    return assignments, distances
```

---

**[find_centers 함수 – 재귀 깊이 제한 없음]**
- **문제:** `dfs()`와 `place_centers()`는 재귀 함수이며, Python 기본 재귀 한도는 1000입니다. 입력 정점이 많을 경우 `RecursionError`가 발생합니다. `sys.setrecursionlimit()`을 임의로 높이는 것은 스택 오버플로우 위험이 있습니다.
- **수정 제안:** 재귀를 명시적 스택 기반 반복문으로 교체하거나, 입력 n 제한을 충분히 낮게 설정합니다.
