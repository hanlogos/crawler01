# test_adaptive_crawler.py
"""
대응형 크롤러 테스트

사전 테스트, 차단 감지, 동적 조절 기능 테스트
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from adaptive_crawler import AdaptiveCrawler, SiteProfile
from crawler_38com import ThirtyEightComCrawler

def test_adaptive_crawler():
    """대응형 크롤러 기본 테스트"""
    
    print("="*60)
    print("대응형 크롤러 테스트")
    print("="*60)
    print()
    
    # 사이트 프로필 생성
    profile = SiteProfile(
        domain="www.38.co.kr",
        base_delay=3.0,
        min_delay=1.0,
        max_delay=10.0
    )
    
    # 대응형 크롤러 생성
    crawler = AdaptiveCrawler(profile)
    
    # 테스트 URL
    test_url = "http://www.38.co.kr/html/fund/"
    
    print(f"테스트 URL: {test_url}\n")
    
    # 1. 사전 테스트
    print("1. 사전 테스트 실행...")
    success, message = crawler.pre_test(test_url, test_requests=3)
    
    if success:
        print(f"✅ 사전 테스트 성공: {message}\n")
    else:
        print(f"❌ 사전 테스트 실패: {message}\n")
        return
    
    # 2. 실제 요청 테스트
    print("2. 실제 요청 테스트...")
    response = crawler.fetch(test_url)
    
    if response:
        print(f"✅ 요청 성공: {len(response.text):,} bytes\n")
    else:
        print("❌ 요청 실패\n")
        return
    
    # 3. 상태 확인
    print("3. 크롤러 상태:")
    status = crawler.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()
    
    # 4. 프로필 저장
    crawler.save_profile()
    print("💾 프로필 저장 완료\n")

def test_integrated_crawler():
    """통합 크롤러 테스트 (대응형 크롤러 포함)"""
    
    print("="*60)
    print("통합 크롤러 테스트 (대응형 크롤러 활성화)")
    print("="*60)
    print()
    
    # 대응형 크롤러 활성화하여 크롤러 생성
    crawler = ThirtyEightComCrawler(
        delay=3.0,
        use_adaptive=True,
        site_domain="www.38.co.kr"
    )
    
    # 사전 테스트
    print("사전 연결 테스트...")
    success, message = crawler.pre_test_connection()
    
    if success:
        print(f"✅ 사전 테스트 성공: {message}\n")
    else:
        print(f"⚠️  사전 테스트 경고: {message}\n")
    
    # 실제 크롤링 테스트
    print("링크 추출 테스트...")
    test_url = "http://www.38.co.kr/html/news/?m=kosdaq&nkey=report"
    html = crawler._fetch(test_url)
    
    if html:
        links = crawler._extract_report_links(html)
        print(f"✅ {len(links)}개 링크 발견\n")
        
        # 상태 확인
        status = crawler.get_crawler_status()
        if status:
            print("크롤러 상태:")
            for key, value in status.items():
                print(f"   {key}: {value}")
    else:
        print("❌ HTML 조회 실패\n")

def test_block_detection():
    """차단 감지 테스트"""
    
    print("="*60)
    print("차단 감지 테스트")
    print("="*60)
    print()
    
    profile = SiteProfile(domain="test.com")
    crawler = AdaptiveCrawler(profile)
    
    # 정상 요청
    print("1. 정상 요청 테스트...")
    response = crawler.fetch("http://www.38.co.kr/html/fund/")
    
    if response:
        print("✅ 정상 요청 성공\n")
    else:
        print("❌ 요청 실패\n")
    
    # 상태 확인
    status = crawler.get_status()
    print("크롤러 상태:")
    print(f"   성공률: {status['success_rate']:.1%}")
    print(f"   평균 응답 시간: {status['avg_response_time']:.2f}초")
    print(f"   현재 지연 시간: {status['current_delay']:.2f}초")
    print(f"   건강 상태: {'✅ 양호' if status['is_healthy'] else '⚠️ 주의'}")

def main():
    """메인 함수"""
    
    print("🧪 대응형 크롤러 테스트 시작\n")
    
    try:
        # 테스트 1: 대응형 크롤러 기본 테스트
        test_adaptive_crawler()
        
        print("\n" + "="*60 + "\n")
        
        # 테스트 2: 통합 크롤러 테스트
        test_integrated_crawler()
        
        print("\n" + "="*60 + "\n")
        
        # 테스트 3: 차단 감지 테스트
        test_block_detection()
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


