# run_crawler.py
"""
38커뮤니케이션 크롤러 실행 스크립트

설정 파일을 읽어서 크롤러를 실행합니다.
"""

import json
import sys
from pathlib import Path
from crawler_38com import ThirtyEightComCrawler

def load_config(config_path: str = "config.json") -> dict:
    """설정 파일 로드"""
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"⚠️  설정 파일이 없습니다: {config_path}")
        print("기본 설정을 사용합니다.")
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        print("기본 설정을 사용합니다.")
        return {}

def main():
    """메인 함수"""
    
    print("🚀 38커뮤니케이션 크롤러 시작\n")
    
    # 설정 로드
    config = load_config()
    
    crawler_config = config.get('crawler', {})
    crawl_settings = config.get('crawl_settings', {})
    output_config = config.get('output', {})
    
    # 크롤러 초기화
    crawler = ThirtyEightComCrawler(
        delay=crawler_config.get('delay', 3.0),
        max_retries=crawler_config.get('max_retries', 3),
        retry_delay=crawler_config.get('retry_delay', 5.0)
    )
    
    # 크롤링 실행
    days = crawl_settings.get('days', 1)
    max_reports = crawl_settings.get('max_reports', 100)
    
    print(f"📊 설정:")
    print(f"   - 최근 {days}일")
    print(f"   - 최대 {max_reports}개")
    print(f"   - 요청 간격: {crawler_config.get('delay', 3.0)}초")
    print()
    
    reports = crawler.crawl_recent_reports(
        days=days,
        max_reports=max_reports
    )
    
    # 결과 출력
    print(f"\n📊 수집 결과: {len(reports)}개\n")
    
    if reports:
        for i, report in enumerate(reports, 1):
            print(f"{i}. {report.stock_name} ({report.stock_code})")
            print(f"   제목: {report.title[:60]}...")
            print(f"   애널리스트: {report.analyst_name} ({report.firm})")
            print(f"   날짜: {report.published_date.strftime('%Y-%m-%d')}")
            
            if report.investment_opinion:
                print(f"   의견: {report.investment_opinion}")
            
            if report.target_price:
                print(f"   목표가: {report.target_price}")
            
            print()
        
        # 저장
        json_file = output_config.get('json_filename', '38com_reports.json')
        csv_file = output_config.get('csv_filename', '38com_reports.csv')
        
        crawler.save_to_json(reports, json_file)
        crawler.save_to_csv(reports, csv_file)
        
        print(f"✅ 완료! 결과가 저장되었습니다:")
        print(f"   - {json_file}")
        print(f"   - {csv_file}")
    else:
        print("⚠️  수집된 보고서가 없습니다.")
        print("\n가능한 원인:")
        print("1. 최근 보고서가 없음")
        print("2. 사이트 구조 변경 (analyze_38com.py로 확인)")
        print("3. 네트워크 오류")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


