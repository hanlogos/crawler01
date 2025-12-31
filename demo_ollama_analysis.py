# demo_ollama_analysis.py
"""
Ollama 분석 시스템 데모

실제 보고서 내용으로 분석 시연
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import logging
from report_knowledge_system import (
    ReportAnalysisOrchestrator,
    TradingAvatar,
    RiskAvatar,
    FinancialAvatar
)
from ollama_llm import OllamaLLM

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Ollama 분석 시스템 데모")
    print("="*60)
    print()
    
    # Ollama LLM 초기화
    print("1. Ollama LLM 초기화...")
    try:
        llm = OllamaLLM(model="llama3")
        print("✅ Ollama LLM 초기화 완료\n")
    except Exception as e:
        print(f"❌ Ollama 초기화 실패: {e}")
        return
    
    # 오케스트레이터 초기화
    print("2. 분석 오케스트레이터 초기화...")
    orchestrator = ReportAnalysisOrchestrator(llm)
    
    # 아바타 등록
    orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
    orchestrator.register_avatar(TradingAvatar("trader_medium", "medium"))
    orchestrator.register_avatar(TradingAvatar("trader_long", "long"))
    orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
    orchestrator.register_avatar(RiskAvatar("risk_upside", "upside"))
    orchestrator.register_avatar(FinancialAvatar("finance_1"))
    
    print(f"✅ {len(orchestrator.avatars)}개 아바타 등록 완료\n")
    
    # 실제 보고서 내용 (샘플)
    report_content = """
    삼성전자 4Q24 Preview 및 2025년 전망
    
    투자의견: 매수 (BUY)
    목표가: 75,000원
    현재가 대비 예상 수익률: 15.5%
    
    [요약]
    삼성전자는 4Q24 실적 호조가 예상되며, HBM(High Bandwidth Memory) 매출 본격화와 
    AI 반도체 수요 증가로 2025년에도 강한 성장세를 이어갈 것으로 전망됩니다.
    
    [단기 전망 (1-3개월)]
    - 4Q24 실적 호조 예상: HBM3E 양산 본격화로 메모리 사업부 수익성 개선
    - AI 서버용 메모리 수요 급증으로 가격 상승세 지속
    - 신규 고객사와의 공급 계약 체결로 안정적 수주 확보
    
    [중기 전망 (3-12개월)]
    - AI 반도체 시장 성장에 따른 수혜 지속
    - GAA(Gate-All-Around) 공정 기술 경쟁력 강화
    - 모바일 AP 시장 점유율 회복 노력
    
    [장기 전망 (1년 이상)]
    - 반도체 업황 회복세 지속
    - 신규 공급 계약 확대로 안정적 성장 기반 마련
    - 차세대 메모리 기술 선도 지위 유지
    
    [재무 지표]
    2024년 예상:
    - 매출: 250조원
    - 영업이익: 35조원
    - 영업이익률: 14.0%
    
    2025년 예상:
    - 매출: 270조원 (전년 대비 +8.0%)
    - 영업이익: 40조원 (전년 대비 +14.3%)
    - 영업이익률: 14.8%
    
    [리스크 분석]
    하방 리스크:
    1. 메모리 가격 변동성: 글로벌 경기 침체 시 메모리 가격 하락 가능성 (영향도: 높음, 확률: 중간)
    2. 경쟁 심화: 중국 반도체 기업의 기술 추격 (영향도: 중간, 확률: 높음)
    3. 환율 변동: 원화 강세 시 수출 경쟁력 저하 (영향도: 중간, 확률: 중간)
    
    상방 리스크:
    1. HBM 수요 급증: AI 서버 시장 성장으로 HBM 수요 예상보다 빠르게 증가 (영향도: 높음, 확률: 높음)
    2. 신규 공급 계약: 주요 고객사와의 장기 공급 계약 체결 (영향도: 높음, 확률: 중간)
    3. 공정 기술 선도: GAA 공정 기술로 경쟁력 강화 (영향도: 높음, 확률: 높음)
    
    [시장 심리]
    - 전체적 심리: 강세 (Bullish)
    - 신뢰도: 85%
    - 주요 요인: 실적 개선, 신규 수주, AI 반도체 수혜
    
    [주요 이벤트]
    - 2025년 1월 15일: 4Q24 실적 발표 (영향도: 높음)
    - 2025년 2월: 신규 HBM 공급 계약 발표 예상 (영향도: 중간)
    - 2025년 상반기: 차세대 공정 기술 공개 예상 (영향도: 높음)
    
    [섹터 정보]
    - 업종: 반도체
    - 주요 테마: AI, HBM, 메모리 반도체
    - 주요 경쟁사: SK하이닉스, 마이크론, 삼성전자 DS부문
    
    [기술 정보]
    - 핵심 기술: HBM3E, GAA 공정, 3nm 공정
    - 경쟁 우위: 공정 기술, 생산 능력, 고객 관계
    
    [밸류에이션]
    - 공정 가치: 80,000원
    - 평가 방법: DCF (Discounted Cash Flow)
    - 현재가 대비 할인율: 6.7%
    """
    
    # 분석 수행
    print("="*60)
    print("3. 보고서 분석 시작")
    print("="*60)
    print()
    print("⚠️  Ollama LLM을 사용하여 분석 중입니다...")
    print("   (약 10-20초 소요 예상)")
    print()
    
    try:
        result = orchestrator.process_report("DEMO_001", report_content)
        
        # 결과 출력
        print("\n" + "="*60)
        print("분석 결과")
        print("="*60)
        print()
        print(f"보고서 ID: {result['report_id']}")
        print(f"추출 시간: {result['extract_time']:.2f}초")
        print(f"아바타 분석 시간: {result['avatar_time']:.2f}초")
        print(f"총 소요 시간: {result['total_time']:.2f}초")
        print()
        
        # 지식 정보
        if 'knowledge' in result:
            knowledge = result['knowledge']
            print("="*60)
            print("추출된 지식 정보")
            print("="*60)
            print(f"종목: {knowledge.stock_name} ({knowledge.stock_code})")
            print(f"애널리스트: {knowledge.analyst} ({knowledge.firm})")
            print(f"투자의견: {knowledge.investment_opinion}")
            print(f"목표가: {knowledge.target_price:,}원" if knowledge.target_price else "목표가: 없음")
            print()
        
        # 아바타 결과
        print("="*60)
        print("아바타 분석 결과")
        print("="*60)
        print()
        
        for res in result['avatar_results']:
            avatar_id = res['avatar_id']
            specialty = res['specialty']
            result_data = res['result']
            
            print(f"[{avatar_id}] {specialty}")
            
            if specialty == 'trading_signals':
                decision = result_data.get('decision', 'UNKNOWN')
                confidence = result_data.get('confidence', 0)
                timeframe = result_data.get('timeframe', '')
                print(f"  결정: {decision}")
                print(f"  신뢰도: {confidence:.1%}")
                print(f"  기간: {timeframe}")
                if 'signals' in result_data and result_data['signals']:
                    signal = result_data['signals'][0]
                    print(f"  이유: {signal.get('reason', 'N/A')}")
            
            elif specialty == 'risks':
                risk_level = result_data.get('risk_level', 'UNKNOWN')
                count = result_data.get('count', 0)
                high_count = result_data.get('high_count', 0)
                focus = result_data.get('focus', '')
                print(f"  위험 수준: {risk_level}")
                print(f"  {focus} 리스크: {count}개 (고위험: {high_count}개)")
                if 'risks' in result_data and result_data['risks']:
                    risk = result_data['risks'][0]
                    print(f"  주요 리스크: {risk.get('description', 'N/A')}")
            
            elif specialty == 'financial_metrics':
                assessment = result_data.get('assessment', 'UNKNOWN')
                growth_rate = result_data.get('growth_rate', 0)
                revenue_2024 = result_data.get('revenue_2024', 0)
                revenue_2025 = result_data.get('revenue_2025', 0)
                print(f"  평가: {assessment}")
                print(f"  성장률: {growth_rate:.1%}")
                print(f"  2024년 매출: {revenue_2024/1e12:.1f}조원")
                print(f"  2025년 매출: {revenue_2025/1e12:.1f}조원")
            
            print()
        
        print("="*60)
        print("✅ 분석 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()



