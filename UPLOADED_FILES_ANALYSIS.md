# 업로드된 크롤링 전략 파일 분석 보고서

> 작성일: 2025-12-31  
> 분석 대상: 해외사이트 + 국내사이트 크롤링 전략  
> 목적: 현재 프로젝트에 유익한 부분 도출 및 적용 방안 제시

---

## 📊 전체 구조 분석

### 해외사이트 크롤링 전략

#### 1. **API 기반 수집 (우선순위 높음)**
- **Finnhub API**: 60 calls/분, 무료 tier
- **FMP API**: 250 calls/일, 무료 tier
- **장점**: 안정적, 빠름, 구조화된 데이터
- **단점**: API 키 필요, 호출 제한

#### 2. **웹 크롤링 (보조)**
- **Yahoo Finance**: Selenium 기반, 동적 로딩 처리
- **장점**: 무료, 광범위한 커버리지
- **단점**: 크롤링 난이도 높음, 불안정

#### 3. **정규화 시스템**
- `global_normalize.py`: 해외 데이터를 통일된 스키마로 변환
- **KoreaAnalystSnapshot v1** 형식으로 표준화
- 여러 소스 데이터 앙상블 병합 지원

### 국내사이트 크롤링 전략

#### 1. **네이버 금융 (1순위)**
- Selenium 기반 크롤링
- 30여개 증권사 리포트 통합
- PDF 다운로드 지원

#### 2. **한경 컨센서스 (2순위)**
- JavaScript 동적 로딩 처리 필요
- 컨센서스 계산 기능 내장

#### 3. **정규화 시스템**
- `korea_normalize.py`: 한국 시장 특화
- 6자리 종목 코드, KRW 통화 처리
- 한국 증권사 의견 정규화 매핑

#### 4. **PostgreSQL 저장소**
- `analyst_snapshot_store.py`: 컨센서스 계산 포함
- `upsert_snapshot()`, `fetch_consensus()` 기능

---

## 🎯 현재 프로젝트에 유익한 부분

### ✅ 즉시 적용 가능 (우선순위 높음)

#### 1. **정규화 시스템 통합**
**파일**: `korea_normalize.py`, `global_normalize.py`

**유익한 점**:
- 우리 크롤러들(`crawler_hankyung_consensus.py`, `crawler_naver_finance_research.py`)의 데이터를 표준 형식으로 변환
- 여러 소스 데이터를 통일된 스키마로 통합
- 컨센서스 계산을 위한 데이터 구조 제공

**적용 방안**:
```python
# 우리 프로젝트에 추가
from korea_normalize import normalize_from_naver, normalize_from_hankyung

# 네이버 크롤러 결과 정규화
reports = naver_crawler.search_by_stock("삼성전자", "005930")
for report in reports:
    snapshot = normalize_from_naver(report.to_dict())
    # 표준 형식으로 변환됨
```

**예상 효과**:
- 데이터 일관성 확보
- 컨센서스 계산 용이
- 여러 소스 통합 가능

---

#### 2. **PostgreSQL 저장소 시스템**
**파일**: `analyst_snapshot_store.py`

**유익한 점**:
- 컨센서스 자동 계산 (`fetch_consensus()`)
- 중복 방지 (`source_url` 기반)
- 최신 리포트 조회 (`fetch_latest()`)
- 의견 분포 집계

**적용 방안**:
```python
# 우리 프로젝트에 통합
from analyst_snapshot_store import AnalystSnapshotStore

# 저장소 초기화
store = AnalystSnapshotStore({
    'host': 'localhost',
    'database': 'crawler_db',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD')
})

# 리포트 저장
with store:
    for report in reports:
        snapshot = normalize_from_naver(report.to_dict())
        report_id = store.upsert_snapshot(snapshot)

# 컨센서스 조회
consensus = store.fetch_consensus('005930', days=30)
```

**예상 효과**:
- 자동 컨센서스 계산
- 데이터 중복 방지
- 효율적인 조회

---

#### 3. **API 기반 해외 데이터 수집**
**파일**: `finnhub_collector.py`, `fmp_collector.py`

**유익한 점**:
- 안정적인 API 기반 수집
- Rate limiting 자동 처리
- 구조화된 데이터 제공
- 무료 tier로 시작 가능

**적용 방안**:
```python
# 해외 종목 데이터 수집 추가
from finnhub_collector import FinnhubCollector
from fmp_collector import FMPCollector
from global_normalize import normalize_from_finnhub, merge_snapshots

# Finnhub
finnhub = FinnhubCollector(api_key=os.getenv('FINNHUB_API_KEY'))
finnhub_data = finnhub.collect_full_data('AAPL')
finnhub_snapshot = normalize_from_finnhub(finnhub_data, 'AAPL')

# FMP
fmp = FMPCollector(api_key=os.getenv('FMP_API_KEY'))
fmp_data = fmp.collect_full_data('AAPL')
fmp_snapshot = normalize_from_fmp(fmp_data, 'AAPL')

# 앙상블 병합
merged = merge_snapshots(finnhub_snapshot, fmp_snapshot)
```

**예상 효과**:
- 해외 종목 데이터 확보
- 안정적인 데이터 수집
- 여러 소스 앙상블로 신뢰도 향상

---

### 🔄 개선 가능 (우선순위 중간)

#### 4. **Selenium 크롤링 전략**
**파일**: `naver_crawler.py`, `yahoo_crawler.py`

**유익한 점**:
- 동적 로딩 사이트 크롤링 방법
- Context manager 패턴 사용
- 에러 처리 및 재시도 로직
- 랜덤 딜레이 전략

**현재 우리 프로젝트**:
- `crawler_naver_finance_research.py`: requests 기반 (정적 페이지)
- `crawler_hankyung_consensus.py`: requests 기반

**개선 방안**:
- 동적 로딩이 필요한 경우 Selenium으로 전환
- Context manager 패턴 적용
- 에러 처리 강화

---

#### 5. **앙상블 병합 전략**
**파일**: `global_normalize.py`의 `merge_snapshots()`

**유익한 점**:
- 여러 소스 데이터 가중 평균
- 신뢰도 기반 가중치 적용
- Missing 데이터 처리

**적용 방안**:
```python
# 우리 프로젝트에 적용
from global_normalize import merge_snapshots

# 한경 + 네이버 데이터 병합
hankyung_snapshot = normalize_from_hankyung(hankyung_data)
naver_snapshot = normalize_from_naver(naver_data)

# 가중치 설정 (신뢰도 기반)
merged = merge_snapshots(
    hankyung_snapshot,
    naver_snapshot,
    weights={'hankyung': 0.6, 'naver': 0.4}
)
```

**예상 효과**:
- 데이터 신뢰도 향상
- 소스별 특성 반영

---

### 📚 참고 가치 (우선순위 낮음)

#### 6. **전략 문서**
**파일**: `GLOBAL_SOURCES_STRATEGY.md`, `CORRECTED_STRATEGY.md`

**유익한 점**:
- 소스별 우선순위 결정 기준
- 구현 로드맵
- 비용 분석
- 주의사항

**활용 방안**:
- 우리 프로젝트 로드맵 수립 시 참고
- 소스 선택 기준으로 활용

---

## 🔧 구체적 적용 계획

### Phase 1: 정규화 시스템 통합 (1-2일)

**작업 내용**:
1. `korea_normalize.py` 파일 복사 및 수정
2. 우리 크롤러 데이터 형식에 맞게 조정
3. `normalize_from_naver()`, `normalize_from_hankyung()` 적용

**예상 효과**:
- 데이터 일관성 확보
- 컨센서스 계산 준비

---

### Phase 2: PostgreSQL 저장소 통합 (2-3일)

**작업 내용**:
1. `analyst_snapshot_store.py` 파일 복사
2. 우리 DB 스키마에 맞게 조정
3. `upsert_snapshot()`, `fetch_consensus()` 테스트

**예상 효과**:
- 자동 컨센서스 계산
- 효율적인 데이터 관리

---

### Phase 3: 해외 API 통합 (선택, 2-3일)

**작업 내용**:
1. Finnhub, FMP API 키 발급
2. `finnhub_collector.py`, `fmp_collector.py` 통합
3. 해외 종목 데이터 수집 테스트

**예상 효과**:
- 해외 종목 데이터 확보
- 글로벌 시장 분석 가능

---

## 📊 비교 분석

### 현재 우리 프로젝트 vs 업로드된 전략

| 항목 | 현재 우리 | 업로드된 전략 | 개선 방안 |
|------|-----------|---------------|-----------|
| **정규화** | ❌ 없음 | ✅ 통일된 스키마 | 즉시 적용 |
| **저장소** | ⚠️ JSON 파일 | ✅ PostgreSQL + 컨센서스 | 통합 권장 |
| **해외 데이터** | ❌ 없음 | ✅ API 기반 | 선택적 적용 |
| **앙상블** | ❌ 없음 | ✅ 가중 평균 병합 | 향후 적용 |
| **Selenium** | ⚠️ requests 기반 | ✅ Selenium 전략 | 필요 시 적용 |

---

## 🎯 우선순위별 적용 계획

### 즉시 적용 (이번 주)

1. **정규화 시스템 통합**
   - `korea_normalize.py` 적용
   - 우리 크롤러 데이터 정규화

2. **PostgreSQL 저장소 통합**
   - `analyst_snapshot_store.py` 적용
   - 컨센서스 계산 기능 활용

### 단기 적용 (다음 주)

3. **앙상블 병합**
   - 여러 소스 데이터 통합
   - 가중치 기반 병합

4. **Selenium 전략 개선**
   - 동적 로딩 사이트 대응
   - 에러 처리 강화

### 중기 적용 (선택)

5. **해외 API 통합**
   - Finnhub, FMP API 추가
   - 글로벌 종목 데이터 수집

---

## 💡 핵심 인사이트

### 1. 정규화의 중요성
- 여러 소스 데이터를 통일된 형식으로 변환
- 컨센서스 계산 및 분석 용이
- **즉시 적용 권장**

### 2. PostgreSQL 저장소의 가치
- 자동 컨센서스 계산
- 효율적인 조회 및 집계
- **통합 권장**

### 3. API vs 크롤링
- API: 안정적, 빠름, 구조화됨
- 크롤링: 유연하지만 불안정
- **해외는 API 우선, 국내는 크롤링 필요**

### 4. 앙상블 전략
- 여러 소스 데이터 병합으로 신뢰도 향상
- 가중치 기반 평균 계산
- **향후 적용 권장**

---

## 📝 다음 단계

### 즉시 작업
1. `korea_normalize.py` 파일 복사 및 수정
2. 우리 크롤러에 정규화 적용
3. `analyst_snapshot_store.py` 통합 검토

### 이번 주
4. PostgreSQL 저장소 통합
5. 컨센서스 계산 테스트
6. 데이터 품질 검증

### 다음 주
7. 앙상블 병합 구현
8. 해외 API 통합 검토 (선택)

---

## ✅ 결론

### 즉시 적용 권장
- ✅ **정규화 시스템**: 데이터 일관성 확보
- ✅ **PostgreSQL 저장소**: 컨센서스 자동 계산

### 단기 적용 권장
- 🔄 **앙상블 병합**: 신뢰도 향상
- 🔄 **Selenium 전략**: 동적 로딩 대응

### 선택적 적용
- 📚 **해외 API**: 글로벌 데이터 확보 (필요 시)

---

*작성일: 2025-12-31*  
*분석 완료: 해외사이트 + 국내사이트 크롤링 전략*  
*다음: 정규화 시스템 통합 시작*


