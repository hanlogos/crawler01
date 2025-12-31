# 빠른 시작 가이드

## 🚀 3분 안에 시작하기

### 1단계: 의존성 설치
```bash
pip install -r requirements.txt
```

### 2단계: Ollama 설정 (선택)
```bash
# Ollama 서버 실행
ollama serve

# 모델 다운로드 (처음 한 번만)
ollama pull llama3
```

### 3단계: 대시보드 실행
```bash
python enhanced_crawling_dashboard.py
```

## 📋 주요 명령어

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

### 테스트 실행
```bash
python test_crawler_quick.py
```

## 🎯 주요 기능 사용법

### 대시보드에서
1. **크롤링 운영 탭**: 사이트별 상태 확인 및 제어
2. **시간대별 전략 탭**: 시간대별 최적 설정 확인
3. **리스크 관리 탭**: 현재 리스크 레벨 확인
4. **AI 인사이트 탭**: 운영/관리/활용 조언 확인

### 크롤링 제어
- **▶ 시작**: 크롤링 시작
- **⏸ 일시정지**: 현재 작업 일시 중단
- **▶ 이어가기**: 일시정지된 작업 재개
- **⏹ 정지**: 크롤링 완전 중지
- **🗑 지우기**: 수집 데이터 초기화
- **💾 저장하기**: 데이터 파일로 저장

## ⚙️ 설정 파일

### config.json
```json
{
  "base_url": "http://www.38.co.kr",
  "delay": 3.0,
  "max_retries": 3,
  "days": 1,
  "max_reports": 50
}
```

## 📁 데이터 저장 위치

- 상태: `crawling_states.json`
- 제목: `report_titles.json`
- 보고서: `reports/` 폴더

## 🔧 문제 해결

### Ollama 연결 실패
```bash
ollama serve
```

### 인코딩 오류
- 이미 모든 스크립트에 포함됨

### 대시보드 실행 오류
```bash
pip install PyQt5
```

## 📚 더 자세한 정보

- `SESSION_SUMMARY.md` - 전체 세션 요약
- `ULTIMATE_SYSTEM_GUIDE.md` - 완전한 시스템 가이드




