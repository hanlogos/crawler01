# 🚀 통합 검색 시스템 확장 가이드

## 📋 개요

이 가이드는 **a+b+c 완전 통합 검색 시스템**을 현재 프로젝트에 통합하는 방법을 설명합니다.

### 통합 목표

- **a (사용자 관점)**: 직관적 UI, AI 인사이트, 액션 가능한 정보
- **b (시스템 관점)**: 성능 모니터링, 크롤러 상태, 에러 핸들링
- **c (정보 품질)**: 신뢰도 검증, 팩트 체크, 데이터 신선도

---

## 📁 추가된 파일

### 1. `enhanced_search_result.py`
- **목적**: 고급 검색 결과 데이터 모델
- **기능**:
  - 신뢰도 점수 시스템 (4단계)
  - 데이터 신선도 추적
  - AI 인사이트 모델
  - 시스템 메트릭 수집

### 2. `integrated_search_engine.py` (추가 예정)
- **목적**: PostgreSQL 기반 통합 검색 엔진
- **기능**:
  - DB에서 뉴스/리포트 검색
  - 신뢰도 자동 계산
  - AI 인사이트 생성
  - 시스템 상태 모니터링

### 3. `enhanced_dashboard_app.py` (선택사항)
- **목적**: Flask 웹 서버 (PyQt5 대시보드 대체/보완)
- **기능**:
  - REST API 제공
  - 웹 기반 UI

---

## 🔄 현재 시스템과의 통합

### 현재 구조

```
현재 시스템:
├── keyword_search_engine.py (JSON 기반)
├── enhanced_crawling_dashboard.py (PyQt5)
└── news_ingestion_service.py (PostgreSQL)
```

### 통합 후 구조

```
통합 시스템:
├── keyword_search_engine.py (기존 - JSON 기반)
├── integrated_search_engine.py (신규 - PostgreSQL 기반)
├── enhanced_search_result.py (신규 - 데이터 모델)
├── enhanced_crawling_dashboard.py (PyQt5 - 확장)
└── enhanced_dashboard_app.py (선택 - Flask 웹)
```

---

## 🛠️ 통합 방법

### 방법 1: 점진적 통합 (권장)

#### Step 1: 데이터 모델 추가
```bash
# 이미 추가됨: enhanced_search_result.py
```

#### Step 2: 통합 검색 엔진 추가
```python
# integrated_search_engine.py를 프로젝트에 추가
# PostgreSQL 연결 필요
```

#### Step 3: 대시보드 확장
```python
# enhanced_crawling_dashboard.py에 통합 검색 탭 추가
# 기존 keyword_search_engine과 병행 사용
```

### 방법 2: 완전 교체

기존 `keyword_search_engine.py`를 `integrated_search_engine.py`로 교체 (PostgreSQL 필수)

---

## 📊 기능 비교

| 기능 | 현재 (keyword_search) | 확장 (integrated) |
|------|---------------------|-------------------|
| 데이터 소스 | JSON 파일 | PostgreSQL |
| 신뢰도 검증 | ❌ | ✅ 4단계 시스템 |
| AI 인사이트 | ✅ (요약만) | ✅ (매수/매도 추천) |
| 시스템 메트릭 | ❌ | ✅ (성능/상태) |
| 데이터 신선도 | ❌ | ✅ (HOT/FRESH/NORMAL/OLD) |
| 팩트 체크 | ❌ | ✅ (교차 검증) |

---

## 🚀 빠른 시작

### 1. PostgreSQL 설정 (필수)

```bash
# 데이터베이스 생성
psql -U postgres
CREATE DATABASE abiseu;

# 스키마 적용
\c abiseu
\i news_ingestion_schema.sql
```

### 2. 통합 검색 엔진 사용

```python
from integrated_search_engine import IntegratedSearchEngine

# DB 연결 설정
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'abiseu',
    'user': 'postgres',
    'password': 'your_password'
}

# 검색 엔진 초기화
engine = IntegratedSearchEngine(DB_PARAMS, enable_ai=True)

# 검색 실행
result = engine.search("삼성전자", limit=20, include_ai_insight=True)

# 결과 확인
print(f"총 {result.total_count}개 결과")
print(f"AI 추천: {result.ai_insight.recommendation}")
print(f"검색 시간: {result.metrics.search_time_ms}ms")
```

### 3. 대시보드 통합

```python
# enhanced_crawling_dashboard.py에 추가

def _create_integrated_search_tab(self) -> QWidget:
    """통합 검색 탭 (a+b+c)"""
    widget = QWidget()
    layout = QVBoxLayout()
    
    # 검색 입력
    search_input = QLineEdit()
    search_input.setPlaceholderText("통합 검색 (PostgreSQL 기반)")
    
    # 검색 버튼
    search_btn = QPushButton("🔍 통합 검색")
    search_btn.clicked.connect(lambda: self.perform_integrated_search())
    
    # 결과 표시 (신뢰도, AI 인사이트 포함)
    # ...
    
    return widget
```

---

## 💡 사용 시나리오

### 시나리오 1: 기존 시스템 유지 + 확장 추가

```python
# 기존: JSON 기반 빠른 검색
basic_results = keyword_engine.search("삼성전자")

# 확장: PostgreSQL 기반 고급 검색
enhanced_results = integrated_engine.search("삼성전자", include_ai_insight=True)

# 두 결과를 병합하여 표시
```

### 시나리오 2: 단계적 마이그레이션

1. **Phase 1**: 통합 검색 엔진 추가 (병행)
2. **Phase 2**: 데이터를 PostgreSQL로 이전
3. **Phase 3**: 기존 JSON 검색 제거

---

## 🔍 주요 기능 상세

### 1. 신뢰도 시스템 (정보 품질 c)

```python
# 4단계 검증 상태
- VERIFIED (90%+): ✅ 검증됨
- UNVERIFIED (60-89%): ⚠️ 미검증
- DISPUTED (40-59%): ⚡ 논쟁중
- FALSE (<40%): ❌ 거짓

# 신뢰도 계산 요소
- 소스 Tier (공식/언론/커뮤니티)
- 교차 검증 점수
- 과거 정확도
- LLM 신뢰도
```

### 2. AI 인사이트 (사용자 관점 a)

```python
# 추천 종류
- 🚀 강력 매수 (85%+)
- 📈 매수 (70-84%)
- 📊 보유 (60-69%)
- 📉 매도 (60-69%)
- ⚠️ 강력 매도 (70%+)

# 제공 정보
- 핵심 3줄 요약
- 근거 리스트
- 리스크 분석
```

### 3. 시스템 메트릭 (시스템 관점 b)

```python
# 수집 정보
- 검색 응답 시간
- 데이터 신선도
- 크롤러 상태
- 캐시 히트율
```

---

## ⚙️ 설정 및 커스터마이징

### DB 연결 설정

```python
# integrated_search_engine.py 수정
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'abiseu',
    'user': 'postgres',
    'password': 'your_password'  # 실제 비밀번호로 변경
}
```

### AI 인사이트 로직 커스터마이징

```python
# integrated_search_engine.py의 _generate_ai_insight() 수정
# 또는 Ollama/OpenAI API 연동
```

---

## 🐛 트러블슈팅

### 1. PostgreSQL 연결 오류

```bash
# PostgreSQL 실행 확인
sudo systemctl status postgresql

# 포트 확인
sudo netstat -tlnp | grep 5432
```

### 2. 스키마 없음 오류

```bash
# 스키마 적용
psql -U postgres -d abiseu -f news_ingestion_schema.sql
```

### 3. 데이터 없음

```bash
# 뉴스 수집 서비스 실행
python news_ingestion_service.py
```

---

## 📈 성능 최적화

### 1. 인덱스 추가

```sql
-- 자주 검색하는 컬럼에 인덱스
CREATE INDEX idx_title_search ON news_articles USING GIN(to_tsvector('korean', title));
CREATE INDEX idx_published_urgency ON news_articles(published_at DESC, urgency_level DESC);
```

### 2. 캐싱

```python
# Redis 캐싱 추가 (미구현)
import redis
cache = redis.Redis(host='localhost', port=6379)
```

---

## 🎯 다음 단계

1. **통합 검색 엔진 추가**: `integrated_search_engine.py` 복사
2. **대시보드 확장**: 통합 검색 탭 추가
3. **데이터 마이그레이션**: JSON → PostgreSQL
4. **웹 UI 추가** (선택): Flask 서버 실행

---

## 📚 참고 문서

- `COMPLETE_INTEGRATION_GUIDE.md`: 전체 통합 가이드
- `enhanced_search_result.py`: 데이터 모델 상세
- `integrated_search_engine.py`: 검색 엔진 구현
- `news_ingestion_schema.sql`: DB 스키마

---

**버전**: 1.0.0  
**작성일**: 2025-01-01  
**상태**: ✅ 통합 준비 완료



