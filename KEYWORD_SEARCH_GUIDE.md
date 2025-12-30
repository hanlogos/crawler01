# 키워드 검색 시스템 가이드

## 📋 개요

구글 검색창처럼 키워드로 관련 회사/산업군/섹터를 검색하고, 검색 결과를 요약하여 보고하는 시스템입니다.

## ✅ 구현 완료 기능

### 1. 키워드 검색 엔진 (`keyword_search_engine.py`)
- ✅ 보고서 검색
- ✅ 뉴스 검색
- ✅ 종목 검색
- ✅ 관련도 점수 계산
- ✅ 종목 코드/섹터 필터링

### 2. 검색 히스토리 관리 (`SearchHistoryManager`)
- ✅ 검색 내역 자동 저장
- ✅ 최근 검색 조회
- ✅ 인기 검색어 통계
- ✅ 자주 검색한 키워드 추적

### 3. 즐겨찾기 관리 (`FavoriteManager`)
- ✅ 종목/키워드/섹터 즐겨찾기
- ✅ 자주 사용한 즐겨찾기 추적
- ✅ 사용 횟수 카운트

### 4. 검색 결과 요약 (`search_summary_generator.py`)
- ✅ AI 기반 요약 생성 (Ollama)
- ✅ 주요 발견사항 추출
- ✅ 종목별 요약
- ✅ 소스별 통계

### 5. 대시보드 통합
- ✅ 검색 탭 추가
- ✅ 검색 UI (구글 스타일)
- ✅ 결과 테이블
- ✅ 요약 및 분석 표시

## 🚀 사용 방법

### 대시보드에서 검색

1. 대시보드 실행
```bash
python enhanced_crawling_dashboard.py
```

2. "🔍 키워드 검색" 탭 선택

3. 검색어 입력 및 검색
   - 검색어 입력 (예: "삼성전자", "반도체", "HBM")
   - 검색 타입 선택 (전체/보고서/뉴스/종목)
   - "🔍 검색" 버튼 클릭 또는 Enter

4. 결과 확인
   - 왼쪽: 검색 결과 테이블
   - 오른쪽: AI 요약 및 분석

### Python 코드에서 사용

```python
from keyword_search_engine import KeywordSearchEngine, SearchHistoryManager, FavoriteManager
from report_title_manager import ReportTitleManager
from search_summary_generator import SearchSummaryGenerator

# 초기화
report_manager = ReportTitleManager()
search_engine = KeywordSearchEngine(report_manager=report_manager)
history_manager = SearchHistoryManager()
favorite_manager = FavoriteManager()
summary_generator = SearchSummaryGenerator(use_ollama=True)

# 검색
results, query = search_engine.search("삼성전자", search_type='all', limit=50)

# 히스토리 저장
history_manager.add_search(query)

# 요약 생성
summary = summary_generator.generate_summary("삼성전자", results)
print(summary['summary'])

# 즐겨찾기 추가
favorite_manager.add_favorite('stock', '삼성전자', '005930')
```

## 📊 검색 기능 상세

### 검색 타입

1. **전체**: 보고서, 뉴스, 종목 모두 검색
2. **보고서**: 리포트 제목 및 키워드 검색
3. **뉴스**: 뉴스 기사 제목 및 내용 검색
4. **종목**: 종목명 및 종목 코드 검색

### 관련도 점수

- 0.8 이상: 높은 관련도 (녹색)
- 0.5~0.8: 중간 관련도 (노란색)
- 0.5 미만: 낮은 관련도 (빨간색)

### 검색 히스토리

- 최근 1000개 검색 내역 보관
- 검색어별 통계 제공
- 자주 검색한 키워드 추적

### 즐겨찾기

- 종목, 키워드, 섹터 즐겨찾기 가능
- 사용 횟수 자동 카운트
- 자주 사용한 즐겨찾기 우선 표시

## 🔍 검색 예제

### 종목 검색
```
검색어: "삼성전자"
결과: 보고서, 뉴스, 종목 정보
```

### 산업군 검색
```
검색어: "반도체"
결과: 반도체 관련 모든 자료
```

### 키워드 검색
```
검색어: "HBM"
결과: HBM 관련 보고서 및 뉴스
```

## 📁 데이터 저장

- 검색 히스토리: `search_history.json`
- 즐겨찾기: `favorites.json`
- 자동 저장 (검색/즐겨찾기 추가 시)

## 🎯 주요 특징

1. **통합 검색**: 보고서, 뉴스, 종목을 한 번에 검색
2. **AI 요약**: Ollama를 사용한 검색 결과 요약
3. **히스토리 관리**: 검색 내역 자동 저장 및 추적
4. **즐겨찾기**: 자주 찾는 종목/키워드 저장
5. **관련도 점수**: 검색 결과의 관련도 자동 계산

## 🔄 연계성

- 검색 히스토리 → 자주 찾는 종목 자동 추출
- 즐겨찾기 → 빠른 재검색
- 검색 결과 → 상세 정보 조회 가능

## 📝 다음 단계

1. 검색 결과 상세 보기 기능
2. 검색 필터 고도화 (날짜, 섹터 등)
3. 검색 결과 내보내기 (CSV, PDF)
4. 검색 알림 설정 (새 자료 발견 시)

---

**구현 완료일**: 2025-12-30  
**버전**: 1.0.0  
**상태**: ✅ 완료

