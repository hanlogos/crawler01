# test_ollama_integration.py
"""
Ollama 연동 테스트
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
from ollama_llm import OllamaLLM
from report_knowledge_system import ReportAnalysisOrchestrator, TradingAvatar, RiskAvatar, FinancialAvatar

def test_ollama_connection():
    """Ollama 연결 테스트"""
    
    print("\n" + "="*60)
    print("1. Ollama 연결 테스트")
    print("="*60)
    
    try:
        llm = OllamaLLM(model="llama3")
        
        # 사용 가능한 모델 확인
        models = llm.list_models()
        if models:
            print(f"\n사용 가능한 모델: {len(models)}개")
            for model in models[:5]:
                print(f"  - {model}")
        
        # 간단한 테스트
        print("\n간단한 테스트 프롬프트 처리 중...")
        response = llm.process("안녕하세요. 한 문장으로 답변해주세요.")
        print(f"\n응답: {response[:100]}...")
        
        return llm
        
    except Exception as e:
        print(f"\n오류: {e}")
        print("\n해결 방법:")
        print("  1. Ollama 서버 실행:")
        print("     - Windows: Ollama 앱 실행 또는 'ollama serve'")
        print("     - Linux/Mac: 'ollama serve'")
        print("  2. 모델 다운로드:")
        print("     - 'ollama pull llama3'")
        print("     - 또는 다른 모델: 'ollama pull mistral', 'ollama pull codellama'")
        return None

def test_with_report_analysis(llm):
    """보고서 분석 테스트"""
    
    print("\n" + "="*60)
    print("2. 보고서 분석 테스트 (Ollama 사용)")
    print("="*60)
    
    # 오케스트레이터 초기화
    orchestrator = ReportAnalysisOrchestrator(llm)
    
    # 아바타 등록
    orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
    orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
    orchestrator.register_avatar(FinancialAvatar("finance_1"))
    
    print(f"\n{len(orchestrator.avatars)}개 아바타 등록 완료")
    
    # 테스트 보고서 내용
    test_content = """
    삼성전자 4Q24 Preview
    
    투자의견: 매수
    목표가: 75,000원
    예상 수익률: 15%
    
    단기 전망: 4Q24 실적 호조 예상, HBM 매출 증가
    중기 전망: AI 반도체 수요 증가, 공급 부족 지속
    장기 전망: 반도체 업황 회복, 신규 수주 확대
    
    재무 지표:
    - 2024년 매출: 250조원
    - 2025년 매출 예상: 270조원
    
    리스크:
    - 하방: 메모리 가격 변동성, 경기 침체 우려
    - 상방: HBM 수요 급증, 신규 공급 계약
    
    이벤트:
    - 2025년 1월 15일: 4Q24 실적 발표
    """
    
    print("\n보고서 분석 중... (Ollama LLM 사용)")
    print("이 작업은 몇 분 정도 걸릴 수 있습니다...")
    
    try:
        result = orchestrator.process_report("TEST_OLLAMA_001", test_content)
        
        print(f"\n분석 완료!")
        print(f"  - 추출 시간: {result['extract_time']:.2f}초")
        print(f"  - 아바타 시간: {result['avatar_time']:.2f}초")
        print(f"  - 총 시간: {result['total_time']:.2f}초")
        
        # 결과 출력
        print("\n아바타 결과:")
        for res in result['avatar_results']:
            print(f"\n  {res['avatar_id']} ({res['specialty']}):")
            print(f"    {res['result']}")
        
        return True
        
    except Exception as e:
        print(f"\n분석 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Ollama 연동 테스트")
    print("="*60)
    
    # 1. Ollama 연결 테스트
    llm = test_ollama_connection()
    
    if not llm:
        print("\n" + "="*60)
        print("Ollama 서버가 실행되지 않았습니다.")
        print("="*60)
        print("\n다음 단계:")
        print("1. Ollama 서버 실행")
        print("   - Windows: Ollama 앱을 실행하거나 터미널에서 'ollama serve'")
        print("   - 또는 백그라운드에서 실행: 'start ollama serve'")
        print("\n2. 모델 다운로드 (처음 한 번만)")
        print("   - 'ollama pull llama3'")
        print("   - 또는 다른 모델: 'ollama pull mistral'")
        print("\n3. 이 스크립트 다시 실행")
        return False
    
    # 2. 보고서 분석 테스트
    print("\n" + "="*60)
    print("보고서 분석 테스트를 진행하시겠습니까?")
    print("(Ollama LLM 호출로 시간이 걸릴 수 있습니다)")
    print("="*60)
    
    try:
        success = test_with_report_analysis(llm)
        
        if success:
            print("\n" + "="*60)
            print("모든 테스트 통과!")
            print("="*60)
            print("\n이제 crawler_with_analysis.py에서 OllamaLLM을 사용할 수 있습니다.")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


