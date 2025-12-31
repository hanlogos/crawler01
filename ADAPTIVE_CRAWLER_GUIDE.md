# 대응형 크롤러 가이드

## 개요

대응형 크롤러 시스템은 웹사이트 규제를 피하고 안정적으로 크롤링하기 위한 AI 로직을 제공합니다.

## 주요 기능

### 1. 사전 테스트 및 검증
- 크롤링 시작 전 연결 테스트
- 성공률 및 응답 시간 측정
- 차단 위험 사전 감지

### 2. 차단 감지 및 대응
- 상태 코드 기반 차단 감지 (403, 429, 503 등)
- 응답 시간 기반 차단 감지
- 실패율 기반 차단 감지
- 연속 실패 감지

### 3. 동적 요청 간격 조절
- 성공 시 지연 시간 감소
- 실패 시 지연 시간 증가
- 최소/최대 지연 시간 제한
- 랜덤성 추가로 패턴 회피

### 4. 사이트별 프로필 관리
- 각 사이트별 독립적인 설정
- 프로필 자동 저장/로드
- 성공률, 응답 시간 등 메트릭 추적

### 5. User-Agent 로테이션
- 여러 User-Agent 순환 사용
- 봇 감지 회피

### 6. 건강 상태 모니터링
- 실시간 성공률 추적
- 평균 응답 시간 모니터링
- 건강 상태 자동 판단

## 사용법

### 기본 사용

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
    print(f"사전 테스트 성공: {message}")
    
    # 크롤링 실행
    reports = crawler.crawl_recent_reports(days=1, max_reports=10)
    
    # 상태 확인
    status = crawler.get_crawler_status()
    print(f"성공률: {status['success_rate']:.1%}")
    print(f"평균 응답 시간: {status['avg_response_time']:.2f}초")
else:
    print(f"사전 테스트 실패: {message}")
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
print(status)
```

## 설정 옵션

### SiteProfile 설정

```python
profile = SiteProfile(
    domain="www.example.com",           # 사이트 도메인
    base_delay=3.0,                      # 기본 대기 시간 (초)
    min_delay=1.0,                       # 최소 대기 시간 (초)
    max_delay=10.0,                      # 최대 대기 시간 (초)
    request_timeout=10,                  # 요청 타임아웃 (초)
    max_retries=3,                       # 최대 재시도 횟수
    
    # 차단 감지 임계값
    block_threshold_fail_rate=0.3,       # 실패율 30% 이상 시 차단 의심
    block_threshold_status_code=[403, 429, 503],  # 차단 상태 코드
    block_threshold_response_time=30.0,  # 응답 시간 30초 이상 시 의심
    
    # 동적 조절 파라미터
    delay_multiplier=1.5,                # 실패 시 지연 시간 배수
    delay_reduction_rate=0.9,            # 성공 시 지연 시간 감소율
)
```

## 차단 감지 기준

1. **상태 코드**: 403, 429, 503 등
2. **응답 시간**: 30초 이상
3. **실패율**: 최근 10개 요청 중 30% 이상 실패
4. **연속 실패**: 5회 이상 연속 실패

## 동적 조절 메커니즘

### 성공 시
- 지연 시간 감소 (현재 지연 시간 × 0.9)
- 최소 지연 시간 유지

### 실패 시
- 지연 시간 증가 (현재 지연 시간 × 1.5)
- 최대 지연 시간 제한
- 연속 실패 횟수 증가

## 프로필 저장/로드

프로필은 자동으로 `site_profiles.json` 파일에 저장됩니다:

```json
{
  "www.38.co.kr": {
    "domain": "www.38.co.kr",
    "base_delay": 3.0,
    "current_delay": 2.7,
    "success_rate": 0.95,
    "avg_response_time": 1.2,
    "consecutive_failures": 0
  }
}
```

## 건강 상태 판단

크롤러가 건강한 상태인지 판단하는 기준:

- 성공률 ≥ 70%
- 연속 실패 < 5회
- 평균 응답 시간 < 10초

## 테스트

```bash
# 대응형 크롤러 테스트
python test_adaptive_crawler.py
```

## 주의사항

1. **사전 테스트 권장**: 크롤링 시작 전 `pre_test_connection()` 실행
2. **상태 모니터링**: 주기적으로 `get_crawler_status()` 확인
3. **프로필 관리**: 각 사이트별 프로필이 자동 저장되므로 재사용 가능
4. **차단 대응**: 차단 감지 시 자동으로 대기 시간 증가 및 재시도

## 고급 사용

### 여러 사이트 크롤링

```python
sites = ["www.site1.com", "www.site2.com", "www.site3.com"]

for domain in sites:
    profile = SiteProfile(domain=domain)
    crawler = AdaptiveCrawler(profile)
    
    # 사전 테스트
    success, _ = crawler.pre_test(f"http://{domain}")
    
    if success:
        # 크롤링 실행
        response = crawler.fetch(f"http://{domain}/page")
```

### 수동 조절

```python
# 지연 시간 수동 조절
crawler.profile.current_delay = 5.0

# 상태 리셋
crawler.reset()
```




