# find_correct_url.py
"""
올바른 URL 찾기

38커뮤니케이션 사이트의 실제 구조를 파악합니다.
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_research_urls(base_url="http://www.38.co.kr"):
    """리서치 페이지 URL 찾기"""
    
    print("="*60)
    print("38커뮤니케이션 사이트 구조 분석")
    print("="*60)
    print()
    
    # 1. 메인 페이지 접근
    print(f"🔍 메인 페이지 접근: {base_url}")
    try:
        response = requests.get(base_url, timeout=10, allow_redirects=True)
        print(f"✅ Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        print(f"🔗 최종 URL: {response.url}\n")
        
        # HTML 저장
        with open('38com_main.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("💾 저장: 38com_main.html\n")
        
    except Exception as e:
        print(f"❌ 실패: {e}\n")
        return
    
    # 2. 링크 분석
    print("="*60)
    print("링크 분석")
    print("="*60)
    print()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    
    print(f"총 {len(links)}개 링크 발견\n")
    
    # 리서치 관련 링크 찾기
    research_keywords = ['research', 'report', '리서치', '보고서', 'fund', '증권']
    research_links = []
    
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        if any(keyword.lower() in href.lower() or keyword in text for keyword in research_keywords):
            full_url = requests.compat.urljoin(base_url, href)
            research_links.append({
                'url': full_url,
                'text': text[:50],
                'href': href
            })
    
    # 중복 제거
    seen = set()
    unique_links = []
    for link in research_links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    print(f"리서치 관련 링크: {len(unique_links)}개\n")
    
    for i, link in enumerate(unique_links[:20], 1):
        print(f"{i}. {link['text']}")
        print(f"   URL: {link['url']}")
        print(f"   원본: {link['href']}")
        print()
    
    # 3. 가능한 URL 패턴 시도
    print("="*60)
    print("가능한 URL 패턴 테스트")
    print("="*60)
    print()
    
    test_urls = [
        "http://www.38.co.kr/html/fund/research_sec.html",
        "http://www.38.co.kr/html/fund/research.html",
        "http://www.38.co.kr/html/fund/",
        "http://www.38.co.kr/fund/research_sec.html",
        "http://www.38.co.kr/research/",
        "http://www.38.co.kr/html/fund/list.html",
    ]
    
    for url in test_urls:
        try:
            test_response = requests.get(url, timeout=5, allow_redirects=True)
            status = "✅" if test_response.status_code == 200 else "⚠️"
            print(f"{status} {url}")
            print(f"   Status: {test_response.status_code}")
            if test_response.status_code == 200:
                print(f"   크기: {len(test_response.text):,} bytes")
        except Exception as e:
            print(f"❌ {url}")
            print(f"   오류: {e}")
        print()

if __name__ == "__main__":
    find_research_urls()


