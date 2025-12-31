# 크롤러-정규화-저장 파이프라인 통합 완료 보고서

## ✅ 완료된 통합

### site_crawling_manager.py에 정규화/저장 파이프라인 통합

**목표**: 크롤링 → 정규화 → PostgreSQL 저장을 자동으로 수행

## 🔧 구현 내용

### 1. 한경 컨센서스 크롤러에 파이프라인 통합

**위치**: `site_crawling_manager.py` - `_crawling_worker()` 메서드

**기능**:
- 한경 컨센서스 크롤링 완료 후 자동으로 정규화 및 저장
- 환경변수로 DB 저장 활성화/비활성화 제어
- 오류 발생 시에도 크롤링 결과는 유지

**동작 조건**:
- `ENABLE_DB_STORAGE=true` 환경변수 설정
- `DB_PASSWORD` 환경변수 설정 (DB 연결 필수)
- `analyst_report_pipeline.py` 모듈 사용 가능

## 📊 통합 흐름

```
1. site_crawling_manager에서 크롤링 시작
   ↓
2. 한경 컨센서스 크롤러 실행
   ↓
3. 리포트 수집 완료
   ↓
4. 정규화 파이프라인 실행 (옵션)
   - AnalystReportPipeline 초기화
   - 리포트 정규화 (korea_normalize.py)
   - PostgreSQL 저장 (analyst_snapshot_store.py)
   ↓
5. 결과 로깅
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
manager.start_crawling("hankyung_consensus", days=7, max_reports=50)
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
manager.start_crawling("hankyung_consensus", days=7, max_reports=50)
# 자동으로 정규화 및 DB 저장 수행
```

### 3. 직접 파이프라인 사용

```python
from crawler_hankyung_consensus import HankyungConsensusCrawler
from analyst_report_pipeline import AnalystReportPipeline
import os

# 크롤링
crawler = HankyungConsensusCrawler()
reports = crawler.crawl_recent_reports(days=7, max_reports=50)

# 정규화 및 저장
db_params = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'crawler_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

pipeline = AnalystReportPipeline(db_params, enable_db=True)
saved_count = pipeline.process_reports(reports, source='hankyung')
print(f"저장된 리포트: {saved_count}개")
```

## 🎯 주요 특징

### 1. 자동화
- 크롤링 완료 후 자동으로 정규화 및 저장
- 별도 스크립트 실행 불필요

### 2. 유연성
- 환경변수로 활성화/비활성화 제어
- DB 연결 실패 시에도 크롤링 결과는 유지

### 3. 오류 처리
- 정규화/저장 실패 시에도 크롤링 결과는 유지
- 상세한 로깅으로 문제 추적 가능

## 📊 로그 예시

### DB 저장 활성화 시
```
크롤링 실행 중: hankyung_consensus (days=7, max=50)
✅ 크롤링 완료: hankyung_consensus - 15개 보고서 수집
💾 DB 저장 완료: 15개 리포트 저장
```

### DB 저장 비활성화 시
```
크롤링 실행 중: hankyung_consensus (days=7, max=50)
✅ 크롤링 완료: hankyung_consensus - 15개 보고서 수집
DB 저장 비활성화 (ENABLE_DB_STORAGE=false 또는 DB_PASSWORD 없음)
```

### 모듈 없음 시
```
크롤링 실행 중: hankyung_consensus (days=7, max=50)
✅ 크롤링 완료: hankyung_consensus - 15개 보고서 수집
정규화 파이프라인 모듈을 사용할 수 없습니다. 크롤링만 수행합니다.
```

## ⚠️ 주의사항

1. **데이터베이스 스키마**: `analyst_reports_schema.sql`을 먼저 적용해야 합니다.
2. **환경변수**: DB 저장을 사용하려면 환경변수 설정이 필요합니다.
3. **의존성**: `analyst_report_pipeline.py`, `korea_normalize.py`, `analyst_snapshot_store.py` 모듈 필요

## 🔍 다음 단계 (선택)

1. **다른 크롤러 통합**: 네이버 금융, 38커뮤니케이션 등에도 파이프라인 통합
2. **대시보드 연동**: 대시보드에서 DB 저장 상태 표시
3. **스케줄링**: 자동 스케줄링 시 DB 저장 포함
4. **모니터링**: 저장 성공/실패 통계 수집

## 📚 관련 문서

- `NORMALIZATION_INTEGRATION.md`: 정규화 시스템 통합 완료 보고서
- `analyst_report_pipeline.py`: 파이프라인 모듈
- `site_crawling_manager.py`: 크롤링 관리자
- `analyst_reports_schema.sql`: 데이터베이스 스키마

