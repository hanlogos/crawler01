# 🔍 검색 시스템 비교 및 DB 연동 필요성

## 📊 현재 시스템 vs 통합 시스템

### 현재 사용 중: `keyword_search_engine.py` (JSON 기반)

**데이터 소스:**
- ✅ `report_titles.json` (보고서 제목)
- ❌ 뉴스 (실시간 크롤링 비활성화)
- ⚠️ 종목 (하드코딩된 매핑)

**지원 기능:**
- ✅ 기본 검색 (보고서/종목)
- ✅ 검색 히스토리 (JSON 파일)
- ✅ 즐겨찾기 (JSON 파일)
- ✅ AI 요약 (Ollama 기반)

**제한 사항:**
- ❌ 신뢰도 검증 없음
- ❌ 팩트 체크 없음
- ❌ 데이터 신선도 추적 없음
- ❌ AI 인사이트 (매수/매도 추천) 없음
- ❌ 시스템 메트릭 없음
- ❌ 액션 버튼 없음
- ❌ 관련 종목 현재가/등락률 없음

---

### 통합 시스템: `integrated_search_engine.py` (PostgreSQL 기반)

**데이터 소스:**
- ✅ PostgreSQL `news_articles` 테이블
- ✅ `fact_checks` 테이블 (팩트 체크 결과)
- ✅ `crawl_jobs` 테이블 (크롤러 상태)

**지원 기능 (a+b+c 완전 통합):**

#### a (사용자 관점)
- ✅ **AI 인사이트**: 매수/매도 추천, 신뢰도 점수
- ✅ **액션 버튼**: 차트 보기, 관심종목 추가, 알림 설정
- ✅ **관련 종목 정보**: 현재가, 등락률, 거래량 비율

#### b (시스템 관점)
- ✅ **성능 모니터링**: 검색 시간 (ms), 캐시 히트율
- ✅ **크롤러 상태**: 실시간 소스별 상태 (정상/지연)
- ✅ **데이터 신선도**: 마지막 업데이트 시간
- ✅ **에러 핸들링**: 사용자 친화적 오류 메시지

#### c (정보 품질)
- ✅ **신뢰도 검증**: 4단계 시스템
  - VERIFIED (90%+): ✅ 검증됨
  - UNVERIFIED (60-89%): ⚠️ 미검증
  - DISPUTED (40-59%): ⚡ 논쟁중
  - FALSE (<40%): ❌ 거짓
- ✅ **데이터 신선도**: HOT/FRESH/NORMAL/OLD
- ✅ **팩트 체크**: 교차 검증, LLM 검증
- ✅ **소스 Tier**: Tier 1/2/3 분류

---

## 🔄 DB 연동 필요성

### 질문: a+b+c 기능들은 DB 연동 후에만 표시되나요?

**답변: 네, 맞습니다.**

| 기능 | 현재 (JSON) | DB 연동 후 |
|------|------------|-----------|
| **기본 검색** | ✅ 가능 | ✅ 가능 |
| **AI 요약** | ✅ 가능 | ✅ 가능 |
| **신뢰도 검증** | ❌ 불가능 | ✅ 가능 |
| **팩트 체크** | ❌ 불가능 | ✅ 가능 |
| **데이터 신선도** | ❌ 불가능 | ✅ 가능 |
| **AI 인사이트 (매수/매도)** | ❌ 불가능 | ✅ 가능 |
| **시스템 메트릭** | ❌ 불가능 | ✅ 가능 |
| **크롤러 상태** | ❌ 불가능 | ✅ 가능 |
| **액션 버튼** | ❌ 불가능 | ✅ 가능 |
| **관련 종목 현재가** | ❌ 불가능 | ✅ 가능 (API 연동 필요) |

---

## 🚀 DB 연동 방법

### Step 1: PostgreSQL 설정

```bash
# 1. PostgreSQL 실행
sudo systemctl start postgresql

# 2. 데이터베이스 생성
psql -U postgres
CREATE DATABASE abiseu;

# 3. 스키마 적용
\c abiseu
\i news_ingestion_schema.sql
```

### Step 2: 뉴스 수집 서비스 실행

```bash
# 뉴스 크롤링 및 DB 저장
python news_ingestion_service.py
```

### Step 3: 대시보드에 통합 검색 엔진 추가

```python
# enhanced_crawling_dashboard.py 수정

# 기존
self.search_engine = KeywordSearchEngine(...)

# 추가 (선택 가능)
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'abiseu',
    'user': 'postgres',
    'password': 'your_password'
}

try:
    from integrated_search_engine import IntegratedSearchEngine
    self.integrated_search_engine = IntegratedSearchEngine(DB_PARAMS, enable_ai=True)
except:
    self.integrated_search_engine = None
```

### Step 4: 검색 탭에서 선택 사용

```python
# 사용자가 선택할 수 있도록
# - "기본 검색" (JSON 기반, 빠름)
# - "통합 검색" (DB 기반, a+b+c 기능)
```

---

## 💡 권장 사용 시나리오

### 시나리오 1: 빠른 검색 (현재)
- **용도**: 보고서 제목 빠른 검색
- **엔진**: `keyword_search_engine.py`
- **장점**: 빠름, DB 불필요
- **단점**: a+b+c 기능 없음

### 시나리오 2: 고급 검색 (DB 연동 후)
- **용도**: 신뢰도 검증, AI 인사이트 필요
- **엔진**: `integrated_search_engine.py`
- **장점**: a+b+c 모든 기능
- **단점**: DB 설정 필요, 약간 느림

### 시나리오 3: 병행 사용 (권장)
- **기본 검색**: 빠른 보고서 검색
- **통합 검색**: 뉴스 + 팩트 체크 + AI 인사이트

---

## 📋 요약

**질문에 대한 답변:**

> a+b+c 기능들 (AI 인사이트, 신뢰도 검증, 시스템 메트릭 등)은 **DB 연동 후에만 표시**됩니다.

**이유:**
1. **신뢰도 검증**: `fact_checks` 테이블 필요
2. **팩트 체크**: `news_articles` + `fact_checks` JOIN 필요
3. **크롤러 상태**: `crawl_jobs` 테이블 필요
4. **데이터 신선도**: `published_at`, `collected_at` 컬럼 필요
5. **AI 인사이트**: 감성 분석, 긴급도 등 메타데이터 필요

**현재 상태:**
- ✅ 기본 검색 + AI 요약: **DB 없이 가능**
- ❌ a+b+c 고급 기능: **DB 필수**

---

## 🎯 다음 단계

1. **PostgreSQL 설정** (필수)
2. **스키마 적용** (`news_ingestion_schema.sql`)
3. **뉴스 수집 서비스 실행** (데이터 수집)
4. **대시보드에 통합 검색 탭 추가** (선택)

자세한 내용은 `INTEGRATED_SEARCH_GUIDE.md` 참고하세요.


