# crawler_with_analysis.py
"""
크롤러 + 분석 시스템 통합

크롤링과 동시에 보고서 분석 수행
"""

import sys
import io
import logging
from typing import List, Optional
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from crawler_38com import ThirtyEightComCrawler, ReportMetadata
from report_knowledge_system import (
    ReportAnalysisOrchestrator,
    TradingAvatar,
    RiskAvatar,
    FinancialAvatar,
    MockLLM
)

# Ollama LLM 임포트 (선택적)
try:
    from ollama_llm import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    OllamaLLM = None

class IntegratedCrawler:
    """통합 크롤러 (크롤링 + 분석)"""
    
    def __init__(
        self,
        use_analysis: bool = True,
        llm_processor = None,
        crawler_delay: float = 3.0,
        use_adaptive: bool = True,
        use_ollama: bool = False,
        ollama_model: str = "llama3"
    ):
        """
        초기화
        
        Args:
            use_analysis: 분석 시스템 사용 여부
            llm_processor: LLM 프로세서 (None이면 MockLLM 또는 OllamaLLM 사용)
            crawler_delay: 크롤러 지연 시간
            use_adaptive: 대응형 크롤러 사용 여부
            use_ollama: Ollama LLM 사용 여부 (llm_processor가 None일 때)
            ollama_model: Ollama 모델 이름 (llama3, mistral 등)
        """
        self.use_analysis = use_analysis
        self.logger = logging.getLogger(__name__)
        
        # 크롤러 초기화
        self.crawler = ThirtyEightComCrawler(
            delay=crawler_delay,
            use_adaptive=use_adaptive
        )
        
        # 분석 시스템 초기화
        if self.use_analysis:
            if llm_processor is None:
                # Ollama 사용 옵션
                if use_ollama and OLLAMA_AVAILABLE:
                    try:
                        llm_processor = OllamaLLM(model=ollama_model)
                        self.logger.info(f"✅ Ollama LLM 초기화 완료 (모델: {ollama_model})")
                    except Exception as e:
                        self.logger.warning(f"⚠️  Ollama 초기화 실패: {e}")
                        self.logger.info("   MockLLM으로 대체합니다.")
                        llm_processor = MockLLM()
                else:
                    llm_processor = MockLLM()
                    if use_ollama and not OLLAMA_AVAILABLE:
                        self.logger.warning("⚠️  Ollama를 사용하려고 했지만 ollama_llm.py를 찾을 수 없습니다.")
            
            self.orchestrator = ReportAnalysisOrchestrator(llm_processor)
            self._setup_avatars()
            self.logger.info("✅ 분석 시스템 초기화 완료")
        else:
            self.orchestrator = None
    
    def _setup_avatars(self):
        """기본 아바타 설정"""
        
        # Trading Avatars
        self.orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
        self.orchestrator.register_avatar(TradingAvatar("trader_medium", "medium"))
        self.orchestrator.register_avatar(TradingAvatar("trader_long", "long"))
        
        # Risk Avatars
        self.orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
        self.orchestrator.register_avatar(RiskAvatar("risk_upside", "upside"))
        
        # Financial Avatar
        self.orchestrator.register_avatar(FinancialAvatar("finance_1"))
        
        self.logger.info(f"✅ {len(self.orchestrator.avatars)}개 아바타 등록")
    
    def crawl_and_analyze(
        self,
        days: int = 1,
        max_reports: int = 10,
        extract_content: bool = True
    ) -> dict:
        """
        크롤링 + 분석 수행
        
        Args:
            days: 최근 N일
            max_reports: 최대 수집 개수
            extract_content: 상세 내용 추출 여부 (분석에 필요)
        
        Returns:
            {
                'reports': [...],  # ReportMetadata 리스트
                'analysis_results': [...],  # 분석 결과 리스트
                'summary': {...}  # 요약 통계
            }
        """
        
        self.logger.info("="*60)
        self.logger.info("🚀 통합 크롤링 시작")
        self.logger.info("="*60)
        
        # 1. 크롤링
        self.logger.info(f"\n📊 1단계: 보고서 크롤링 (최근 {days}일)")
        reports = self.crawler.crawl_recent_reports(
            days=days,
            max_reports=max_reports
        )
        
        self.logger.info(f"✅ {len(reports)}개 보고서 수집 완료")
        
        if not reports:
            return {
                'reports': [],
                'analysis_results': [],
                'summary': {
                    'total_reports': 0,
                    'analyzed': 0,
                    'failed': 0
                }
            }
        
        # 2. 분석 (옵션)
        analysis_results = []
        
        if self.use_analysis and extract_content:
            self.logger.info(f"\n🤖 2단계: 보고서 분석 ({len(reports)}개)")
            
            for i, report in enumerate(reports, 1):
                self.logger.info(f"\n[{i}/{len(reports)}] {report.stock_name} - {report.title[:50]}...")
                
                try:
                    # 상세 내용 추출
                    report_content = self._extract_report_content(report)
                    
                    if not report_content:
                        self.logger.warning(f"⚠️  내용 추출 실패: {report.report_id}")
                        analysis_results.append({
                            'report_id': report.report_id,
                            'status': 'failed',
                            'error': '내용 추출 실패'
                        })
                        continue
                    
                    # 분석 수행
                    result = self.orchestrator.process_report(
                        report_id=report.report_id,
                        report_content=report_content
                    )
                    
                    analysis_results.append({
                        'report_id': report.report_id,
                        'status': 'success',
                        'result': result
                    })
                    
                    self.logger.info(f"✅ 분석 완료: {result['total_time']:.2f}초")
                    
                except Exception as e:
                    self.logger.error(f"❌ 분석 실패: {e}")
                    analysis_results.append({
                        'report_id': report.report_id,
                        'status': 'error',
                        'error': str(e)
                    })
        
        # 3. 요약
        summary = {
            'total_reports': len(reports),
            'analyzed': sum(1 for r in analysis_results if r['status'] == 'success'),
            'failed': sum(1 for r in analysis_results if r['status'] != 'success'),
            'analysis_enabled': self.use_analysis
        }
        
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 최종 요약")
        self.logger.info("="*60)
        self.logger.info(f"  수집: {summary['total_reports']}개")
        self.logger.info(f"  분석: {summary['analyzed']}개")
        self.logger.info(f"  실패: {summary['failed']}개")
        
        return {
            'reports': reports,
            'analysis_results': analysis_results,
            'summary': summary
        }
    
    def _extract_report_content(self, report: ReportMetadata) -> Optional[str]:
        """
        보고서 상세 내용 추출
        
        Args:
            report: ReportMetadata 객체
        
        Returns:
            보고서 텍스트 내용
        """
        
        try:
            # 상세 페이지 크롤링
            detail = self.crawler._crawl_report_detail(report.source_url)
            
            if not detail:
                return None
            
            # 텍스트 추출 (제목 + 본문)
            from bs4 import BeautifulSoup
            
            html = self.crawler._fetch(report.source_url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 본문 추출
            content_parts = []
            
            # 제목
            title = detail.get('title', report.title)
            if title:
                content_parts.append(f"제목: {title}")
            
            # 본문 (여러 패턴 시도)
            body = soup.find('div', {'class': 'content'}) or \
                   soup.find('div', {'class': 'article'}) or \
                   soup.find('div', {'id': 'content'}) or \
                   soup.find('div', {'class': 'body'})
            
            if body:
                # 텍스트만 추출 (태그 제거)
                text = body.get_text(separator='\n', strip=True)
                content_parts.append(text)
            else:
                # 전체 본문 텍스트 추출
                body = soup.find('body')
                if body:
                    # 스크립트, 스타일 제거
                    for script in body(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    
                    text = body.get_text(separator='\n', strip=True)
                    content_parts.append(text)
            
            # 추가 정보
            if detail.get('investment_opinion'):
                content_parts.append(f"투자의견: {detail['investment_opinion']}")
            
            if detail.get('target_price'):
                content_parts.append(f"목표가: {detail['target_price']}")
            
            return '\n\n'.join(content_parts)
            
        except Exception as e:
            self.logger.error(f"내용 추출 오류: {e}")
            return None
    
    def save_results(
        self,
        results: dict,
        json_file: str = 'crawled_reports.json',
        analysis_file: str = 'analysis_results.json'
    ):
        """결과 저장"""
        
        import json
        
        # 크롤링 결과 저장
        if results['reports']:
            self.crawler.save_to_json(results['reports'], json_file)
            self.logger.info(f"💾 크롤링 결과 저장: {json_file}")
        
        # 분석 결과 저장
        if results['analysis_results']:
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"💾 분석 결과 저장: {analysis_file}")

# ============================================================
# 사용 예제
# ============================================================

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🚀 통합 크롤러 시작")
    print("="*60)
    print()
    
    # 통합 크롤러 초기화
    integrated = IntegratedCrawler(
        use_analysis=True,
        crawler_delay=3.0,
        use_adaptive=True
    )
    
    # 크롤링 + 분석
    results = integrated.crawl_and_analyze(
        days=1,
        max_reports=5,  # 테스트용 5개
        extract_content=True
    )
    
    # 결과 저장
    integrated.save_results(results)
    
    # 결과 출력
    print("\n" + "="*60)
    print("📊 최종 결과")
    print("="*60)
    print(f"수집: {results['summary']['total_reports']}개")
    print(f"분석: {results['summary']['analyzed']}개")
    print(f"실패: {results['summary']['failed']}개")
    
    # 분석 결과 샘플 출력
    if results['analysis_results']:
        print("\n📋 분석 결과 샘플:")
        for res in results['analysis_results'][:3]:
            if res['status'] == 'success':
                result = res['result']
                print(f"\n  보고서 ID: {result['report_id']}")
                print(f"  추출 시간: {result['extract_time']:.2f}초")
                print(f"  아바타 시간: {result['avatar_time']:.2f}초")
                print(f"  아바타 결과: {len(result['avatar_results'])}개")
                
                # 첫 번째 아바타 결과
                if result['avatar_results']:
                    first = result['avatar_results'][0]
                    print(f"    - {first['avatar_id']}: {first['result']}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

