"""
검색 결과 요약 생성기
AI를 사용하여 검색 결과를 요약하고 분석
"""

import sys
from typing import List, Dict
from datetime import datetime
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from keyword_search_engine import SearchResult

# Ollama LLM (선택적)
try:
    from ollama_llm import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class SearchSummaryGenerator:
    """검색 결과 요약 생성기"""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = 'llama3'):
        """
        초기화
        
        Args:
            use_ollama: Ollama 사용 여부
            ollama_model: Ollama 모델명
        """
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        
        if use_ollama and OLLAMA_AVAILABLE:
            try:
                self.ollama = OllamaLLM(model=ollama_model)
                self.llm_available = True
            except Exception as e:
                logger.warning(f"Ollama 초기화 실패: {e}")
                self.ollama = None
                self.llm_available = False
        else:
            self.ollama = None
            self.llm_available = False
    
    def generate_summary(
        self,
        keyword: str,
        results: List[SearchResult],
        max_items: int = 10
    ) -> Dict:
        """
        검색 결과 요약 생성
        
        Args:
            keyword: 검색 키워드
            results: 검색 결과 리스트
            max_items: 요약에 포함할 최대 항목 수
        
        Returns:
            요약 딕셔너리
        """
        if not results:
            return {
                'keyword': keyword,
                'total_results': 0,
                'summary': '검색 결과가 없습니다.',
                'key_findings': [],
                'sources': {},
                'stock_codes': [],
                'sectors': []
            }
        
        # 상위 결과만 사용
        top_results = results[:max_items]
        
        # 기본 통계
        sources = {}
        stock_codes = []
        sectors = []
        
        for result in top_results:
            # 소스별 카운트
            sources[result.source] = sources.get(result.source, 0) + 1
            
            # 종목 코드 수집
            if result.stock_codes:
                stock_codes.extend(result.stock_codes)
            
            # 섹터 수집
            if result.sectors:
                sectors.extend(result.sectors)
        
        # 중복 제거
        stock_codes = list(set(stock_codes))
        sectors = list(set(sectors))
        
        # AI 요약 생성
        if self.llm_available and self.ollama:
            ai_summary = self._generate_ai_summary(keyword, top_results)
        else:
            ai_summary = self._generate_simple_summary(keyword, top_results)
        
        # 주요 발견사항 추출
        key_findings = self._extract_key_findings(top_results)
        
        return {
            'keyword': keyword,
            'total_results': len(results),
            'summary': ai_summary,
            'key_findings': key_findings,
            'sources': sources,
            'stock_codes': stock_codes,
            'sectors': sectors,
            'top_results': [
                {
                    'title': r.title,
                    'source': r.source,
                    'relevance': r.relevance_score
                }
                for r in top_results[:5]
            ],
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_ai_summary(
        self,
        keyword: str,
        results: List[SearchResult]
    ) -> str:
        """AI를 사용한 요약 생성"""
        try:
            # 결과 텍스트 구성
            results_text = []
            for i, result in enumerate(results[:10], 1):
                results_text.append(
                    f"{i}. [{result.source}] {result.title}\n"
                    f"   {result.summary or result.content[:200] if result.content else ''}"
                )
            
            prompt = f"""당신은 한국어 전문가입니다. 다음 검색 결과를 한국어로만 요약해주세요.

중요: 
- 반드시 한국어로만 작성하세요. 영어는 절대 사용하지 마세요.
- "Here is", "Summary", "The following" 같은 영어 표현 금지
- 자연스러운 한국어 문장으로 작성하세요.

검색 키워드: '{keyword}'

검색 결과:
{chr(10).join(results_text)}

위 검색 결과를 한국어로 요약하여 주요 내용을 3-5문장으로 정리해주세요. 영어는 절대 사용하지 마세요:
"""
            
            summary = self.ollama.process(prompt)
            summary = summary.strip()
            
            # 영어로 시작하는 경우 제거
            english_prefixes = [
                "Here is", "Here are", "Summary:", "The following", 
                "Based on", "According to", "This is", "These are"
            ]
            for prefix in english_prefixes:
                if summary.startswith(prefix):
                    # 영어 부분 제거하고 한글 부분만 추출
                    lines = summary.split('\n')
                    korean_lines = [line for line in lines if not any(line.strip().startswith(p) for p in english_prefixes)]
                    if korean_lines:
                        summary = '\n'.join(korean_lines).strip()
                    break
            
            # 영어만 있는 경우 간단한 한글 요약으로 대체
            if not any('\uac00' <= char <= '\ud7a3' for char in summary):
                # 한글이 하나도 없으면 간단한 요약 생성
                return self._generate_simple_summary(keyword, results)
            
            return summary
        
        except Exception as e:
            logger.error(f"AI 요약 생성 실패: {e}")
            return self._generate_simple_summary(keyword, results)
    
    def _generate_simple_summary(
        self,
        keyword: str,
        results: List[SearchResult]
    ) -> str:
        """간단한 요약 생성 (AI 없이)"""
        summary_parts = []
        
        summary_parts.append(f"'{keyword}' 키워드로 {len(results)}개의 검색 결과를 찾았습니다.")
        
        # 소스별 통계
        sources = {}
        for result in results:
            sources[result.source] = sources.get(result.source, 0) + 1
        
        if sources:
            source_text = ", ".join([f"{k} {v}개" for k, v in sources.items()])
            summary_parts.append(f"소스별: {source_text}")
        
        # 종목 코드
        stock_codes = []
        for result in results:
            if result.stock_codes:
                stock_codes.extend(result.stock_codes)
        
        if stock_codes:
            unique_codes = list(set(stock_codes))[:5]
            summary_parts.append(f"관련 종목: {', '.join(unique_codes)}")
        
        return " ".join(summary_parts)
    
    def _extract_key_findings(self, results: List[SearchResult]) -> List[str]:
        """주요 발견사항 추출"""
        findings = []
        
        # 상위 3개 결과의 제목
        for result in results[:3]:
            findings.append(f"[{result.source}] {result.title}")
        
        return findings
    
    def generate_stock_summary(
        self,
        stock_code: str,
        stock_name: str,
        results: List[SearchResult]
    ) -> Dict:
        """종목별 요약 생성"""
        if not results:
            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'summary': f'{stock_name}({stock_code})에 대한 검색 결과가 없습니다.',
                'report_count': 0,
                'news_count': 0
            }
        
        report_count = sum(1 for r in results if r.source == 'report')
        news_count = sum(1 for r in results if r.source == 'news')
        
        # AI 요약
        if self.llm_available and self.ollama:
            summary = self._generate_stock_ai_summary(stock_name, results)
        else:
            summary = f"{stock_name}({stock_code})에 대한 보고서 {report_count}개, 뉴스 {news_count}개를 찾았습니다."
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'summary': summary,
            'report_count': report_count,
            'news_count': news_count,
            'total_results': len(results),
            'latest_result': results[0].title if results else None
        }
    
    def _generate_stock_ai_summary(
        self,
        stock_name: str,
        results: List[SearchResult]
    ) -> str:
        """종목별 AI 요약"""
        try:
            results_text = []
            for i, result in enumerate(results[:5], 1):
                results_text.append(f"{i}. [{result.source}] {result.title}")
            
            prompt = f"""당신은 한국어 전문가입니다. 다음 종목에 대한 검색 결과를 한국어로만 요약해주세요.

중요: 
- 반드시 한국어로만 작성하세요. 영어는 절대 사용하지 마세요.
- 자연스러운 한국어 문장으로 작성하세요.

종목명: {stock_name}

검색 결과:
{chr(10).join(results_text)}

위 검색 결과를 바탕으로 {stock_name}에 대한 주요 내용을 2-3문장으로 한국어로만 요약해주세요:
"""
            
            summary = self.ollama.process(prompt)
            summary = summary.strip()
            
            # 영어로 시작하는 경우 제거
            english_prefixes = [
                "Here is", "Here are", "Summary:", "The following", 
                "Based on", "According to", "This is", "These are"
            ]
            for prefix in english_prefixes:
                if summary.startswith(prefix):
                    lines = summary.split('\n')
                    korean_lines = [line for line in lines if not any(line.strip().startswith(p) for p in english_prefixes)]
                    if korean_lines:
                        summary = '\n'.join(korean_lines).strip()
                    break
            
            # 영어만 있는 경우 간단한 한글 요약으로 대체
            if not any('\uac00' <= char <= '\ud7a3' for char in summary):
                return f"{stock_name}에 대한 {len(results)}개의 검색 결과를 찾았습니다."
            
            return summary
        
        except Exception as e:
            logger.error(f"종목 요약 생성 실패: {e}")
            return f"{stock_name}에 대한 {len(results)}개의 검색 결과를 찾았습니다."

