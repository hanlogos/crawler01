# 🏗️ 모듈 구조 가이드

> 작성일: 2025-12-28  
> 목적: Abiseu 프로젝트 모듈 구조 및 아키텍처 가이드

---

## 📋 목차

1. [모듈 기본 구조](#모듈-기본-구조)
2. [모듈 계층 구조](#모듈-계층-구조)
3. [모듈 인터페이스](#모듈-인터페이스)
4. [의존성 관리](#의존성-관리)
5. [모듈 생명주기](#모듈-생명주기)
6. [이벤트 통신](#이벤트-통신)
7. [모듈 템플릿](#모듈-템플릿)

---

## 🧩 모듈 기본 구조

### 필수 구조

모든 모듈은 다음 구조를 따라야 합니다:

```python
"""
[모듈명] 모듈

[모듈 설명]

계약:
- 입력: [입력 형식 및 제약]
- 출력: [출력 형식 및 제약]
- 예외: [예외 타입 및 조건]

의존성:
- [의존 모듈 1]: [의존 이유]
- [의존 모듈 2]: [의존 이유]

사용 예시:
    ```python
    # 예시 코드
    ```
"""

# 표준 라이브러리
import logging
from typing import Dict, Any, Optional

# 서드파티
import pandas as pd

# 로컬
from src.core.light_module import LightModule
from src.core.db_pool import DatabasePool
from src.exceptions import POVDataError

# 로깅 설정
logger = logging.getLogger(__name__)

# 상수 정의
DEFAULT_TIMEOUT = 5
MAX_RETRY_COUNT = 3


class FirstPersonPOV(LightModule):
    """
    1인칭: 회사 내부자 관점
    
    재무 분석을 통해 회사의 내재가치와 건강도를 평가합니다.
    """
    
    def __init__(self, name: str, db_pool: DatabasePool):
        """
        초기화
        
        Args:
            name: 모듈 이름
            db_pool: 데이터베이스 연결 풀
        """
        super().__init__(name)
        self.db_pool = db_pool
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        모듈 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            # 초기화 로직
            self.initialized = True
            logger.info(f"{self.name} 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"{self.name} 초기화 실패: {e}", exc_info=True)
            return False
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        재무 분석 수행
        
        Args:
            stock_code: 종목 코드 (6자리 문자열)
        
        Returns:
            Dict with keys: 'intrinsic_value', 'health_score', 'outlook'
        
        Raises:
            ValueError: 잘못된 stock_code
            POVDataError: 데이터 조회 실패
        """
        # 입력 검증
        if not isinstance(stock_code, str) or len(stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {stock_code}")
        
        # 로직 수행
        # ...
        
        # 출력 검증
        result = {
            'intrinsic_value': 0.0,
            'health_score': 0.0,
            'outlook': 'neutral'
        }
        
        return result
```

---

## 📊 모듈 계층 구조

### 3.5-Layer 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│ Layer 3.5: 통합 레이어 (EventBus)                        │
├─────────────────────────────────────────────────────────┤
│ EventBus (Pub/Sub)                                       │
│ - 모듈 간 이벤트 통신                                    │
│ - 느슨한 결합                                            │
│ - 확장성 보장                                            │
└─────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
         │                    │                    │
┌────────┴────────┐  ┌─────────┴─────────┐  ┌──────┴──────┐
│ Layer 3:       │  │ Layer 2:          │  │ Layer 1:    │
│ 실행 레이어    │  │ 비즈니스 로직     │  │ 데이터 레이어│
├────────────────┤  ├──────────────────┤  ├─────────────┤
│ TradingEngine  │  │ POV System        │  │ Repository  │
│ RiskManager    │  │ Strategy Engine   │  │ Database    │
│ OrderExecutor  │  │ Coliseum          │  │ Cache       │
└────────────────┘  └──────────────────┘  └─────────────┘
```

### 모듈 분류

#### Layer 1: 데이터 레이어

- **Repository**: 데이터 접근 추상화
- **Database**: 데이터베이스 연결 및 쿼리
- **Cache**: 캐시 관리

```python
# src/repository/market_data_repository.py
class MarketDataRepository:
    """시장 데이터 저장소"""
    pass
```

#### Layer 2: 비즈니스 로직 레이어

- **POV System**: 관점별 분석
- **Strategy Engine**: 전략 실행
- **Coliseum**: 합의 엔진

```python
# src/pov/first_person_pov.py
class FirstPersonPOV(LightModule):
    """1인칭 관점 분석"""
    pass
```

#### Layer 3: 실행 레이어

- **Trading Engine**: 매매 실행
- **Risk Manager**: 리스크 관리
- **Order Executor**: 주문 실행

```python
# src/trading/order_executor.py
class OrderExecutor(LightModule):
    """주문 실행기"""
    pass
```

#### Layer 3.5: 통합 레이어

- **EventBus**: 이벤트 통신
- **Orchestrator**: 오케스트레이션

```python
# src/core/event_bus.py
class EventBus:
    """이벤트 버스"""
    pass
```

---

## 🔌 모듈 인터페이스

### LightModule 기본 인터페이스

모든 모듈은 `LightModule`을 상속해야 합니다:

```python
# src/core/light_module.py (예상 구조)
class LightModule:
    """모든 모듈의 기본 클래스"""
    
    def __init__(self, name: str):
        """초기화"""
        self.name = name
        self.initialized = False
        self.running = False
    
    def initialize(self) -> bool:
        """모듈 초기화"""
        raise NotImplementedError
    
    def start(self) -> bool:
        """모듈 시작"""
        raise NotImplementedError
    
    def stop(self) -> bool:
        """모듈 중지"""
        raise NotImplementedError
    
    def cleanup(self) -> bool:
        """모듈 정리"""
        raise NotImplementedError
    
    def get_status(self) -> Dict[str, Any]:
        """모듈 상태 조회"""
        return {
            'name': self.name,
            'initialized': self.initialized,
            'running': self.running
        }
```

### 인터페이스 구현 예시

```python
class FirstPersonPOV(LightModule):
    """1인칭 관점 분석"""
    
    def __init__(self, name: str, db_pool: DatabasePool):
        super().__init__(name)
        self.db_pool = db_pool
    
    def initialize(self) -> bool:
        """초기화"""
        try:
            # 초기화 로직
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"초기화 실패: {e}", exc_info=True)
            return False
    
    def start(self) -> bool:
        """시작"""
        if not self.initialized:
            logger.error("초기화되지 않음")
            return False
        
        self.running = True
        logger.info(f"{self.name} 시작")
        return True
    
    def stop(self) -> bool:
        """중지"""
        self.running = False
        logger.info(f"{self.name} 중지")
        return True
    
    def cleanup(self) -> bool:
        """정리"""
        self.stop()
        # 리소스 정리
        return True
```

---

## 🔗 의존성 관리

### 의존성 선언

모듈의 의존성은 명시적으로 선언해야 합니다:

```python
class FirstPersonPOV(LightModule):
    """
    1인칭 관점 분석
    
    의존성:
    - DatabasePool: 데이터베이스 연결 풀 (필수)
    - EventBus: 이벤트 통신 (선택)
    """
    
    def __init__(
        self, 
        name: str, 
        db_pool: DatabasePool,
        event_bus: Optional[EventBus] = None
    ):
        super().__init__(name)
        self.db_pool = db_pool  # 필수 의존성
        self.event_bus = event_bus  # 선택 의존성
```

### 의존성 주입

의존성은 생성자에서 주입받습니다:

```python
# ✅ 올바른 예시
db_pool = DatabasePool(...)
event_bus = EventBus()
pov = FirstPersonPOV("first_person", db_pool, event_bus)
```

```python
# ❌ 잘못된 예시
class FirstPersonPOV(LightModule):
    def __init__(self, name: str):
        super().__init__(name)
        self.db_pool = DatabasePool(...)  # 내부에서 생성 (의존성 주입 아님)
```

### 순환 의존성 방지

순환 의존성은 금지됩니다:

```python
# ❌ 순환 의존성 (금지)
# ModuleA가 ModuleB에 의존
# ModuleB가 ModuleA에 의존
# → 순환 의존성

# ✅ 해결 방법: EventBus 사용
# ModuleA와 ModuleB는 EventBus를 통해 통신
```

---

## 🔄 모듈 생명주기

### 생명주기 단계

1. **초기화 (initialize)**: 모듈 초기 설정
2. **시작 (start)**: 모듈 실행 시작
3. **실행 (running)**: 모듈 정상 실행
4. **중지 (stop)**: 모듈 실행 중지
5. **정리 (cleanup)**: 모듈 리소스 정리

### 생명주기 관리 예시

```python
class FirstPersonPOV(LightModule):
    """1인칭 관점 분석"""
    
    def initialize(self) -> bool:
        """초기화"""
        if self.initialized:
            logger.warning(f"{self.name} 이미 초기화됨")
            return True
        
        try:
            # 초기화 로직
            self._setup_database()
            self._load_config()
            self.initialized = True
            logger.info(f"{self.name} 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"{self.name} 초기화 실패: {e}", exc_info=True)
            return False
    
    def start(self) -> bool:
        """시작"""
        if not self.initialized:
            logger.error(f"{self.name} 초기화되지 않음")
            return False
        
        if self.running:
            logger.warning(f"{self.name} 이미 실행 중")
            return True
        
        try:
            self.running = True
            self._start_background_tasks()
            logger.info(f"{self.name} 시작")
            return True
        except Exception as e:
            logger.error(f"{self.name} 시작 실패: {e}", exc_info=True)
            self.running = False
            return False
    
    def stop(self) -> bool:
        """중지"""
        if not self.running:
            logger.warning(f"{self.name} 실행 중이 아님")
            return True
        
        try:
            self._stop_background_tasks()
            self.running = False
            logger.info(f"{self.name} 중지")
            return True
        except Exception as e:
            logger.error(f"{self.name} 중지 실패: {e}", exc_info=True)
            return False
    
    def cleanup(self) -> bool:
        """정리"""
        self.stop()
        
        try:
            self._cleanup_resources()
            self.initialized = False
            logger.info(f"{self.name} 정리 완료")
            return True
        except Exception as e:
            logger.error(f"{self.name} 정리 실패: {e}", exc_info=True)
            return False
```

---

## 📡 이벤트 통신

### EventBus 사용

모듈 간 통신은 EventBus를 통해 이루어집니다:

```python
class FirstPersonPOV(LightModule):
    """1인칭 관점 분석"""
    
    def __init__(
        self, 
        name: str, 
        db_pool: DatabasePool,
        event_bus: Optional[EventBus] = None
    ):
        super().__init__(name)
        self.db_pool = db_pool
        self.event_bus = event_bus
        
        # 이벤트 구독
        if self.event_bus:
            self.event_bus.subscribe("market_data_updated", self._on_market_data_updated)
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """분석 수행"""
        result = {...}
        
        # 이벤트 발행
        if self.event_bus:
            self.event_bus.emit("pov_analysis_completed", {
                'stock_code': stock_code,
                'result': result
            })
        
        return result
    
    def _on_market_data_updated(self, data: Dict[str, Any]) -> None:
        """시장 데이터 업데이트 이벤트 처리"""
        logger.info(f"시장 데이터 업데이트: {data}")
        # 처리 로직
```

### 이벤트 명명 규칙

- **snake_case** 사용
- **동사_명사** 형식
- **명확한 의미**

```python
# ✅ 올바른 예시
"pov_analysis_completed"
"market_data_updated"
"position_opened"
"order_executed"

# ❌ 잘못된 예시
"POVAnalysisCompleted"  # camelCase
"marketDataUpdated"  # camelCase
"update"  # 불명확
```

---

## 📝 모듈 템플릿

### POV 모듈 템플릿

```python
"""
[모듈명] 모듈

[모듈 설명]

계약:
- 입력: stock_code (str, 6자리)
- 출력: Dict with keys: [키 목록]
- 예외: ValueError, POVDataError

의존성:
- DatabasePool: 데이터베이스 연결 풀
- EventBus: 이벤트 통신 (선택)
"""

import logging
from typing import Dict, Any, Optional

from src.core.light_module import LightModule
from src.core.db_pool import DatabasePool
from src.core.event_bus import EventBus
from src.exceptions import POVDataError

logger = logging.getLogger(__name__)


class [모듈명](LightModule):
    """[모듈 설명]"""
    
    def __init__(
        self, 
        name: str, 
        db_pool: DatabasePool,
        event_bus: Optional[EventBus] = None
    ):
        """
        초기화
        
        Args:
            name: 모듈 이름
            db_pool: 데이터베이스 연결 풀
            event_bus: 이벤트 버스 (선택)
        """
        super().__init__(name)
        self.db_pool = db_pool
        self.event_bus = event_bus
        
        # 이벤트 구독
        if self.event_bus:
            self.event_bus.subscribe("[이벤트명]", self._on_[이벤트명])
    
    def initialize(self) -> bool:
        """모듈 초기화"""
        try:
            # 초기화 로직
            self.initialized = True
            logger.info(f"{self.name} 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"{self.name} 초기화 실패: {e}", exc_info=True)
            return False
    
    def start(self) -> bool:
        """모듈 시작"""
        if not self.initialized:
            logger.error(f"{self.name} 초기화되지 않음")
            return False
        
        self.running = True
        logger.info(f"{self.name} 시작")
        return True
    
    def stop(self) -> bool:
        """모듈 중지"""
        self.running = False
        logger.info(f"{self.name} 중지")
        return True
    
    def cleanup(self) -> bool:
        """모듈 정리"""
        self.stop()
        # 리소스 정리
        return True
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        분석 수행
        
        Args:
            stock_code: 종목 코드 (6자리 문자열)
        
        Returns:
            Dict with keys: [키 목록]
        
        Raises:
            ValueError: 잘못된 stock_code
            POVDataError: 데이터 조회 실패
        """
        # 입력 검증
        if not isinstance(stock_code, str) or len(stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {stock_code}")
        
        # 로직 수행
        # ...
        
        # 출력 검증
        result = {...}
        
        # 이벤트 발행
        if self.event_bus:
            self.event_bus.emit("[이벤트명]", {
                'stock_code': stock_code,
                'result': result
            })
        
        return result
    
    def _on_[이벤트명](self, data: Dict[str, Any]) -> None:
        """이벤트 처리"""
        logger.info(f"[이벤트명] 이벤트 수신: {data}")
        # 처리 로직
```

---

## ✅ 체크리스트

### 모듈 개발 전

- [ ] 모듈 구조 가이드 읽기
- [ ] 모듈 계층 구조 확인
- [ ] 의존성 확인
- [ ] 인터페이스 설계

### 모듈 개발 중

- [ ] LightModule 상속
- [ ] 필수 메서드 구현 (initialize, start, stop, cleanup)
- [ ] 의존성 주입
- [ ] 이벤트 통신 구현 (필요 시)
- [ ] 계약 준수

### 모듈 개발 후

- [ ] 모듈 구조 검증
- [ ] 의존성 검증
- [ ] 생명주기 테스트
- [ ] 이벤트 통신 테스트

---

## 🔗 관련 문서

- [코딩 스타일 가이드](./CODING_STYLE_GUIDE.md)
- [계약 준수 가이드](./CONTRACT_COMPLIANCE_GUIDE.md)
- [개발거버넌스 가이드](./DEVELOPMENT_GOVERNANCE_GUIDE.md)

---

**모듈 구조 가이드 작성 완료. 모든 모듈은 이 구조를 따라야 합니다.**






