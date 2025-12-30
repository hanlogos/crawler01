# 사이트 구조 분석 및 적응형 시스템 통합 완료

## 완료된 작업

### ✅ Phase 1: 사이트 구조 분석 시스템

1. **site_structure_analyzer.py**
   - 메뉴 구조 분석 (93개 메뉴 발견)
   - 링크 패턴 분석 (3개 패턴 발견)
   - 데이터 구조 분석 (목록/상세 페이지)
   - 구조 체크섬 계산 (변경 감지용)

2. **구조 저장/로드**
   - JSON 형식으로 구조 저장
   - 이전 구조와 비교 가능

### ✅ Phase 2: 구조 변경 감지 시스템

1. **StructureChangeDetector**
   - 메뉴 변경 감지
   - 링크 패턴 변경 감지
   - 데이터 구조 변경 감지
   - 체크섬 기반 변경 확인

2. **변경 알림**
   - 변경 사항 자동 감지
   - 상세 변경 내역 로깅
   - 추천 조치 제시

### ✅ Phase 3: 적응형 파서 시스템

1. **AdaptiveParser**
   - 다중 추출 방법 시도
   - 구조 기반 선택자 우선 사용
   - 폴백 메커니즘 (여러 방법 시도)
   - 신뢰도 점수 제공

2. **추출 필드**
   - 제목 (title)
   - 날짜 (date)
   - 애널리스트 (analyst)
   - 종목 (stock)
   - 투자의견 (opinion)
   - 목표가 (target_price)
   - 본문 (content)

### ✅ Phase 4: 구조 변경 모니터링

1. **StructureMonitor**
   - 주기적 구조 확인 (기본 24시간)
   - 자동 변경 감지
   - 테스트 URL로 파싱 검증
   - 구조 이력 관리

2. **AdaptiveCrawler38Com**
   - 크롤러와 모니터 통합
   - 자동 구조 업데이트
   - 적응형 파싱

### ✅ Phase 5: 카테고리 분류 시스템

1. **CategoryClassifier**
   - URL/제목/내용 기반 분류
   - 메뉴 경로 추적
   - 신뢰도 점수 제공

2. **카테고리**
   - 리포트 (KOSPI, KOSDAQ)
   - 뉴스 (비상장)
   - 공시
   - 펀드

## 시스템 구조

```
사이트 구조 분석기 (SiteStructureAnalyzer)
    ↓
구조 변경 감지기 (StructureChangeDetector)
    ↓
적응형 파서 (AdaptiveParser)
    ↓
구조 모니터 (StructureMonitor)
    ↓
카테고리 분류기 (CategoryClassifier)
    ↓
통합 크롤러 (AdaptiveCrawler38Com)
```

## 사용 방법

### 1. 구조 분석 (1회)

```bash
python site_structure_analyzer.py
```

### 2. 구조 모니터링

```python
from structure_monitor import StructureMonitor

monitor = StructureMonitor("http://www.38.co.kr", check_interval_hours=24)
monitor.monitor_loop()  # 백그라운드 실행
```

### 3. 적응형 크롤러 사용

```python
from structure_monitor import AdaptiveCrawler38Com

crawler = AdaptiveCrawler38Com()

# 구조 업데이트 (필요시)
crawler.update_structure()

# 보고서 파싱
html = fetch_report_html(url)
data = crawler.parse_report(html)
```

### 4. 카테고리 분류

```python
from category_classifier import IntegratedClassifier

classifier = IntegratedClassifier(structure)

result = classifier.classify_report(
    url="http://www.38.co.kr/html/news/?m=kosdaq&nkey=report",
    title="삼성전자 리포트",
    content="..."
)

print(f"카테고리: {result['category']}")
print(f"신뢰도: {result['confidence']:.1%}")
```

## 주요 특징

### 1. 자동 구조 변경 대응
- 구조 변경 자동 감지
- 적응형 파서가 자동으로 대응
- 수동 개입 최소화

### 2. 다중 추출 방법
- 구조 기반 선택자 우선
- 일반적인 선택자 폴백
- 메타 태그, 텍스트 검색 등

### 3. 신뢰도 기반 추출
- 각 추출 방법에 신뢰도 점수
- 높은 신뢰도 결과 우선 사용
- 실패 시 대체 방법 시도

### 4. 구조 이력 관리
- 모든 구조 변경 이력 저장
- 롤백 가능
- 변경 추적

## 파일 구조

```
crawler_01/
├── site_structure_analyzer.py    # 구조 분석기
├── adaptive_parser.py            # 적응형 파서
├── structure_monitor.py          # 구조 모니터
├── category_classifier.py        # 카테고리 분류
├── site_structures/              # 구조 저장 디렉토리
│   └── structure_*.json
└── INTEGRATION_COMPLETE.md       # 이 문서
```

## 다음 단계

1. **크롤러 통합**
   - `crawler_38com.py`에 적응형 파서 통합
   - 구조 모니터링 자동화

2. **대시보드 통합**
   - 구조 변경 알림을 대시보드에 표시
   - 파싱 성공률 모니터링

3. **성능 최적화**
   - 구조 분석 캐싱
   - 병렬 파싱

4. **테스트 강화**
   - 다양한 사이트 구조 테스트
   - 엣지 케이스 처리

## 참고사항

- 구조 파일은 `site_structures/` 디렉토리에 저장됩니다
- 구조 변경 시 자동으로 새 파일이 생성됩니다
- 이전 구조와 비교하여 변경 사항을 확인할 수 있습니다
- 적응형 파서는 구조 변경 시 자동으로 대응하지만, 수동 확인을 권장합니다


