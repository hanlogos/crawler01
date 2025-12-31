# 크롤러 테스트 가이드

## 현재 상황

38커뮤니케이션 사이트에 SSL handshake 오류가 발생하고 있습니다. 이는 다음 중 하나일 수 있습니다:

1. **사이트 접근 제한**: IP 차단 또는 봇 감지
2. **SSL/TLS 프로토콜 문제**: 사이트가 특정 SSL 버전을 요구
3. **네트워크 문제**: 방화벽 또는 프록시 설정

## 해결 방법

### 1. 사이트 접근 확인

먼저 브라우저에서 직접 접근해보세요:
- https://www.38.co.kr/html/fund/research_sec.html

접근이 안 되면:
- 사이트가 현재 운영 중인지 확인
- URL이 변경되었는지 확인

### 2. SSL 설정 개선

더 강력한 SSL 설정을 시도할 수 있습니다:

```python
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# SSL 컨텍스트 생성
ctx = create_urllib3_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 어댑터 설정
adapter = HTTPAdapter()
session = requests.Session()
session.mount('https://', adapter)
```

### 3. User-Agent 변경

더 실제 브라우저처럼 보이도록 User-Agent를 변경:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
```

### 4. 프록시 사용

회사 네트워크나 방화벽이 있다면 프록시를 사용:

```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'http://proxy.example.com:8080'
}
response = session.get(url, proxies=proxies, verify=False)
```

### 5. 대안: Selenium 사용

JavaScript가 필요한 사이트라면 Selenium을 사용:

```bash
pip install selenium
```

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get(url)
html = driver.page_source
```

## 테스트 단계

### Step 1: 기본 연결 테스트
```bash
python test_crawler_quick.py 1
```

### Step 2: 링크 추출 테스트
```bash
python test_crawler_quick.py 2
```

### Step 3: 상세 페이지 테스트
```bash
python test_crawler_quick.py 3
```

### Step 4: 전체 크롤링 테스트
```bash
python test_crawler_quick.py 4
```

## 디버깅 팁

1. **HTML 구조 분석**
   ```bash
   python analyze_38com.py
   ```
   - 실제 사이트 구조를 확인
   - HTML 파일 저장

2. **수동 테스트**
   ```python
   from crawler_38com import ThirtyEightComCrawler
   
   crawler = ThirtyEightComCrawler()
   html = crawler._fetch("https://www.38.co.kr/html/fund/research_sec.html")
   print(html[:1000] if html else "Failed")
   ```

3. **로그 확인**
   - 크롤러는 자세한 로그를 출력합니다
   - 각 단계별 성공/실패를 확인하세요

## 다음 단계

1. ✅ 사이트 접근 가능 여부 확인
2. ✅ SSL 설정 개선
3. ✅ 실제 사이트 구조 분석 (`analyze_38com.py`)
4. ✅ 크롤러 추출 로직 수정
5. ✅ 테스트 실행




