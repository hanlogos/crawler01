# test_integrated_crawler.py
"""
통합 크롤러 테스트 (간단 버전)
"""

import sys
import io
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # 이미 설정되어 있거나 실패한 경우

from crawler_with_analysis import IntegratedCrawler
from report_knowledge_system import MockLLM

def test_integration():
    """통합 테스트"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🧪 통합 크롤러 테스트")
    print("="*60)
    print()
    
    # 통합 크롤러 초기화
    print("1. 통합 크롤러 초기화...")
    integrated = IntegratedCrawler(
        use_analysis=True,
        crawler_delay=2.0,  # 테스트용 짧은 지연
        use_adaptive=True
    )
    print("✅ 초기화 완료")
    print(f"   - 아바타 수: {len(integrated.orchestrator.avatars)}개")
    print()
    
    # 작은 규모로 테스트 (1개만)
    print("2. 크롤링 + 분석 테스트 (1개 보고서)...")
    print("   ⚠️  실제 크롤링은 시간이 걸릴 수 있습니다.")
    print()
    
    try:
        results = integrated.crawl_and_analyze(
            days=1,
            max_reports=1,  # 테스트용 1개만
            extract_content=True
        )
        
        print("\n✅ 테스트 완료!")
        print(f"\n📊 결과:")
        print(f"   - 수집: {results['summary']['total_reports']}개")
        print(f"   - 분석: {results['summary']['analyzed']}개")
        print(f"   - 실패: {results['summary']['failed']}개")
        
        # 분석 결과 확인
        if results['analysis_results']:
            for res in results['analysis_results']:
                if res['status'] == 'success':
                    result = res['result']
                    print(f"\n   📄 보고서 분석 결과:")
                    print(f"      - ID: {result['report_id']}")
                    print(f"      - 추출 시간: {result['extract_time']:.2f}초")
                    print(f"      - 아바타 시간: {result['avatar_time']:.2f}초")
                    print(f"      - 아바타 수: {len(result['avatar_results'])}개")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_crawling():
    """크롤링 없이 분석 시스템만 테스트"""
    
    print("\n" + "="*60)
    print("🧪 분석 시스템 단독 테스트")
    print("="*60)
    print()
    
    from report_knowledge_system import ReportAnalysisOrchestrator, MockLLM
    
    # 오케스트레이터 초기화
    orchestrator = ReportAnalysisOrchestrator(MockLLM())
    
    # 아바타 등록
    from report_knowledge_system import TradingAvatar, RiskAvatar, FinancialAvatar
    
    orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
    orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
    orchestrator.register_avatar(FinancialAvatar("finance_1"))
    
    print(f"✅ {len(orchestrator.avatars)}개 아바타 등록")
    
    # 테스트 보고서 내용
    test_content = """
    삼성전자 4Q24 Preview
    
    투자의견: 매수
    목표가: 75,000원
    
    단기 전망: 4Q24 실적 호조 예상
    중기 전망: HBM 매출 본격화
    장기 전망: AI 반도체 수혜
    
    리스크: 메모리 업황 변동성
    """
    
    # 분석 수행
    print("\n📄 보고서 분석 중...")
    result = orchestrator.process_report("TEST_001", test_content)
    
    print(f"\n✅ 분석 완료!")
    print(f"   - 추출 시간: {result['extract_time']:.2f}초")
    print(f"   - 아바타 시간: {result['avatar_time']:.2f}초")
    print(f"   - 총 시간: {result['total_time']:.2f}초")
    
    # 결과 출력
    print("\n📋 아바타 결과:")
    for res in result['avatar_results']:
        print(f"   - {res['avatar_id']}: {res['result']}")
    
    return True

def main():
    """메인 함수"""
    
    print("\n" + "="*60)
    print("🚀 통합 크롤러 테스트 스위트")
    print("="*60)
    
    # 테스트 1: 분석 시스템 단독 테스트 (빠름)
    print("\n[테스트 1] 분석 시스템 단독 테스트")
    success1 = test_without_crawling()
    
    # 테스트 2: 통합 테스트 (실제 크롤링, 느림)
    print("\n" + "="*60)
    print("[테스트 2] 통합 크롤러 테스트 (실제 크롤링)")
    print("="*60)
    print("\n⚠️  실제 크롤링은 시간이 걸립니다.")
    print("   건너뛰려면 Ctrl+C를 누르세요.\n")
    
    try:
        success2 = test_integration()
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
        success2 = None
    
    # 최종 결과
    print("\n" + "="*60)
    print("📊 테스트 결과")
    print("="*60)
    print(f"  분석 시스템: {'✅ 통과' if success1 else '❌ 실패'}")
    if success2 is not None:
        print(f"  통합 크롤러: {'✅ 통과' if success2 else '❌ 실패'}")
    else:
        print(f"  통합 크롤러: ⏭️  건너뜀")
    
    return success1 and (success2 is None or success2)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

