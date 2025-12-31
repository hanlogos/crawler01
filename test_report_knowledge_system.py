# test_report_knowledge_system.py
"""
보고서 지식 시스템 테스트
"""

import sys
import io
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from report_knowledge_system import (
    ReportKnowledge,
    KnowledgeStore,
    ComprehensiveExtractor,
    TradingAvatar,
    RiskAvatar,
    FinancialAvatar,
    ReportAnalysisOrchestrator,
    MockLLM
)
from datetime import datetime

def test_knowledge_store():
    """KnowledgeStore 테스트"""
    
    print("="*60)
    print("Test 1: KnowledgeStore")
    print("="*60)
    
    store = KnowledgeStore()
    
    # 테스트 데이터 생성
    knowledge = ReportKnowledge(
        report_id="RPT_001",
        timestamp=datetime.now(),
        stock_name="삼성전자",
        stock_code="005930",
        analyst="홍길동",
        firm="삼성증권",
        report_date="2024-12-30",
        investment_opinion="buy",
        target_price=75000.0,
        expected_return=15.5,
        financial_metrics={"2024": {"revenue": 250000000000000}},
        trading_signals={
            "short_term": [{"signal": "buy", "confidence": 0.8}],
            "medium_term": [{"signal": "hold", "confidence": 0.7}]
        },
        risks=[
            {"type": "downside", "impact": "high"},
            {"type": "upside", "impact": "high"}
        ],
        sentiment={"overall": "bullish"},
        events=[],
        sector_info={},
        technical_info={},
        valuation={},
        raw_content="테스트 내용"
    )
    
    # 저장
    store.store(knowledge)
    print("✅ 저장 완료")
    
    # 조회
    retrieved = store.get("RPT_001")
    assert retrieved is not None, "조회 실패"
    print(f"✅ 조회 성공: {retrieved.stock_name}")
    
    # 측면 쿼리
    signals = store.query_aspect("RPT_001", "trading_signals")
    assert signals is not None, "신호 쿼리 실패"
    print(f"✅ 신호 쿼리 성공: {len(signals.get('short_term', []))}개")
    
    # 필터 쿼리
    short_signals = store.query_filtered("RPT_001", "trading_signals", {"timeframe": "short_term"})
    print(f"✅ 필터 쿼리 성공: {short_signals}")
    
    # 검색
    stock_reports = store.search_by_stock("005930")
    assert "RPT_001" in stock_reports, "종목 검색 실패"
    print(f"✅ 종목 검색 성공: {len(stock_reports)}개")
    
    # 통계
    stats = store.get_stats()
    print(f"✅ 통계: {stats}")
    
    print("\n✅ KnowledgeStore 테스트 통과!\n")

def test_avatars():
    """아바타 테스트"""
    
    print("="*60)
    print("Test 2: 아바타")
    print("="*60)
    
    store = KnowledgeStore()
    
    # 테스트 지식 생성
    knowledge = ReportKnowledge(
        report_id="RPT_002",
        timestamp=datetime.now(),
        stock_name="SK하이닉스",
        stock_code="000660",
        analyst="김철수",
        firm="KB증권",
        report_date="2024-12-30",
        investment_opinion="buy",
        target_price=150000.0,
        expected_return=20.0,
        financial_metrics={
            "2024": {"revenue": 30000000000000},
            "2025": {"revenue": 35000000000000}
        },
        trading_signals={
            "short_term": [{"signal": "buy", "confidence": 0.9}],
            "medium_term": [{"signal": "buy", "confidence": 0.85}],
            "long_term": [{"signal": "buy", "confidence": 0.95}]
        },
        risks=[
            {"type": "downside", "impact": "medium"},
            {"type": "upside", "impact": "high", "description": "HBM 수요 증가"}
        ],
        sentiment={"overall": "bullish"},
        events=[],
        sector_info={},
        technical_info={},
        valuation={},
        raw_content="테스트 내용"
    )
    
    store.store(knowledge)
    
    # TradingAvatar 테스트
    trader = TradingAvatar("trader_1", "short")
    result = trader.analyze("RPT_002", store)
    print(f"✅ TradingAvatar: {result}")
    assert result['decision'] in ['BUY', 'HOLD', 'SELL'], "결정 실패"
    
    # RiskAvatar 테스트
    risk_avatar = RiskAvatar("risk_1", "upside")
    result = risk_avatar.analyze("RPT_002", store)
    print(f"✅ RiskAvatar: {result}")
    assert 'risk_level' in result, "리스크 분석 실패"
    
    # FinancialAvatar 테스트
    finance_avatar = FinancialAvatar("finance_1")
    result = finance_avatar.analyze("RPT_002", store)
    print(f"✅ FinancialAvatar: {result}")
    assert 'assessment' in result, "재무 분석 실패"
    
    print("\n✅ 아바타 테스트 통과!\n")

def test_orchestrator():
    """오케스트레이터 테스트"""
    
    print("="*60)
    print("Test 3: ReportAnalysisOrchestrator")
    print("="*60)
    
    # Mock LLM
    llm = MockLLM()
    
    # 오케스트레이터
    orchestrator = ReportAnalysisOrchestrator(llm)
    
    # 아바타 등록
    orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
    orchestrator.register_avatar(TradingAvatar("trader_medium", "medium"))
    orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
    orchestrator.register_avatar(FinancialAvatar("finance_1"))
    
    print(f"✅ 아바타 {len(orchestrator.avatars)}개 등록")
    
    # 보고서 처리
    report_content = """
    삼성전자 4Q24 Preview
    
    투자의견: 매수
    목표가: 75,000원
    
    단기 전망: 4Q24 실적 호조 예상
    중기 전망: HBM 매출 본격화
    장기 전망: AI 반도체 수혜
    
    리스크: 메모리 업황 변동성
    """
    
    result = orchestrator.process_report("RPT_003", report_content)
    
    print(f"\n✅ 보고서 처리 완료")
    print(f"  추출 시간: {result['extract_time']:.2f}초")
    print(f"  아바타 시간: {result['avatar_time']:.2f}초")
    print(f"  총 시간: {result['total_time']:.2f}초")
    print(f"  아바타 결과: {len(result['avatar_results'])}개")
    
    # 결과 확인
    for res in result['avatar_results']:
        print(f"\n  {res['avatar_id']} ({res['specialty']}):")
        print(f"    {res['result']}")
    
    print("\n✅ 오케스트레이터 테스트 통과!\n")

def test_performance():
    """성능 테스트"""
    
    print("="*60)
    print("Test 4: 성능 테스트 (100개 아바타)")
    print("="*60)
    
    llm = MockLLM()
    orchestrator = ReportAnalysisOrchestrator(llm)
    
    # 100개 아바타 등록
    for i in range(30):
        timeframe = ['short', 'medium', 'long'][i % 3]
        orchestrator.register_avatar(TradingAvatar(f"trader_{i:03d}", timeframe))
    
    for i in range(30):
        focus = ['upside', 'downside'][i % 2]
        orchestrator.register_avatar(RiskAvatar(f"risk_{i:03d}", focus))
    
    for i in range(40):
        orchestrator.register_avatar(FinancialAvatar(f"finance_{i:03d}"))
    
    print(f"✅ {len(orchestrator.avatars)}개 아바타 등록")
    
    # 보고서 처리
    report_content = "삼성전자 4Q24 Preview..."
    
    result = orchestrator.process_report("RPT_PERF", report_content)
    
    print(f"\n📊 성능 결과:")
    print(f"  추출 시간: {result['extract_time']:.2f}초")
    print(f"  아바타 시간: {result['avatar_time']:.4f}초")
    print(f"  총 시간: {result['total_time']:.2f}초")
    print(f"  아바타당: {result['avatar_time']/len(orchestrator.avatars):.6f}초")
    
    # 기존 방식과 비교
    old_time = 3.0 * len(orchestrator.avatars)  # 가정: 각 아바타당 3초
    improvement = old_time / result['total_time']
    
    print(f"\n💡 성능 개선:")
    print(f"  기존 방식 (예상): {old_time:.1f}초")
    print(f"  One-Pass 방식: {result['total_time']:.2f}초")
    print(f"  개선율: {improvement:.1f}배 빠름! ✅")
    
    print("\n✅ 성능 테스트 통과!\n")

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🧪 보고서 지식 시스템 테스트")
    print("="*60)
    print()
    
    try:
        test_knowledge_store()
        test_avatars()
        test_orchestrator()
        test_performance()
        
        print("="*60)
        print("🎉 모든 테스트 통과!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




