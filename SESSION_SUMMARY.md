# 크롤러 시스템 세션 요약

## 📋 프로젝트 개요

38커뮤니케이션(38.co.kr) 증권 리포트 크롤러 시스템
- 목표: 증권 리포트 자동 수집 및 분석
- 상태: ✅ 완전한 통합 시스템 구축 완료

## ✅ 완성된 주요 시스템

### 1. 기본 크롤링 시스템
- `crawler_38com.py` - 메인 크롤러
- `adaptive_crawler.py` - 적응형 크롤러
- `site_structure_analyzer.py` - 사이트 구조 분석
- `adaptive_parser.py` - 적응형 파서
- `structure_monitor.py` - 구조 변경 감지
- `category_classifier.py` - 카테고리 분류

### 2. 차단 방지 시스템
- `fake_face_system.py` - 페이크 페이스 (4가지 프로필)
- `time_based_strategy.py` - 시간대별 전략
- `risk_management_system.py` - 리스크 관리 (3단계 + 자동 복구)

### 3. 데이터 관리 시스템
- `report_title_manager.py` - 보고서 제목 관리 (원본 + AI 요약)
- `data_structure_templates.py` - 데이터 구조 템플릿
- `crawling_scenarios.py` - 크롤링 시나리오

### 4. 크롤링 운영 시스템
- `site_crawling_manager.py` - 사이트별 상태 관리
- `crawler_manager.py` - 크롤러 매니저

### 5. AI 분석 시스템
- `report_knowledge_system.py` - One-Pass Multi-Avatar 시스템
- `ollama_llm.py` - Ollama LLM 통합
- `ai_insights_system.py` - AI 인사이트

### 6. 통합 대시보드
- `enhanced_crawling_dashboard.py` - 향상된 대시보드 (추천)
- `run_ultimate_dashboard.py` - 최종 통합 대시보드
- `crawler_monitoring_widget.py` - 모니터링 위젯

## 🚀 빠른 시작

### 대시보드 실행
```bash
python enhanced_crawling_dashboard.py
```

### 크롤러 실행 (Ollama 사용)
```bash
python run_crawler_with_ollama.py
```

### 크롤러 실행 (기본)
```bash
python run_crawler.py
```

## 📁 주요 파일 구조

```
crawler_01/
├── crawler_38com.py              # 메인 크롤러
├── enhanced_crawling_dashboard.py # 향상된 대시보드 (추천)
├── site_crawling_manager.py      # 사이트별 관리
├── report_title_manager.py       # 보고서 제목 관리
├── time_based_strategy.py        # 시간대별 전략
├── risk_management_system.py     # 리스크 관리
├── fake_face_system.py           # 페이크 페이스
├── report_knowledge_system.py    # AI 분석 시스템
├── ollama_llm.py                 # Ollama 통합
├── ai_insights_system.py         # AI 인사이트
└── requirements.txt              # 의존성
```

## ⚙️ 주요 설정

### Ollama 설정
- 기본 모델: `llama3`
- 서버: `http://localhost:11434`
- 확인: `ollama serve` 실행 필요

### 크롤링 설정
- 기본 대기 시간: 3초
- 페이크 페이스 프로필: `casual` (기본)
- 적응형 크롤러: 활성화

### 데이터 저장
- 상태 파일: `crawling_states.json`
- 제목 파일: `report_titles.json`
- 수집 데이터: `reports/` 폴더

## 🎯 주요 기능

### 크롤링 제어
- ▶ 시작 / ⏸ 일시정지 / ▶ 이어가기 / ⏹ 정지
- 🗑 지우기 / 💾 저장하기
- ▶️ 전체 시작 / ⏸️ 전체 일시정지 / ⏹️ 전체 중지

### 보고서 관리
- 원본 제목 보존
- AI 요약 제목 자동 생성
- 파일명 자동 생성 (원본/AI 선택)
- 다중 선택 및 일괄 작업
- 검색 및 필터링

### 전략 시스템
- 시간대별 자동 전략 (새벽/아침/장중/저녁)
- 요일별 패턴 (월요일 백필, 금요일 전체 스캔)
- 리스크 레벨 자동 감지 및 대응

### AI 기능
- One-Pass Multi-Avatar 분석
- AI 인사이트 (운영/데이터 관리/데이터 활용)
- Ollama 로컬 LLM 통합

## 📊 현재 상태

### 완료된 기능
✅ 기본 크롤링 시스템
✅ 적응형 파서 및 구조 감지
✅ 페이크 페이스 시스템
✅ 시간대별 전략
✅ 리스크 관리
✅ 보고서 제목 관리
✅ AI 분석 시스템
✅ 통합 대시보드

### 선택적 추가 기능 (구현 가능)
⚠️ 병렬 처리 최적화
⚠️ 3단계 캐싱 시스템
⚠️ 데이터 계층 구조 (5단계)
⚠️ 품질 점수 시스템
⚠️ 4단계 중복 감지

## 🔧 문제 해결

### Ollama 연결 실패
```bash
# Ollama 서버 확인
ollama serve

# 모델 확인
ollama list
```

### 인코딩 오류 (Windows)
- 모든 스크립트에 `sys.stdout.reconfigure(encoding='utf-8')` 포함됨

### 대시보드 실행 오류
- PyQt5 설치 확인: `pip install PyQt5`

## 📚 참고 문서

- `ULTIMATE_SYSTEM_GUIDE.md` - 완전한 시스템 가이드
- `COMPREHENSIVE_INTEGRATION_SUMMARY.md` - 통합 요약
- `FINAL_COMPARISON_AND_INTEGRATION.md` - 비교 분석
- `system_comparison_analysis.md` - 시스템 비교

## 🎯 다음 세션에서 할 수 있는 작업

1. **실제 크롤링 테스트**
   - 실제 사이트에서 크롤링 실행
   - 데이터 수집 확인

2. **추가 기능 구현**
   - 병렬 처리 최적화
   - 캐싱 시스템
   - 품질 점수 시스템

3. **성능 최적화**
   - 크롤링 속도 개선
   - 메모리 사용 최적화

4. **데이터 분석**
   - 수집된 데이터 분석
   - 트렌드 분석

5. **시스템 확장**
   - 다른 사이트 추가
   - 새로운 기능 추가

## 💡 중요 참고사항

1. **Ollama 사용 시**: 서버가 실행 중이어야 함
2. **페이크 페이스**: 차단 방지를 위해 프로필 선택 중요
3. **시간대별 전략**: 자동으로 최적 설정 적용
4. **리스크 관리**: 자동으로 리스크 감지 및 대응
5. **데이터 저장**: 상태와 제목은 자동 저장됨

---

**마지막 업데이트**: 2025-12-30
**시스템 상태**: ✅ 모든 핵심 기능 완료




