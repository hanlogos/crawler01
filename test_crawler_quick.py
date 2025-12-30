# test_crawler_quick.py
"""
38커뮤니케이션 크롤러 빠른 테스트

크롤러가 제대로 작동하는지 빠르게 확인
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from crawler_38com import ThirtyEightComCrawler

def test_connection():
    """연결 테스트"""
    print("="*60)
    print("Test 1: 연결 테스트")
    print("="*60)
    
    crawler = ThirtyEightComCrawler()
    
    url = f"{crawler.REPORT_LIST_URL}research_sec.html"
    html = crawler._fetch(url)
    
    if html:
        print(f"✅ 연결 성공")
        print(f"📄 HTML 크기: {len(html):,} bytes")
        return True
    else:
        print(f"❌ 연결 실패")
        return False

def test_link_extraction():
    """링크 추출 테스트"""
    print("\n" + "="*60)
    print("Test 2: 링크 추출 테스트")
    print("="*60)
    
    crawler = ThirtyEightComCrawler()
    
    # 실제 접근 가능한 URL 시도
    test_urls = [
        "http://www.38.co.kr/html/news/?m=kosdaq&nkey=report",
        "http://www.38.co.kr/html/fund/",
        f"{crawler.REPORT_LIST_URL}research_sec.html",
    ]
    
    html = None
    url = None
    
    for test_url in test_urls:
        print(f"시도 중: {test_url}")
        html = crawler._fetch(test_url)
        if html and len(html) > 1000:
            url = test_url
            print(f"✅ 접근 성공: {url}\n")
            break
    
    if not html:
        print("❌ 모든 URL 접근 실패")
        return False
    
    links = crawler._extract_report_links(html)
    
    print(f"✅ {len(links)}개 링크 발견")
    
    if links:
        print("\n샘플 링크 (최대 5개):")
        for i, link in enumerate(links[:5], 1):
            print(f"  {i}. {link}")
        return True
    else:
        print("⚠️  링크를 찾지 못했습니다.")
        print("analyze_38com.py를 실행하여 HTML 구조를 분석하세요.")
        return False

def test_detail_extraction():
    """상세 정보 추출 테스트"""
    print("\n" + "="*60)
    print("Test 3: 상세 정보 추출 테스트")
    print("="*60)
    
    # 샘플 URL 입력
    print("\n상세 페이지 URL을 입력하세요.")
    print("(엔터만 치면 이 테스트를 건너뜁니다)")
    
    url = input("URL: ").strip()
    
    if not url:
        print("⏭️  테스트 건너뜀")
        return True
    
    crawler = ThirtyEightComCrawler()
    report = crawler._crawl_report_detail(url)
    
    if report:
        print("\n✅ 추출 성공!\n")
        print(f"제목: {report.title}")
        print(f"종목: {report.stock_name} ({report.stock_code})")
        print(f"애널리스트: {report.analyst_name} ({report.firm})")
        print(f"날짜: {report.published_date.strftime('%Y-%m-%d')}")
        
        if report.investment_opinion:
            print(f"의견: {report.investment_opinion}")
        
        if report.target_price:
            print(f"목표가: {report.target_price}")
        
        return True
    else:
        print("\n❌ 추출 실패")
        print("analyze_38com.py를 실행하여 HTML 구조를 분석하세요.")
        return False

def test_full_crawl():
    """전체 크롤링 테스트 (적은 개수)"""
    print("\n" + "="*60)
    print("Test 4: 전체 크롤링 테스트")
    print("="*60)
    
    print("\n⚠️  이 테스트는 실제로 크롤링을 수행합니다.")
    print("계속하시겠습니까? (y/n): ", end='')
    
    choice = input().strip().lower()
    
    if choice != 'y':
        print("⏭️  테스트 건너뜀")
        return True
    
    crawler = ThirtyEightComCrawler(delay=2.0)
    
    print("\n최근 1일, 최대 5개 보고서 수집 시작...")
    
    reports = crawler.crawl_recent_reports(days=1, max_reports=5)
    
    print(f"\n✅ {len(reports)}개 수집 완료\n")
    
    if reports:
        for i, report in enumerate(reports, 1):
            print(f"{i}. {report.stock_name} - {report.title[:50]}")
        
        # 저장
        crawler.save_to_json(reports, 'test_reports.json')
        print("\n💾 저장 완료: test_reports.json")
        
        return True
    else:
        print("⚠️  보고서를 수집하지 못했습니다.")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    
    print("🧪 38커뮤니케이션 크롤러 테스트 시작\n")
    
    results = []
    
    # Test 1
    results.append(("연결 테스트", test_connection()))
    
    if not results[-1][1]:
        print("\n❌ 연결 실패. 테스트 중단.")
        return
    
    # Test 2
    results.append(("링크 추출", test_link_extraction()))
    
    if not results[-1][1]:
        print("\n⚠️  링크 추출 실패. HTML 구조 분석이 필요합니다.")
        print("analyze_38com.py를 실행하세요.")
    
    # Test 3
    results.append(("상세 추출", test_detail_extraction()))
    
    # Test 4
    if results[1][1]:  # 링크 추출 성공 시에만
        results.append(("전체 크롤링", test_full_crawl()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n총 {total}개 중 {passed}개 통과 ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 크롤러가 정상 작동합니다.")
    else:
        print("\n⚠️  일부 테스트 실패. 크롤러 수정이 필요합니다.")

def main():
    """메인 함수"""
    
    if len(sys.argv) > 1:
        # 개별 테스트 실행
        test_num = sys.argv[1]
        
        if test_num == '1':
            test_connection()
        elif test_num == '2':
            test_link_extraction()
        elif test_num == '3':
            test_detail_extraction()
        elif test_num == '4':
            test_full_crawl()
        else:
            print("사용법: python test_crawler_quick.py [1-4]")
    else:
        # 모든 테스트 실행
        run_all_tests()

if __name__ == "__main__":
    main()

