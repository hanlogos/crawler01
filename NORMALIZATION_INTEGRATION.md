# 정규화 시스템 통합 완료 보고서

## 📋 개요

업로드된 파일 분석 결과를 바탕으로, **korea_normalize.py**와 **analyst_snapshot_store.py**를 프로젝트에 통합했습니다.

## ✅ 완료된 작업

### 1. 정규화 시스템 통합 (`korea_normalize.py`)

**위치**: `korea_normalize.py`

**주요 기능**:
- 한국 애널리스트 리포트를 **KoreaAnalystSnapshot v1** 형식으로 정규화
- 지원 소스: `38com`, `hankyung`, `naver`
- 의견 정규화: 매수(강력) → Strong Buy, 매수 → Buy, 중립 → Hold 등
- 목표주가, 신뢰도, 애널리스트 정보 자동 추출

**주요 함수**:
```python
normalize_opinion(opinion_text) -> str
normalize_from_38com(raw_data) -> Dict
normalize_from_hankyung(raw_data) -> Dict
normalize_from_naver(raw_data) -> Dict
normalize_report_metadata(report, source='auto') -> Dict
```

**사용 예시**:
```python
from korea_normalize import normalize_report_metadata

# ReportMetadata 객체 또는 dict를 정규화
snapshot = normalize_report_metadata(report.to_dict(), source='naver')
```

### 2. PostgreSQL 저장소 통합 (`analyst_snapshot_store.py`)

**위치**: `analyst_snapshot_store.py`

**주요 기능**:
- 정규화된 스냅샷을 PostgreSQL에 저장/조회
- 컨센서스 계산 (최근 N일 리포트 집계)
- 최신 리포트 조회

**주요 메서드**:
```python
store.upsert_snapshot(snapshot) -> str  # 저장/업데이트
store.fetch_latest(stock_code, source, limit) -> List[Dict]
store.fetch_consensus(stock_code, days=30) -> Optional[Dict]
```

**사용 예시**:
```python
from analyst_snapshot_store import AnalystSnapshotStore

db_params = {
    'host': 'localhost',
    'database': 'crawler_db',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD')
}

with AnalystSnapshotStore(db_params) as store:
    report_id = store.upsert_snapshot(snapshot)
    consensus = store.fetch_consensus('005930', days=30)
```

### 3. 데이터베이스 스키마 생성 (`analyst_reports_schema.sql`)

**위치**: `analyst_reports_schema.sql`

**테이블 구조**:
- `analyst_reports`: 리포트 메인 테이블
  - `report_id` (UUID, PK)
  - `source`, `source_url` (unique)
  - `stock_code`, `stock_name`
  - `published_at`, `opinion`, `target_price`
  - `analyst_name`, `analyst_firm`
  - `trust_score`
  - `structured_data` (JSONB, 전체 스냅샷)

**인덱스**:
- 종목 코드, 발행일, 소스, 의견별 인덱스
- JSONB 필드 검색용 GIN 인덱스

**뷰**:
- `v_analyst_consensus`: 최근 30일 컨센서스 집계

**적용 방법**:
```sql
-- PostgreSQL에서 실행
\i analyst_reports_schema.sql
```

### 4. 파이프라인 모듈 생성 (`analyst_report_pipeline.py`)

**위치**: `analyst_report_pipeline.py`

**주요 기능**:
- 크롤러 → 정규화 → 저장 자동화
- 오류 처리 및 로깅
- DB 저장 활성화/비활성화 옵션

**사용 예시**:
```python
from analyst_report_pipeline import AnalystReportPipeline

db_params = {...}
pipeline = AnalystReportPipeline(db_params)

# 크롤러에서 수집한 리포트 처리
reports = crawler.search_by_stock("삼성전자", "005930")
saved_count = pipeline.process_reports(reports, source='naver')

# 컨센서스 조회
consensus = pipeline.get_consensus('005930', days=30)
```

## 🔗 크롤러 통합 방법

### 방법 1: 파이프라인 사용 (권장)

```python
from analyst_report_pipeline import AnalystReportPipeline

# 크롤러 실행
reports = crawler.search_by_stock("삼성전자", "005930", days=7)

# 파이프라인으로 처리
pipeline = AnalystReportPipeline(db_params)
saved_count = pipeline.process_reports(reports, source='naver')
```

### 방법 2: 직접 통합

```python
from korea_normalize import normalize_report_metadata
from analyst_snapshot_store import AnalystSnapshotStore

# 정규화
snapshot = normalize_report_metadata(report.to_dict(), source='naver')

# 저장
with AnalystSnapshotStore(db_params) as store:
    report_id = store.upsert_snapshot(snapshot)
```

## 📊 데이터 흐름

```
크롤러 (ReportMetadata)
    ↓
정규화 (korea_normalize.py)
    ↓
KoreaAnalystSnapshot v1
    ↓
PostgreSQL 저장 (analyst_snapshot_store.py)
    ↓
컨센서스 계산 / 조회
```

## 🎯 다음 단계

### 즉시 적용 가능
1. ✅ **정규화 시스템**: 완료
2. ✅ **PostgreSQL 저장소**: 완료
3. ⏳ **크롤러 통합**: `site_crawling_manager.py`에 파이프라인 추가 필요

### 선택적 작업
1. **global_normalize.py 통합**: 해외 데이터 정규화 (Finnhub, FMP)
2. **앙상블 병합**: 여러 소스 데이터 통합 전략
3. **자동 스케줄링**: Windows Task Scheduler 연동

## 📝 환경 변수 설정

```bash
# .env 파일 또는 환경 변수
DB_HOST=localhost
DB_NAME=crawler_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## 🔍 테스트

### 정규화 테스트
```bash
python korea_normalize.py
```

### 저장소 테스트
```bash
python analyst_snapshot_store.py
```

### 파이프라인 테스트
```bash
python analyst_report_pipeline.py
```

## 📚 참고 문서

- `korea_analyst_snapshot_v1.schema.json`: 스키마 정의
- `UPLOADED_FILES_ANALYSIS.md`: 업로드 파일 분석 결과
- `DEVELOPMENT_GOVERNANCE_GUIDE.md`: 개발 거버넌스 가이드

## ⚠️ 주의사항

1. **데이터베이스 스키마**: `analyst_reports_schema.sql`을 먼저 적용해야 합니다.
2. **환경 변수**: DB 연결 정보를 환경 변수로 설정하세요.
3. **에러 처리**: `skip_errors=True`로 설정하면 오류 발생 시 건너뛰고 계속 진행합니다.
4. **중복 방지**: `source_url`을 unique key로 사용하여 중복 저장을 방지합니다.

## ✨ 주요 개선사항

1. **표준화**: 모든 크롤러 데이터를 동일한 형식으로 정규화
2. **자동화**: 크롤링 → 정규화 → 저장 파이프라인 자동화
3. **확장성**: 새로운 소스 추가 시 `normalize_from_*` 함수만 추가하면 됨
4. **신뢰도**: 소스별 신뢰도 점수 자동 계산
5. **컨센서스**: 여러 리포트를 집계하여 컨센서스 계산

