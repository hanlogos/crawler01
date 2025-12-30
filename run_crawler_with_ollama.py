# run_crawler_with_ollama.py
"""
Ollama를 사용한 통합 크롤러 실행

사용법:
    python run_crawler_with_ollama.py
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
from crawler_with_analysis import IntegratedCrawler

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Ollama를 사용한 통합 크롤러")
    print("="*60)
    print()
    
    # Ollama 서버 확인
    try:
        from ollama_llm import OllamaLLM
        test_llm = OllamaLLM(model="llama3")
        models = test_llm.list_models()
        
        if models:
            print(f"✅ Ollama 서버 연결 성공")
            print(f"   사용 가능한 모델: {', '.join(models[:3])}")
            print()
        else:
            print("⚠️  Ollama 서버는 실행 중이지만 모델이 없습니다.")
            print("   모델 다운로드: 'ollama pull llama3'")
            print()
            return
            
    except Exception as e:
        print(f"❌ Ollama 서버 연결 실패: {e}")
        print()
        print("다음 단계:")
        print("1. Ollama 서버 실행:")
        print("   - Windows: Ollama 앱 실행 또는 'ollama serve'")
        print("   - 또는 백그라운드: 'start ollama serve'")
        print()
        print("2. 모델 다운로드 (처음 한 번만):")
        print("   - 'ollama pull llama3'")
        print("   - 또는 다른 모델: 'ollama pull mistral'")
        print()
        return
    
    # 통합 크롤러 초기화 (Ollama 사용)
    print("통합 크롤러 초기화 중...")
    integrated = IntegratedCrawler(
        use_analysis=True,
        crawler_delay=3.0,
        use_adaptive=True,
        use_ollama=True,  # Ollama 사용
        ollama_model="llama3"  # 사용할 모델
    )
    
    print("✅ 초기화 완료\n")
    
    # 크롤링 + 분석
    print("="*60)
    print("크롤링 + 분석 시작")
    print("="*60)
    print()
    print("⚠️  Ollama LLM 사용으로 인해 각 보고서 분석에 시간이 걸릴 수 있습니다.")
    print("   (보고서당 약 10-30초 소요 예상)")
    print()
    
    try:
        results = integrated.crawl_and_analyze(
            days=7,  # 최근 7일로 확대
            max_reports=5,  # 최대 5개
            extract_content=True
        )
        
        # 결과 저장
        integrated.save_results(results)
        
        # 결과 출력
        print("\n" + "="*60)
        print("최종 결과")
        print("="*60)
        print(f"수집: {results['summary']['total_reports']}개")
        print(f"분석: {results['summary']['analyzed']}개")
        print(f"실패: {results['summary']['failed']}개")
        
        # 분석 결과 샘플
        if results['analysis_results']:
            print("\n분석 결과 샘플:")
            for res in results['analysis_results'][:2]:
                if res['status'] == 'success':
                    result = res['result']
                    print(f"\n  보고서 ID: {result['report_id']}")
                    print(f"  추출 시간: {result['extract_time']:.2f}초")
                    print(f"  아바타 시간: {result['avatar_time']:.2f}초")
                    print(f"  아바타 결과: {len(result['avatar_results'])}개")
        
        print("\n✅ 완료!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

