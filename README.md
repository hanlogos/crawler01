# 38커뮤니케이션 크롤러

38커뮤니케이션 사이트에서 증권 리서치 보고서를 수집하는 크롤러입니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. HTML 구조 분석 (선택사항)

크롤러를 사용하기 전에 실제 사이트 구조를 분석하여 크롤러를 최적화할 수 있습니다:

```bash
python analyze_38com.py
```

이 도구는:
- 목록 페이지의 링크 패턴 분석
- 상세 페이지의 정보 추출 패턴 분석
- HTML 파일 저장 (디버깅용)

### 3. 크롤러 테스트

```bash
python test_crawler_quick.py
```

테스트 항목:
1. 연결 테스트
2. 링크 추출 테스트
3. 상세 정보 추출 테스트
4. 전체 크롤링 테스트

### 4. 크롤러 실행

**방법 1: 설정 파일 사용 (권장)**
```bash
python run_crawler.py
```

**방법 2: 직접 실행**
```bash
python crawler_38com.py
```

## 📁 파일 구조

```
.
├── crawler_38com.py          # 메인 크롤러
├── analyze_38com.py          # HTML 구조 분석 도구
├── test_crawler_quick.py     # 테스트 스크립트
├── run_crawler.py            # 설정 파일 기반 실행 스크립트
├── config.json               # 크롤러 설정 파일
├── requirements.txt           # 의존성 패키지
└── README.md                 # 이 파일
```

## 🔧 사용법

### 기본 사용

```python
from crawler_38com import ThirtyEightComCrawler

# 크롤러 초기화
crawler = ThirtyEightComCrawler(delay=3.0)

# 최근 1일 보고서 수집
reports = crawler.crawl_recent_reports(days=1, max_reports=20)

# 결과 저장
crawler.save_to_json(reports, 'reports.json')
crawler.save_to_csv(reports, 'reports.csv')
```

### 수집된 데이터 구조

```python
@dataclass
class ReportMetadata:
    report_id: str              # 보고서 고유 ID
    title: str                  # 보고서 제목
    stock_code: str             # 종목 코드
    stock_name: str             # 종목명
    analyst_name: str           # 애널리스트 이름
    firm: str                   # 증권사
    published_date: datetime    # 발행일
    source_url: str             # 원본 URL
    investment_opinion: str      # 투자의견 (buy/sell/hold)
    target_price: str           # 목표가
```

## ⚙️ 설정

### 설정 파일 (config.json)

`config.json` 파일을 수정하여 크롤러 동작을 설정할 수 있습니다:

```json
{
  "crawler": {
    "delay": 3.0,           # 요청 간 대기 시간 (초)
    "max_retries": 3,       # 최대 재시도 횟수
    "retry_delay": 5.0,     # 재시도 대기 시간 (초)
    "timeout": 10           # 요청 타임아웃 (초)
  },
  "crawl_settings": {
    "days": 1,              # 수집할 최근 일수
    "max_reports": 100      # 최대 수집 개수
  },
  "output": {
    "json_filename": "38com_reports.json",
    "csv_filename": "38com_reports.csv"
  }
}
```

### 크롤러 옵션 (코드에서 직접 사용)

```python
crawler = ThirtyEightComCrawler(
    delay=3.0,           # 요청 간 대기 시간 (초)
    max_retries=3,       # 최대 재시도 횟수
    retry_delay=5.0      # 재시도 대기 시간 (초)
)
```

## 🐛 문제 해결

### 링크를 찾지 못하는 경우

1. `analyze_38com.py`를 실행하여 HTML 구조 확인
2. 생성된 `38com_list_page.html` 파일 확인
3. `crawler_38com.py`의 `_extract_report_links()` 메서드 수정

### 정보 추출이 실패하는 경우

1. `analyze_38com.py`로 상세 페이지 분석
2. 생성된 `38com_detail_page.html` 파일 확인
3. 각 추출 메서드(`_extract_title`, `_extract_analyst` 등) 수정

### 인코딩 오류

크롤러는 기본적으로 UTF-8 인코딩을 사용합니다. 만약 문제가 발생하면:

```python
# crawler_38com.py의 _fetch 메서드에서
response.encoding = 'euc-kr'  # 또는 필요한 인코딩
```

## ✨ 개선 사항

### v2.0 추가 기능

- ✅ **재시도 로직**: 네트워크 오류 시 자동 재시도
- ✅ **설정 파일 지원**: `config.json`으로 크롤러 설정 관리
- ✅ **진행 상황 표시**: 더 자세한 진행 상황 로그
- ✅ **에러 처리 개선**: 더 안정적인 오류 처리

## 📝 참고사항

- 크롤링 시 서버에 부하를 주지 않도록 적절한 `delay` 값을 설정하세요
- 사이트 구조가 변경되면 크롤러를 업데이트해야 할 수 있습니다
- 수집한 데이터의 사용은 해당 사이트의 이용약관을 준수하세요
- 네트워크 오류가 발생하면 자동으로 재시도합니다 (최대 3회)

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.

