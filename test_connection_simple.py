# test_connection_simple.py
"""
간단한 연결 테스트 스크립트

다양한 방법으로 사이트 접근을 시도합니다.
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
import ssl

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_method_1_basic():
    """기본 방법"""
    print("="*60)
    print("방법 1: 기본 requests (verify=False)")
    print("="*60)
    
    try:
        response = requests.get(
            'https://www.38.co.kr/html/fund/research_sec.html',
            verify=False,
            timeout=10
        )
        print(f"✅ 성공! Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_method_2_custom_headers():
    """커스텀 헤더"""
    print("\n" + "="*60)
    print("방법 2: 커스텀 User-Agent")
    print("="*60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(
            'https://www.38.co.kr/html/fund/research_sec.html',
            headers=headers,
            verify=False,
            timeout=10
        )
        print(f"✅ 성공! Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_method_3_session():
    """Session 사용"""
    print("\n" + "="*60)
    print("방법 3: Session 사용")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        response = session.get(
            'https://www.38.co.kr/html/fund/research_sec.html',
            verify=False,
            timeout=10
        )
        print(f"✅ 성공! Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_method_4_http_instead():
    """HTTP로 시도 (HTTPS 실패 시)"""
    print("\n" + "="*60)
    print("방법 4: HTTP로 시도")
    print("="*60)
    
    try:
        response = requests.get(
            'http://www.38.co.kr/html/fund/research_sec.html',
            timeout=10,
            allow_redirects=True
        )
        print(f"✅ 성공! Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        print(f"🔗 최종 URL: {response.url}")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_method_5_different_url():
    """다른 URL 시도"""
    print("\n" + "="*60)
    print("방법 5: 메인 페이지 접근")
    print("="*60)
    
    try:
        response = requests.get(
            'https://www.38.co.kr',
            verify=False,
            timeout=10
        )
        print(f"✅ 성공! Status: {response.status_code}")
        print(f"📄 크기: {len(response.text):,} bytes")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def main():
    """모든 방법 시도"""
    
    print("🔍 38커뮤니케이션 사이트 연결 테스트\n")
    print("여러 방법으로 접근을 시도합니다...\n")
    
    methods = [
        test_method_1_basic,
        test_method_2_custom_headers,
        test_method_3_session,
        test_method_4_http_instead,
        test_method_5_different_url
    ]
    
    results = []
    for method in methods:
        try:
            result = method()
            results.append(result)
        except Exception as e:
            print(f"⚠️  오류 발생: {e}")
            results.append(False)
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"성공: {success_count}/{total_count}")
    
    if success_count > 0:
        print("\n✅ 일부 방법으로 접근 성공!")
        print("성공한 방법을 크롤러에 적용하세요.")
    else:
        print("\n❌ 모든 방법 실패")
        print("\n가능한 원인:")
        print("1. 사이트 접근 제한 (IP 차단, 봇 감지)")
        print("2. 네트워크/방화벽 문제")
        print("3. 사이트가 현재 운영 중이 아님")
        print("4. URL 변경")
        print("\n해결 방법:")
        print("- 브라우저에서 직접 접근 확인")
        print("- 프록시 사용 고려")
        print("- Selenium 사용 고려")

if __name__ == "__main__":
    main()



