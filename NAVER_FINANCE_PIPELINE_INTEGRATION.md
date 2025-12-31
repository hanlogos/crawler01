# 네이버 금융 크롤러 파이프라인 통합 완료 보고서

## ✅ 완료된 통합

### 네이버 금융 리서치 크롤러에 파이프라인 통합

**목표**: 네이버 금융 크롤링 → 정규화 → PostgreSQL 저장을 자동으로 수행

## 🔧 구현 내용

### 1. site_crawling_manager.py에 네이버 금융 통합

**위치**: `site_crawling_manager.py` - `_crawling_worker()` 메서드

**기능**:
- 네이버 금융 리서치 크롤러 통합
- 주요 종목 리스트를 순회하며 리포트 수집
- 크롤링 완료 후 자동으로 정규화 및 저장
- 환경변수로 DB 저장 활성화/비활성화 제어

**주요 종목 리스트** (기본값):
- 삼성전자 (005930)
- SK하이닉스 (000660)
- LG에너지솔루션 (373220)
- 현대차 (005380)
- NAVER (035420)

### 2. 대시보드에 네이버 금융 사이트 등록

**위치**: `enhanced_crawling_dashboard.py`

**기능**:
- 네이버 금융 리서치 사이트 등록
- 스케줄 설정 (매일 10:00, 한경 이후 실행)

## 📊 통합 흐름

```
1. site_crawling_manager에서 크롤링 시작
   ↓
2. 네이버 금융 리서치 크롤러 실행
   ↓
3. 주요 종목 리스트 순회
   - 각 종목별로 search_by_stock() 실행
   - 최근 N일 리포트 수집
   ↓
4. 리포트 수집 완료
   ↓
5. 정규화 파이프라인 실행 (옵션)
   - AnalystReportPipeline 초기화
   - 리포트 정규화 (korea_normalize.py)
   - PostgreSQL 저장 (analyst_snapshot_store.py)
   ↓
6. 결과 로깅
```

## 🔧 환경 설정

### 환경변수 설정

```bash
# .env 파일 또는 환경변수
ENABLE_DB_STORAGE=true
DB_HOST=localhost
DB_NAME=crawler_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### DB 저장 활성화/비활성화

**활성화**:
```bash
export ENABLE_DB_STORAGE=true
export DB_PASSWORD=your_password
```

**비활성화**:
```bash
export ENABLE_DB_STORAGE=false
# 또는 DB_PASSWORD를 설정하지 않음
```

## 📝 사용 방법

### 1. 기본 사용 (크롤링만)

```python
from site_crawling_manager import SiteCrawlingManager

manager = SiteCrawlingManager()
manager.start_crawling("naver_finance", days=7, max_reports=50)
```

### 2. DB 저장 포함 (환경변수 설정 필요)

```bash
# 환경변수 설정
export ENABLE_DB_STORAGE=true
export DB_HOST=localhost
export DB_NAME=crawler_db
export DB_USER=postgres
export DB_PASSWORD=your_password
```

```python
from site_crawling_manager import SiteCrawlingManager

manager = SiteCrawlingManager()
manager.start_crawling("naver_finance", days=7, max_reports=50)
# 자동으로 정규화 및 DB 저장 수행
```

### 3. 직접 크롤러 사용

```python
from crawler_naver_finance_research import NaverFinanceResearchCrawler
from analyst_report_pipeline import AnalystReportPipeline
import os

# 크롤링
crawler = NaverFinanceResearchCrawler()
reports = crawler.search_by_stock("삼성전자", "005930", days=7, max_reports=50)

# 정규화 및 저장
db_params = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'crawler_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

pipeline = AnalystReportPipeline(db_params, enable_db=True)
saved_count = pipeline.process_reports(reports, source='naver')
print(f"저장된 리포트: {saved_count}개")
```

## 🎯 주요 특징

### 1. 종목별 검색
- 네이버 금융은 종목별 검색이 주 기능
- 주요 종목 리스트를 순회하며 수집
- 각 종목별로 최근 N일 리포트 수집

### 2. 자동화
- 크롤링 완료 후 자동으로 정규화 및 저장
- 별도 스크립트 실행 불필요

### 3. 유연성
- 환경변수로 활성화/비활성화 제어
- DB 연결 실패 시에도 크롤링 결과는 유지

### 4. 오류 처리
- 정규화/저장 실패 시에도 크롤링 결과는 유지
- 상세한 로깅으로 문제 추적 가능

## 📊 로그 예시

### DB 저장 활성화 시
```
크롤링 실행 중: naver_finance (days=7, max=50)
🔍 네이버 금융 리서치 검색: 삼성전자 (최근 7일)
📋 발견된 리포트: 12개
✅ 크롤링 완료: naver_finance - 45개 보고서 수집
💾 DB 저장 완료: 45개 리포트 저장
```

### DB 저장 비활성화 시
```
크롤링 실행 중: naver_finance (days=7, max=50)
✅ 크롤링 완료: naver_finance - 45개 보고서 수집
DB 저장 비활성화 (ENABLE_DB_STORAGE=false 또는 DB_PASSWORD 없음)
```

## ⚠️ 주의사항

1. **데이터베이스 스키마**: `analyst_reports_schema.sql`을 먼저 적용해야 합니다.
2. **환경변수**: DB 저장을 사용하려면 환경변수 설정이 필요합니다.
3. **의존성**: `analyst_report_pipeline.py`, `korea_normalize.py`, `analyst_snapshot_store.py` 모듈 필요
4. **종목 리스트**: 현재는 하드코딩된 주요 종목 리스트를 사용합니다. 필요 시 확장 가능합니다.

## 🔍 개선 가능 사항

### 1. 종목 리스트 확장
- 설정 파일에서 종목 리스트 관리
- 대시보드에서 종목 리스트 편집 기능
- 인기 종목 자동 감지

### 2. 스케줄링 개선
- 종목별 스케줄링
- 우선순위 기반 수집

### 3. 성능 최적화
- 병렬 처리 (여러 종목 동시 검색)
- 캐싱 (중복 리포트 방지)

## 📚 관련 문서

- `PIPELINE_INTEGRATION_COMPLETE.md`: 한경 컨센서스 파이프라인 통합
- `COMPLETE_SYSTEM_INTEGRATION_SUMMARY.md`: 전체 시스템 통합 요약
- `crawler_naver_finance_research.py`: 네이버 금융 크롤러
- `analyst_report_pipeline.py`: 파이프라인 모듈

## ✨ 통합 완료

이제 한경 컨센서스와 네이버 금융 리서치 모두에서 크롤링한 리포트가 자동으로 정규화되어 PostgreSQL에 저장됩니다.

