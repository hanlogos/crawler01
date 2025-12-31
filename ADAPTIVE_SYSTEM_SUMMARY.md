# 대응형 크롤러 시스템 구현 완료

## ✅ 구현 완료 사항

### 1. 핵심 기능

#### ✅ 사전 테스트 및 검증
- 크롤링 시작 전 연결 테스트 (기본 3회)
- 성공률 및 평균 응답 시간 측정
- 차단 위험 사전 감지

#### ✅ 차단 감지 시스템
- **상태 코드 기반**: 403, 429, 503 등 감지
- **응답 시간 기반**: 30초 이상 시 차단 의심
- **실패율 기반**: 최근 10개 요청 중 30% 이상 실패 시 감지
- **연속 실패 감지**: 5회 이상 연속 실패 시 감지

#### ✅ 동적 요청 간격 조절
- **성공 시**: 지연 시간 감소 (×0.9, 최소값 유지)
- **실패 시**: 지연 시간 증가 (×1.5, 최대값 제한)
- **랜덤성 추가**: 0.8~1.2배 랜덤 조절로 패턴 회피

#### ✅ 사이트별 프로필 관리
- 각 사이트별 독립적인 설정
- 프로필 자동 저장/로드 (`site_profiles.json`)
- 성공률, 응답 시간 등 메트릭 추적

#### ✅ User-Agent 로테이션
- 5개의 다양한 User-Agent 순환 사용
- 봇 감지 회피

#### ✅ 건강 상태 모니터링
- 실시간 성공률 추적
- 평균 응답 시간 모니터링
- 건강 상태 자동 판단 (성공률 ≥70%, 연속 실패 <5회, 응답 시간 <10초)

## 📊 테스트 결과

```
✅ 사전 테스트 성공: 성공률 100.0%, 평균 응답 시간 0.13초
✅ 요청 성공: 71,071 bytes
✅ 크롤러 상태: 건강 (성공률 100%, 응답 시간 0.11초)
✅ 프로필 저장 완료
```

## 🎯 사용 예제

### 기본 사용 (대응형 크롤러 활성화)

```python
from crawler_38com import ThirtyEightComCrawler

# 대응형 크롤러 활성화
crawler = ThirtyEightComCrawler(
    delay=3.0,
    use_adaptive=True,  # 대응형 크롤러 활성화
    site_domain="www.38.co.kr"
)

# 사전 테스트
success, message = crawler.pre_test_connection()
if success:
    print(f"✅ 사전 테스트 성공: {message}")
    
    # 크롤링 실행
    reports = crawler.crawl_recent_reports(days=1, max_reports=10)
    
    # 상태 확인
    status = crawler.get_crawler_status()
    print(f"성공률: {status['success_rate']:.1%}")
    print(f"평균 응답 시간: {status['avg_response_time']:.2f}초")
    print(f"현재 지연 시간: {status['current_delay']:.2f}초")
    print(f"건강 상태: {'✅ 양호' if status['is_healthy'] else '⚠️ 주의'}")
```

### 직접 사용 (AdaptiveCrawler)

```python
from adaptive_crawler import AdaptiveCrawler, SiteProfile

# 사이트 프로필 생성
profile = SiteProfile(
    domain="www.example.com",
    base_delay=3.0,
    min_delay=1.0,
    max_delay=10.0
)

# 대응형 크롤러 생성
crawler = AdaptiveCrawler(profile)

# 사전 테스트
success, message = crawler.pre_test("http://www.example.com", test_requests=3)

# 안전한 요청
response = crawler.fetch("http://www.example.com/page")

# 상태 확인
status = crawler.get_status()
```

## 🔧 설정 옵션

### SiteProfile 주요 설정

```python
profile = SiteProfile(
    domain="www.example.com",           # 사이트 도메인
    base_delay=3.0,                      # 기본 대기 시간 (초)
    min_delay=1.0,                       # 최소 대기 시간 (초)
    max_delay=10.0,                      # 최대 대기 시간 (초)
    
    # 차단 감지 임계값
    block_threshold_fail_rate=0.3,       # 실패율 30% 이상 시 차단 의심
    block_threshold_status_code=[403, 429, 503],  # 차단 상태 코드
    block_threshold_response_time=30.0,  # 응답 시간 30초 이상 시 의심
    
    # 동적 조절 파라미터
    delay_multiplier=1.5,                # 실패 시 지연 시간 배수
    delay_reduction_rate=0.9,            # 성공 시 지연 시간 감소율
)
```

## 📈 동작 원리

### 1. 사전 테스트 단계
```
크롤링 시작 전 → 3회 테스트 요청 → 성공률/응답시간 측정 → 차단 위험 평가
```

### 2. 요청 단계
```
요청 전 → 동적 지연 시간 적용 (랜덤성 포함) → 요청 실행 → 차단 감지 → 결과 기록
```

### 3. 조절 단계
```
성공 → 지연 시간 감소 (×0.9) → 최소값 확인
실패 → 지연 시간 증가 (×1.5) → 최대값 확인 → 연속 실패 카운트 증가
```

### 4. 차단 대응
```
차단 감지 → 지연 시간 급증 (×2^attempt) → User-Agent 변경 → 재시도
```

## 📁 생성된 파일

1. **`adaptive_crawler.py`** - 대응형 크롤러 핵심 모듈
2. **`test_adaptive_crawler.py`** - 테스트 스크립트
3. **`ADAPTIVE_CRAWLER_GUIDE.md`** - 사용 가이드
4. **`site_profiles.json`** - 사이트별 프로필 저장 파일 (자동 생성)

## 🚀 다음 단계

1. **실제 크롤링 테스트**
   ```bash
   python run_crawler.py
   ```

2. **상태 모니터링**
   - 주기적으로 `get_crawler_status()` 호출
   - 프로필 파일 확인 (`site_profiles.json`)

3. **설정 조정**
   - 사이트별 특성에 맞게 임계값 조정
   - User-Agent 목록 확장

## 💡 주요 특징

- ✅ **자동 조절**: 성공/실패에 따라 자동으로 요청 간격 조절
- ✅ **차단 방지**: 다양한 차단 감지 메커니즘
- ✅ **사이트별 관리**: 각 사이트별 독립적인 프로필
- ✅ **상태 추적**: 실시간 메트릭 추적 및 건강 상태 판단
- ✅ **프로필 저장**: 설정 자동 저장으로 재사용 가능

## ⚠️ 주의사항

1. **사전 테스트 권장**: 크롤링 시작 전 반드시 `pre_test_connection()` 실행
2. **상태 모니터링**: 주기적으로 크롤러 상태 확인
3. **차단 대응**: 차단 감지 시 자동으로 대기 시간 증가
4. **프로필 관리**: 각 사이트별 프로필이 자동 저장되므로 재사용 가능



