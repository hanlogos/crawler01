# 🔒 계약 준수 가이드

> 작성일: 2025-12-28  
> 목적: 모듈 간 계약(Contract) 정의 및 준수 가이드

---

## 📋 목차

1. [계약의 종류](#계약의-종류)
2. [인터페이스 계약](#인터페이스-계약)
3. [데이터 형식 계약](#데이터-형식-계약)
4. [에러 처리 계약](#에러-처리-계약)
5. [동시성 계약](#동시성-계약)
6. [트랜잭션 계약](#트랜잭션-계약)
7. [이벤트 계약](#이벤트-계약)
8. [의존성 계약](#의존성-계약)
9. [계약 검증](#계약-검증)

---

## 🎯 계약의 종류

### 7종 계약

1. **인터페이스 계약**: 메서드 시그니처, 반환 타입, 예외
2. **데이터 형식 계약**: 입력/출력 데이터 구조, 필수 필드
3. **에러 처리 계약**: 예외 타입, 에러 코드, 복구 방법
4. **동시성 계약**: 락 규칙, 동시 접근 제한
5. **트랜잭션 계약**: 원자성, 일관성, 격리성, 지속성
6. **이벤트 계약**: 이벤트 타입, 데이터 형식, 순서
7. **의존성 계약**: 초기화 순서, 생명주기

---

## 🔌 인터페이스 계약

### 계약 정의

인터페이스 계약은 메서드의 입력, 출력, 예외를 명시합니다:

```python
class FirstPersonPOV(LightModule):
    """
    계약:
    1. analyze(stock_code: str) -> Dict[str, Any]
       - 입력: stock_code는 6자리 문자열
       - 출력: Dict with keys: 'intrinsic_value', 'health_score', 'outlook'
       - 예외: ValueError (잘못된 stock_code), POVDataError (DB 오류)
    """
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        재무 분석 수행
        
        계약:
        - 입력: stock_code (str, 6자리)
        - 출력: Dict with keys: 'intrinsic_value', 'health_score', 'outlook'
        - 예외: ValueError, POVDataError
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
        
        # 필수 키 검증
        required_keys = ['intrinsic_value', 'health_score', 'outlook']
        for key in required_keys:
            if key not in result:
                raise ContractViolationError(f"Missing required key: {key}")
        
        return result
```

### 계약 위반 시나리오

#### 시나리오 1: 잘못된 입력 타입

```python
# 위반 케이스
pov = FirstPersonPOV("first_person", db_pool)
result = pov.analyze(123)  # int 전달 (str 기대)

# 예상 결과
# ✅ ValueError 발생
# ✅ 명확한 에러 메시지
```

#### 시나리오 2: None 반환 (계약 위반)

```python
# 위반 케이스
def analyze(self, stock_code: str) -> Dict[str, Any]:
    if not stock_code:
        return None  # 계약 위반: Dict 기대

# 예상 결과
# ✅ None 대신 빈 Dict 또는 예외 발생
# ✅ 타입 힌트와 실제 반환 일치
```

#### 시나리오 3: 예외 타입 불일치

```python
# 위반 케이스
def analyze(self, stock_code: str) -> Dict[str, Any]:
    if not stock_code:
        raise KeyError("stock_code required")  # ValueError 기대

# 예상 결과
# ✅ 올바른 예외 타입 사용
# ✅ 예외 계층 구조 준수
```

### 인터페이스 계약 체크리스트

- [ ] 입력 타입 검증
- [ ] 입력 범위/형식 검증
- [ ] 출력 타입 검증
- [ ] 출력 구조 검증 (필수 키 등)
- [ ] 예외 타입 명시
- [ ] 예외 계층 구조 준수

---

## 📊 데이터 형식 계약

### 계약 정의

데이터 형식 계약은 데이터 구조와 제약을 명시합니다:

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class TradingSignal:
    """
    거래 신호 데이터 계약
    
    데이터 계약:
    1. stock_code: str (6자리, 필수)
    2. signal_type: str ('BUY'|'SELL'|'HOLD', 필수)
    3. confidence: float (0.0-1.0, 필수)
    4. strategy_type: str (선택)
    5. timestamp: datetime (필수)
    """
    stock_code: str
    signal_type: str
    confidence: float
    strategy_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """데이터 검증"""
        # stock_code 검증
        if not isinstance(self.stock_code, str) or len(self.stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {self.stock_code}")
        
        # signal_type 검증
        if self.signal_type not in ['BUY', 'SELL', 'HOLD']:
            raise ValueError(f"Invalid signal_type: {self.signal_type}")
        
        # confidence 검증
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0: {self.confidence}")
```

### 계약 위반 시나리오

#### 시나리오 1: 필수 필드 누락

```python
# 위반 케이스
signal = TradingSignal(
    stock_code="005930",
    # signal_type 누락 (필수)
    confidence=0.75
)

# 예상 결과
# ✅ TypeError 발생 (dataclass)
# ✅ 명확한 에러 메시지
```

#### 시나리오 2: 데이터 범위 위반

```python
# 위반 케이스
signal = TradingSignal(
    stock_code="005930",
    signal_type="BUY",
    confidence=1.5  # 0.0-1.0 범위 초과
)

# 예상 결과
# ✅ ValueError 발생
# ✅ 범위 검증 로직
```

#### 시나리오 3: 데이터 형식 불일치

```python
# 위반 케이스
signal = TradingSignal(
    stock_code="005930",
    signal_type="BUY",
    confidence="0.75"  # str (float 기대)
)

# 예상 결과
# ✅ TypeError 발생
# ✅ 명확한 에러 메시지
```

### 데이터 형식 계약 체크리스트

- [ ] @dataclass 사용
- [ ] 필수 필드 검증
- [ ] 선택 필드 명시 (Optional)
- [ ] 범위 검증 (__post_init__)
- [ ] 타입 검증
- [ ] 기본값 설정 (필요 시)

---

## ⚠️ 에러 처리 계약

### 계약 정의

에러 처리 계약은 예외 타입과 처리 방법을 명시합니다:

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

### 계약 규칙

1. **모든 POV 에러는 POVError 상속**
2. **에러 메시지는 명확해야 함**
3. **컨텍스트 정보 포함 (stock_code 등)**
4. **복구 가능 여부 표시**

### 계약 위반 시나리오

#### 시나리오 1: 일반 예외 사용 (계약 위반)

```python
# 위반 케이스
def analyze(self, stock_code: str) -> Dict[str, Any]:
    if not stock_code:
        raise Exception("Invalid stock code")  # POVError 기대

# 예상 결과
# ✅ POVError 사용
# ✅ 적절한 하위 클래스 선택
```

#### 시나리오 2: 에러 메시지 불명확

```python
# 위반 케이스
raise POVError("Error")  # 불명확한 메시지

# 예상 결과
# ✅ 명확한 에러 메시지
# ✅ 컨텍스트 정보 포함
```

#### 시나리오 3: 에러 복구 규약 위반

```python
# 계약: 에러 발생 시 None 반환 또는 예외 발생 (일관성 필요)

# 위반 케이스: 혼합 사용
def analyze(self, stock_code: str) -> Dict[str, Any]:
    if error1:
        return None  # None 반환
    if error2:
        raise POVError("Error")  # 예외 발생 (불일치)

# 예상 결과
# ✅ 일관된 에러 처리
# ✅ None 반환 또는 예외 발생 (선택 후 일관성 유지)
```

### 에러 처리 계약 체크리스트

- [ ] 예외 계층 구조 준수
- [ ] 적절한 예외 타입 선택
- [ ] 명확한 에러 메시지
- [ ] 컨텍스트 정보 포함
- [ ] 일관된 에러 처리
- [ ] 로깅 포함 (필요 시)

---

## 🔐 동시성 계약

### 계약 정의

동시성 계약은 락 규칙과 동시 접근 제한을 명시합니다:

```python
from threading import Lock
from contextlib import contextmanager

class LockManager:
    """
    락 관리자
    
    계약:
    1. acquire(key) -> Lock: 락 획득 (블로킹, 타임아웃 5초)
    2. release(key): 락 해제 (자동 또는 명시적)
    3. 규칙:
       - 같은 스레드에서 중복 획득 가능 (재진입)
       - 다른 스레드에서 대기 (블로킹)
       - 데드락 방지 (타임아웃)
    """
    
    def __init__(self):
        self._locks: Dict[str, Lock] = {}
        self._timeout = 5
    
    @contextmanager
    def acquire(self, key: str):
        """락 획득 (컨텍스트 매니저)"""
        if key not in self._locks:
            self._locks[key] = Lock()
        
        lock = self._locks[key]
        acquired = lock.acquire(timeout=self._timeout)
        
        if not acquired:
            raise TimeoutError(f"락 획득 타임아웃: {key}")
        
        try:
            yield lock
        finally:
            lock.release()
```

### 계약 위반 시나리오

#### 시나리오 1: 락 해제 누락

```python
# 위반 케이스
lock = lock_manager.acquire("position_005930")
# ... 작업 수행 ...
# release() 호출 누락

# 예상 결과
# ✅ 자동 해제 (with 문 사용)
# ✅ 컨텍스트 매니저 지원
```

#### 시나리오 2: 데드락 발생

```python
# 위반 케이스
# 스레드 1: position_005930 → position_005380
# 스레드 2: position_005380 → position_005930
# → 순환 대기 (데드락)

# 예상 결과
# ✅ 타임아웃으로 데드락 감지
# ✅ 락 순서 규칙 (알파벳 순)
```

### 동시성 계약 체크리스트

- [ ] 컨텍스트 매니저 사용
- [ ] 타임아웃 설정
- [ ] 락 순서 규칙
- [ ] 데드락 방지
- [ ] 리소스 누수 방지

---

## 💾 트랜잭션 계약

### 계약 정의

트랜잭션 계약은 ACID 속성을 명시합니다:

```python
class TransactionManager:
    """
    트랜잭션 관리자
    
    계약:
    1. 원자성 (Atomicity): 모두 성공 또는 모두 실패
    2. 일관성 (Consistency): 데이터 무결성 유지
    3. 격리성 (Isolation): 동시 트랜잭션 간 간섭 없음
    4. 지속성 (Durability): 커밋 후 영구 저장
    
    규칙:
    - add_rollback()로 롤백 함수 등록
    - commit() 성공 시 모든 작업 커밋
    - rollback() 실패 시 모든 롤백 함수 실행
    """
    
    def __init__(self):
        self._rollback_functions: List[Callable] = []
        self._committed = False
    
    def add_rollback(self, func: Callable) -> None:
        """롤백 함수 등록"""
        self._rollback_functions.append(func)
    
    def commit(self) -> bool:
        """트랜잭션 커밋"""
        try:
            # 모든 작업 수행
            # ...
            self._committed = True
            return True
        except Exception as e:
            self.rollback()
            raise
    
    def rollback(self) -> None:
        """트랜잭션 롤백"""
        for func in reversed(self._rollback_functions):
            try:
                func()
            except Exception as e:
                logger.error(f"롤백 실패: {e}", exc_info=True)
```

### 계약 위반 시나리오

#### 시나리오 1: 부분 커밋 (원자성 위반)

```python
# 위반 케이스
txn = TransactionManager()
txn.add_rollback(lambda: position_manager.delete_position(pos_id))

# 포지션 생성 성공
position_id = position_manager.open_position(...)

# 주문 실행 실패
order_id = order_executor.execute(...)  # 실패

# commit() 호출 (부분 커밋 위반)

# 예상 결과
# ✅ rollback() 자동 호출
# ✅ 포지션 삭제 (롤백)
```

### 트랜잭션 계약 체크리스트

- [ ] 원자성 보장
- [ ] 일관성 보장
- [ ] 격리성 보장
- [ ] 지속성 보장
- [ ] 롤백 메커니즘

---

## 📡 이벤트 계약

### 계약 정의

이벤트 계약은 이벤트 타입과 데이터 형식을 명시합니다:

```python
class SimpleEventNotifier:
    """
    이벤트 알림기
    
    계약:
    1. 이벤트 타입: 문자열 (명명 규칙: snake_case)
    2. 이벤트 데이터: Dict 또는 None
    3. 순서: 동기 처리 (순서 보장)
    4. 에러: 리스너 에러는 로깅만 (다른 리스너 영향 없음)
    
    이벤트 타입:
    - "prediction_generated": {prediction_id, stock_code}
    - "position_opened": {position_id, stock_code}
    - "position_closed": {position_id, stock_code, pnl}
    - "error_occurred": {error_type, message, context}
    """
    
    def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """이벤트 발행"""
        # 명명 규칙 검증
        if not event_type.islower() or '_' not in event_type:
            logger.warning(f"이벤트 타입 명명 규칙 위반: {event_type}")
        
        # 타입 검증
        if data is not None and not isinstance(data, dict):
            raise ValueError(f"이벤트 데이터는 Dict여야 함: {type(data)}")
        
        # 리스너 호출
        for listener in self._listeners.get(event_type, []):
            try:
                listener(data)
            except Exception as e:
                logger.error(f"리스너 에러: {e}", exc_info=True)
                # 다른 리스너 영향 없음
```

### 계약 위반 시나리오

#### 시나리오 1: 이벤트 타입 불일치

```python
# 위반 케이스
event_notifier.emit("PredictionGenerated")  # camelCase (snake_case 기대)

# 예상 결과
# ✅ 명명 규칙 검증
# ✅ 경고 또는 자동 변환
```

### 이벤트 계약 체크리스트

- [ ] 명명 규칙 (snake_case)
- [ ] 데이터 형식 검증
- [ ] 리스너 독립 실행
- [ ] 에러 격리

---

## 🔗 의존성 계약

### 계약 정의

의존성 계약은 초기화 순서와 생명주기를 명시합니다:

```python
class DependencyChecker:
    """
    의존성 검사기
    
    계약:
    1. 의존성 선언: dependencies = ["task1", "task2"]
    2. 완료 표시: mark_complete("task1")
    3. 검증: check_dependency("task3", ["task1", "task2"]) -> bool
    
    규칙:
    - 의존성은 명시적으로 선언
    - 순환 의존성 금지
    - 의존성 미완료 시 False 반환
    """
    
    def check_dependency(
        self, 
        task: str, 
        dependencies: List[str]
    ) -> bool:
        """의존성 검증"""
        # 순환 의존성 검사
        if self._has_circular_dependency(task, dependencies):
            raise ValueError(f"순환 의존성 발견: {task}")
        
        # 의존성 완료 확인
        for dep in dependencies:
            if not self._is_completed(dep):
                return False
        
        return True
```

### 계약 위반 시나리오

#### 시나리오 1: 순환 의존성

```python
# 위반 케이스
# task1 의존: ["task2"]
# task2 의존: ["task1"]
# → 순환 의존성 (데드락)

# 예상 결과
# ✅ 순환 의존성 감지
# ✅ 에러 발생
```

### 의존성 계약 체크리스트

- [ ] 의존성 명시적 선언
- [ ] 순환 의존성 금지
- [ ] 의존성 검증
- [ ] 초기화 순서 보장

---

## ✅ 계약 검증

### 계약 검증 도구

계약 검증은 `ContractValidator`를 사용합니다:

```python
from src.core.contract_validator import ContractValidator

# 모듈 계약 검증
ContractValidator.validate_module(FirstPersonPOV)

# 인터페이스 계약 검증
ContractValidator.validate_interface(FirstPersonPOV.analyze)
```

### 계약 검증 체크리스트

#### 개발 단계

- [ ] 인터페이스 계약 정의
- [ ] 데이터 형식 계약 정의
- [ ] 에러 처리 계약 정의
- [ ] 동시성 계약 정의 (필요 시)
- [ ] 트랜잭션 계약 정의 (필요 시)
- [ ] 이벤트 계약 정의 (필요 시)
- [ ] 의존성 계약 정의

#### 검증 단계

- [ ] 계약 위반 시나리오 시뮬레이션
- [ ] 계약 검증 구현
- [ ] 에러 처리 테스트
- [ ] 동시성 테스트 (필요 시)
- [ ] 트랜잭션 테스트 (필요 시)

#### 문서화 단계

- [ ] 계약 문서화
- [ ] 예제 코드
- [ ] 에러 처리 가이드

---

## 🔗 관련 문서

- [코딩 스타일 가이드](./CODING_STYLE_GUIDE.md)
- [모듈 구조 가이드](./MODULE_STRUCTURE_GUIDE.md)
- [계약 시뮬레이션](./MVP_PLUS_CONTRACT_SIMULATION.md)
- [개발거버넌스 가이드](./DEVELOPMENT_GOVERNANCE_GUIDE.md)

---

**계약 준수 가이드 작성 완료. 모든 모듈은 이 계약을 준수해야 합니다.**






