# test_detail_page.py
"""상세 페이지 추출 테스트"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from crawler_38com import ThirtyEightComCrawler
from bs4 import BeautifulSoup

def test_detail_extraction():
    """상세 페이지 추출 테스트"""
    
    print("="*60)
    print("상세 페이지 추출 테스트")
    print("="*60)
    print()
    
    crawler = ThirtyEightComCrawler()
    
    # 테스트 URL
    test_url = "http://www.38.co.kr/html/news/?o=v&m=kosdaq&key=report&no=1879932&page=1"
    
    print(f"테스트 URL: {test_url}\n")
    
    # 1. HTML 가져오기
    print("1. HTML 가져오기...")
    html = crawler._fetch(test_url)
    
    if not html:
        print("❌ HTML 조회 실패")
        return
    
    print(f"✅ HTML 크기: {len(html):,} bytes\n")
    
    # HTML 저장 (분석용)
    with open('38com_detail_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("💾 저장: 38com_detail_test.html\n")
    
    # 2. 상세 정보 추출
    print("2. 상세 정보 추출...")
    report = crawler._crawl_report_detail(test_url)
    
    if report:
        print("\n✅ 추출 성공!\n")
        print(f"제목: {report.title}")
        print(f"종목: {report.stock_name} ({report.stock_code})")
        print(f"애널리스트: {report.analyst_name} ({report.firm})")
        print(f"날짜: {report.published_date.strftime('%Y-%m-%d')}")
        print(f"URL: {report.source_url}")
        
        if report.investment_opinion:
            print(f"의견: {report.investment_opinion}")
        
        if report.target_price:
            print(f"목표가: {report.target_price}")
    else:
        print("\n❌ 추출 실패")
        print("\nHTML 구조 분석 중...\n")
        
        # HTML 구조 분석
        soup = BeautifulSoup(html, 'html.parser')
        
        # 제목 찾기
        print("제목 후보:")
        for tag in ['h1', 'h2', 'h3', 'title']:
            elements = soup.find_all(tag)
            for el in elements[:3]:
                text = el.get_text(strip=True)
                if text and len(text) > 5:
                    print(f"  <{tag}>: {text[:80]}")
        
        print("\n애널리스트 후보:")
        for div in soup.find_all(['div', 'span', 'td']):
            text = div.get_text(strip=True)
            if '증권' in text and len(text) < 100:
                print(f"  {text[:80]}")
                break
        
        print("\n날짜 후보:")
        import re
        date_pattern = r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}'
        for div in soup.find_all(['div', 'span', 'td']):
            text = div.get_text(strip=True)
            if re.search(date_pattern, text):
                print(f"  {text[:80]}")
                break

if __name__ == "__main__":
    test_detail_extraction()

