# 📝 코딩 스타일 가이드

> 작성일: 2025-12-28  
> 목적: Abiseu 프로젝트 코딩 스타일 및 규칙 정의

---

## 📋 목차

1. [Python 스타일 규칙](#python-스타일-규칙)
2. [타입 힌트](#타입-힌트)
3. [Docstring](#docstring)
4. [네이밍 규칙](#네이밍-규칙)
5. [에러 처리](#에러-처리)
6. [코드 구조](#코드-구조)
7. [주석 및 문서화](#주석-및-문서화)

---

## 🐍 Python 스타일 규칙

### 기본 원칙

1. **PEP 8 준수**: Python 공식 스타일 가이드 준수
2. **Black 포맷터 사용**: 자동 코드 포맷팅
3. **최대 줄 길이**: 100자
4. **들여쓰기**: 4칸 공백 (탭 사용 금지)

### 예시

```python
# ✅ 올바른 예시
class FirstPersonPOV(LightModule):
    """1인칭: 회사 내부자 관점"""
    
    def __init__(self, name: str, db_pool: DatabasePool):
        super().__init__(name)
        self.db_pool = db_pool
        self.initialized = False
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """재무 분석 수행"""
        if not isinstance(stock_code, str) or len(stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {stock_code}")
        return {"result": "analysis"}
```

```python
# ❌ 잘못된 예시
class FirstPersonPOV(LightModule):
    def __init__(self, name, db_pool):  # 타입 힌트 없음
        super().__init__(name)
        self.db_pool=db_pool  # 공백 없음
        self.initialized=False
    
    def analyze(self, stock_code):  # 타입 힌트 없음, docstring 없음
        if not stock_code:
            return None  # 계약 위반
        return {"result":"analysis"}  # 공백 없음
```

---

## 🏷️ 타입 힌트

### 필수 규칙

1. **모든 함수/메서드에 타입 힌트 필수**
2. **클래스 변수 타입 힌트 권장**
3. **복잡한 타입은 `typing` 모듈 사용**

### 예시

```python
# ✅ 올바른 예시
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

def analyze(
    self, 
    stock_code: str, 
    start_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """분석 수행"""
    pass

def get_stock_list(self) -> List[str]:
    """종목 리스트 조회"""
    pass

def calculate_value(
    self, 
    price: Union[int, float]
) -> float:
    """가치 계산"""
    pass
```

```python
# ❌ 잘못된 예시
def analyze(self, stock_code):  # 타입 힌트 없음
    pass

def get_stock_list(self):  # 타입 힌트 없음
    pass
```

### 타입 힌트 체크리스트

- [ ] 모든 함수 파라미터에 타입 힌트
- [ ] 모든 함수 반환값에 타입 힌트
- [ ] Optional 사용 시 명시
- [ ] Union 타입 적절히 사용
- [ ] 제네릭 타입 적절히 사용 (List[str], Dict[str, Any] 등)

---

## 📖 Docstring

### 필수 규칙

1. **모든 공개 함수/메서드에 Docstring 필수**
2. **Google 스타일 Docstring 사용**
3. **계약 정보 포함 (입력/출력/예외)**

### Docstring 템플릿

```python
def method_name(self, param1: str, param2: int) -> Dict[str, Any]:
    """
    메서드 설명 (한 줄 요약)
    
    상세 설명이 필요한 경우 여기에 작성합니다.
    여러 줄에 걸쳐 설명할 수 있습니다.
    
    Args:
        param1: 파라미터 1 설명
        param2: 파라미터 2 설명
    
    Returns:
        반환값 설명 (Dict with keys: 'key1', 'key2')
    
    Raises:
        ValueError: 잘못된 파라미터
        DatabaseError: 데이터베이스 오류
    
    계약:
    - 입력: param1은 str 타입, 6자리
    - 출력: Dict with keys: 'key1', 'key2'
    - 예외: ValueError (잘못된 param1), DatabaseError (DB 오류)
    
    사용 예시:
        ```python
        result = obj.method_name("005930", 100)
        print(result['key1'])
        ```
    """
    pass
```

### 클래스 Docstring

```python
class FirstPersonPOV(LightModule):
    """
    FirstPersonPOV 모듈
    
    1인칭 관점에서 회사 내부자처럼 재무 분석을 수행합니다.
    
    계약:
    - 입력: stock_code (str, 6자리)
    - 출력: Dict with keys: 'intrinsic_value', 'health_score', 'outlook'
    - 예외: ValueError, POVDataError
    
    의존성:
    - DatabasePool: 데이터베이스 연결 풀
    - LightModule: 기본 모듈 클래스
    
    사용 예시:
        ```python
        pov = FirstPersonPOV("first_person", db_pool)
        result = pov.analyze("005930")
        print(result['intrinsic_value'])
        ```
    """
    pass
```

### Docstring 체크리스트

- [ ] 모든 공개 함수/메서드에 Docstring
- [ ] Args 섹션 포함
- [ ] Returns 섹션 포함
- [ ] Raises 섹션 포함 (예외 발생 시)
- [ ] 계약 정보 포함
- [ ] 사용 예시 포함 (복잡한 경우)

---

## 🏷️ 네이밍 규칙

### 규칙 요약

| 항목 | 규칙 | 예시 |
|------|------|------|
| 클래스 | `PascalCase` | `FirstPersonPOV`, `DatabasePool` |
| 함수/메서드 | `snake_case` | `analyze_stock`, `get_connection` |
| 변수 | `snake_case` | `stock_code`, `db_pool` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_POSITION_SIZE`, `DEFAULT_TIMEOUT` |
| Private | `_leading_underscore` | `_internal_method`, `_cache` |
| Protected | `_single_underscore` | `_helper_method` |
| 모듈 | `snake_case` | `first_person_pov.py` |
| 패키지 | `snake_case` | `pov/`, `trading/` |

### 예시

```python
# ✅ 올바른 예시
class TradingSignal:
    """거래 신호 클래스"""
    
    MAX_CONFIDENCE = 1.0  # 상수
    DEFAULT_TIMEOUT = 5  # 상수
    
    def __init__(self, stock_code: str):
        self.stock_code = stock_code  # 인스턴스 변수
        self._cache = {}  # private 변수
    
    def analyze(self) -> Dict[str, Any]:
        """분석 수행"""
        return self._internal_calculation()  # private 메서드 호출
    
    def _internal_calculation(self) -> Dict[str, Any]:
        """내부 계산 (private)"""
        pass
```

```python
# ❌ 잘못된 예시
class tradingSignal:  # 소문자 시작
    maxConfidence = 1.0  # camelCase
    
    def Analyze(self):  # PascalCase
        pass
    
    def internalCalculation(self):  # camelCase, private 아님
        pass
```

### 네이밍 체크리스트

- [ ] 클래스명은 PascalCase
- [ ] 함수/메서드명은 snake_case
- [ ] 변수명은 snake_case
- [ ] 상수는 UPPER_SNAKE_CASE
- [ ] Private는 _leading_underscore
- [ ] 의미 있는 이름 사용 (축약어 지양)

---

## ⚠️ 에러 처리

### 필수 규칙

1. **명확한 예외 타입 사용**
2. **예외 계층 구조 준수**
3. **명확한 에러 메시지**
4. **컨텍스트 정보 포함**

### 예외 계층 구조

```python
# src/exceptions.py
class AbiseuError(Exception):
    """Abiseu 기본 예외"""
    pass

class POVError(AbiseuError):
    """POV 관련 에러 기본 클래스"""
    pass

class POVDataError(POVError):
    """데이터 관련 에러"""
    def __init__(self, message: str, stock_code: str):
        self.stock_code = stock_code
        super().__init__(message)

class POVCalculationError(POVError):
    """계산 관련 에러"""
    pass
```

### 에러 처리 예시

```python
# ✅ 올바른 예시
def analyze(self, stock_code: str) -> Dict[str, Any]:
    """재무 분석 수행"""
    try:
        # 입력 검증
        if not isinstance(stock_code, str) or len(stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {stock_code}")
        
        # 데이터 조회
        data = self.db_pool.get_connection().query(...)
        if not data:
            raise POVDataError(
                f"데이터 조회 실패: {stock_code}",
                stock_code
            )
        
        # 계산 수행
        result = self._calculate(data)
        return result
        
    except DatabaseError as e:
        logger.error(f"DB 오류: {e}", exc_info=True)
        raise POVDataError(f"데이터 조회 실패: {stock_code}", stock_code) from e
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise POVCalculationError(f"계산 실패: {stock_code}") from e
```

```python
# ❌ 잘못된 예시
def analyze(self, stock_code: str) -> Dict[str, Any]:
    """재무 분석 수행"""
    # 예외 타입 불명확
    if not stock_code:
        raise Exception("Error")  # 일반 예외 사용
    
    # 에러 메시지 불명확
    if error:
        raise ValueError("Error")  # 컨텍스트 없음
    
    # 예외 처리 없음
    data = self.db_pool.get_connection().query(...)  # 예외 처리 없음
    return data
```

### 에러 처리 체크리스트

- [ ] 명확한 예외 타입 사용
- [ ] 예외 계층 구조 준수
- [ ] 명확한 에러 메시지
- [ ] 컨텍스트 정보 포함 (stock_code 등)
- [ ] 로깅 포함 (필요 시)
- [ ] 예외 체이닝 (from e)

---

## 📐 코드 구조

### 파일 구조 순서

1. **모듈 Docstring**
2. **Import (표준 라이브러리 → 서드파티 → 로컬)**
3. **로깅 설정**
4. **상수 정의**
5. **예외 클래스 (해당 파일 내)**
6. **클래스 정의**
7. **함수 정의**

### 예시

```python
"""
FirstPersonPOV 모듈

1인칭 관점에서 회사 내부자처럼 재무 분석을 수행합니다.

계약:
- 입력: stock_code (str, 6자리)
- 출력: Dict with keys: 'intrinsic_value', 'health_score', 'outlook'
- 예외: ValueError, POVDataError
"""

# 표준 라이브러리
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 서드파티
import pandas as pd
import numpy as np

# 로컬
from src.core.light_module import LightModule
from src.core.db_pool import DatabasePool
from src.exceptions import POVDataError, POVCalculationError

# 로깅 설정
logger = logging.getLogger(__name__)

# 상수 정의
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 5

# 클래스 정의
class FirstPersonPOV(LightModule):
    """1인칭: 회사 내부자 관점"""
    pass

# 함수 정의 (모듈 레벨)
def helper_function() -> None:
    """헬퍼 함수"""
    pass
```

### Import 규칙

```python
# ✅ 올바른 예시
# 표준 라이브러리
import logging
import os
from typing import Dict, Any
from datetime import datetime

# 서드파티
import pandas as pd
import numpy as np

# 로컬
from src.core.light_module import LightModule
from src.core.db_pool import DatabasePool
```

```python
# ❌ 잘못된 예시
# 순서 무시
from src.core.light_module import LightModule
import logging
import pandas as pd

# 와일드카드 import (지양)
from src.core import *
```

### 코드 구조 체크리스트

- [ ] 모듈 Docstring 포함
- [ ] Import 순서 준수
- [ ] 로깅 설정 포함
- [ ] 상수 정의 포함
- [ ] 클래스/함수 정의 순서 명확

---

## 💬 주석 및 문서화

### 주석 규칙

1. **복잡한 로직에만 주석**
2. **"왜"를 설명하는 주석 (코드가 "무엇"을 하는지는 코드로)**
3. **TODO/FIXME 주석 사용**

### 예시

```python
# ✅ 올바른 예시
# 재무 비율 계산: ROE는 순이익/자기자본으로 계산하되,
# 자기자본이 0인 경우는 업계 평균값을 사용합니다.
if equity == 0:
    roe = industry_average_roe
else:
    roe = net_income / equity

# TODO: 캐시 메커니즘 추가 필요 (성능 개선)
def calculate_value(self):
    pass

# FIXME: 동시성 문제 해결 필요
def update_position(self):
    pass
```

```python
# ❌ 잘못된 예시
# 변수에 값 할당 (불필요한 주석)
stock_code = "005930"  # stock_code에 "005930" 할당

# 명확한 코드에 주석 (불필요)
if stock_code:  # stock_code가 있으면
    return True  # True 반환
```

### 주석 체크리스트

- [ ] 복잡한 로직에만 주석
- [ ] "왜"를 설명하는 주석
- [ ] TODO/FIXME 주석 사용
- [ ] 불필요한 주석 제거

---

## 🔧 도구 설정

### Black 설정

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'
```

### Flake8 설정

```ini
# .flake8
[flake8]
max-line-length = 100
exclude = 
    .git,
    __pycache__,
    venv,
    .venv
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
```

### MyPy 설정

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "src.*"
disallow_untyped_defs = true
```

---

## ✅ 체크리스트

### 개발 전

- [ ] 코딩 스타일 가이드 읽기
- [ ] Black, flake8, mypy 설정 확인

### 개발 중

- [ ] 타입 힌트 추가
- [ ] Docstring 작성
- [ ] 네이밍 규칙 준수
- [ ] 에러 처리 구현
- [ ] 코드 구조 준수

### 개발 후

- [ ] Black 포맷팅 실행
- [ ] flake8 검증 통과
- [ ] mypy 타입 체크 통과
- [ ] Docstring 완성도 확인

---

## 🔗 관련 문서

- [모듈 구조 가이드](./MODULE_STRUCTURE_GUIDE.md)
- [계약 준수 가이드](./CONTRACT_COMPLIANCE_GUIDE.md)
- [개발거버넌스 가이드](./DEVELOPMENT_GOVERNANCE_GUIDE.md)

---

**코딩 스타일 가이드 작성 완료. 모든 개발자는 이 가이드를 준수해야 합니다.**






