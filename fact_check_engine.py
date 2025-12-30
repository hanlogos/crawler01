"""
Phase A-1: 팩트 체크 엔진
LLM 기반 뉴스 신뢰도 검증 시스템 (OpenAI + Ollama 지원)
"""

import sys
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from collections import Counter

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# OpenAI (선택적)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Ollama (선택적)
try:
    from ollama_llm import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    """팩트 체크 결과"""
    article_id: int
    verification_status: str  # verified, disputed, false, unverified
    confidence_score: float  # 0.0 ~ 1.0
    
    supporting_sources: List[str]
    contradicting_sources: List[str]
    
    llm_analysis: str
    llm_reasoning: str
    
    cross_verified_count: int
    total_sources_checked: int
    
    similar_past_events: List[Dict]
    past_accuracy_rate: float
    
    checked_at: datetime


class FactCheckEngine:
    """팩트 체크 엔진"""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        use_ollama: bool = False,
        ollama_model: str = 'llama3'
    ):
        """
        초기화
        
        Args:
            openai_api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
            use_ollama: Ollama 사용 여부 (True면 OpenAI 대신 Ollama 사용)
            ollama_model: Ollama 모델명
        """
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        
        # OpenAI 설정
        if not use_ollama and OPENAI_AVAILABLE:
            self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            if self.api_key:
                openai.api_key = self.api_key
            self.llm_available = bool(self.api_key)
        else:
            self.api_key = None
            self.llm_available = False
        
        # Ollama 설정
        if use_ollama and OLLAMA_AVAILABLE:
            try:
                self.ollama = OllamaLLM(model=ollama_model)
                self.llm_available = True
                logger.info(f"Ollama LLM 초기화 완료 (모델: {ollama_model})")
            except Exception as e:
                logger.warning(f"Ollama 초기화 실패: {e}")
                self.ollama = None
                self.llm_available = False
        else:
            self.ollama = None
    
    def verify_article(
        self, 
        article,
        related_articles: List = None,
        use_llm: bool = True
    ) -> FactCheckResult:
        """
        기사 진위 검증
        
        Args:
            article: 검증할 기사
            related_articles: 관련 기사 리스트 (교차 검증용)
            use_llm: LLM 사용 여부
        """
        logger.info(f"Verifying article: {article.title[:50]}...")
        
        # 1. 다중 소스 교차 검증
        supporting, contradicting = self._cross_verify_sources(article, related_articles)
        
        # 2. 과거 유사 사례 확인
        similar_events, past_accuracy = self._check_past_history(article)
        
        # 3. LLM 논리 검증
        if use_llm and self.llm_available:
            llm_analysis, llm_reasoning = self._llm_verification(article, related_articles)
        else:
            llm_analysis = "LLM 검증 미실행"
            llm_reasoning = ""
        
        # 4. 최종 신뢰도 계산
        confidence, status = self._calculate_confidence(
            article=article,
            supporting_count=len(supporting),
            contradicting_count=len(contradicting),
            past_accuracy=past_accuracy,
            llm_confidence=self._extract_llm_confidence(llm_analysis) if use_llm else 0.5
        )
        
        return FactCheckResult(
            article_id=getattr(article, 'article_id', 0),
            verification_status=status,
            confidence_score=confidence,
            supporting_sources=supporting,
            contradicting_sources=contradicting,
            llm_analysis=llm_analysis,
            llm_reasoning=llm_reasoning,
            cross_verified_count=len(supporting) + len(contradicting),
            total_sources_checked=len(related_articles) if related_articles else 0,
            similar_past_events=similar_events,
            past_accuracy_rate=past_accuracy,
            checked_at=datetime.now()
        )
    
    def _cross_verify_sources(
        self, 
        article, 
        related_articles: List
    ) -> Tuple[List[str], List[str]]:
        """
        다중 소스 교차 검증
        
        Returns:
            (지지 소스 리스트, 반박 소스 리스트)
        """
        if not related_articles:
            return [], []
        
        supporting = []
        contradicting = []
        
        # 제목 키워드로 유사도 판단 (간단 버전)
        article_keywords = set(article.title.lower().split())
        
        for related in related_articles:
            if related.url == article.url:  # 자기 자신 제외
                continue
            
            related_keywords = set(related.title.lower().split())
            
            # 키워드 중복도
            overlap = len(article_keywords & related_keywords)
            total = len(article_keywords | related_keywords)
            similarity = overlap / total if total > 0 else 0
            
            # 유사도 높으면 지지, 낮으면 반박
            if similarity > 0.5:
                supporting.append(related.source)
            elif similarity < 0.2 and related.sentiment != article.sentiment:
                contradicting.append(related.source)
        
        return supporting, contradicting
    
    def _check_past_history(
        self, 
        article
    ) -> Tuple[List[Dict], float]:
        """
        과거 유사 사례 확인
        
        Returns:
            (유사 사례 리스트, 소스 과거 정확도)
        """
        # 실제로는 DB에서 조회
        # 여기서는 시뮬레이션
        
        similar_events = []
        
        # 소스별 과거 정확도 (실제로는 DB에서)
        source_accuracy = {
            '연합뉴스': 0.92,
            '네이버금융': 0.88,
            '한국경제': 0.90,
            '팍스넷': 0.75,
            '38커뮤니케이션': 0.85,
        }
        
        past_accuracy = source_accuracy.get(article.source, 0.80)
        
        return similar_events, past_accuracy
    
    def _llm_verification(
        self, 
        article, 
        related_articles: List = None
    ) -> Tuple[str, str]:
        """
        LLM을 사용한 논리적 검증 (OpenAI 또는 Ollama)
        
        Returns:
            (분석 결과, 추론 과정)
        """
        if not self.llm_available:
            return "LLM 사용 불가", ""
        
        try:
            # 컨텍스트 구성
            context = self._build_llm_context(article, related_articles)
            
            # 프롬프트 생성
            prompt = f"""당신은 팩트 체커입니다. 다음 뉴스 기사의 신뢰도를 평가하세요.

기사:
제목: {article.title}
내용: {article.content[:500] if article.content else article.title}
출처: {article.source} (Tier {article.source_tier})

{context}

다음을 분석하세요:
1. 논리적 일관성 (내용이 모순되지 않는가?)
2. 출처 신뢰도 (출처가 믿을만한가?)
3. 객관성 (과장되거나 편향되지 않았는가?)
4. 증거 (구체적 근거가 있는가?)

결론:
- 신뢰도: [높음/중간/낮음]
- 검증 상태: [verified/disputed/false/unverified]
- 신뢰도 점수: [0.0~1.0]
- 이유: [구체적 근거]
"""
            
            # LLM 호출 (Ollama 또는 OpenAI)
            if self.use_ollama and self.ollama:
                analysis = self.ollama.process(prompt)
                reasoning = self._extract_reasoning(analysis)
            elif OPENAI_AVAILABLE and self.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "당신은 전문 팩트 체커입니다. 뉴스의 신뢰도를 객관적으로 평가합니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                analysis = response.choices[0].message.content
                reasoning = self._extract_reasoning(analysis)
            else:
                return "LLM 사용 불가", ""
            
            logger.info(f"LLM verification completed for: {article.title[:50]}")
            return analysis, reasoning
            
        except Exception as e:
            logger.error(f"LLM verification failed: {e}")
            return f"LLM 오류: {str(e)}", ""
    
    def _build_llm_context(
        self, 
        article, 
        related_articles: List = None
    ) -> str:
        """LLM을 위한 컨텍스트 구성"""
        if not related_articles or len(related_articles) == 0:
            return "관련 기사 없음"
        
        # 상위 3개만
        related = related_articles[:3]
        
        context_parts = ["관련 기사:"]
        for i, rel in enumerate(related, 1):
            context_parts.append(f"{i}. [{rel.source}] {rel.title}")
        
        return "\n".join(context_parts)
    
    def _extract_reasoning(self, analysis: str) -> str:
        """LLM 분석에서 추론 과정 추출"""
        # "이유:" 이후 텍스트 추출
        if "이유:" in analysis:
            return analysis.split("이유:")[1].strip()
        return analysis
    
    def _extract_llm_confidence(self, analysis: str) -> float:
        """LLM 분석에서 신뢰도 점수 추출"""
        # 신뢰도 점수 패턴 찾기
        import re
        
        # "신뢰도 점수: 0.85" 같은 패턴
        pattern = r'신뢰도 점수[:\s]+([0-9.]+)'
        match = re.search(pattern, analysis)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # 키워드 기반 추정
        if '높음' in analysis or 'verified' in analysis.lower():
            return 0.85
        elif '중간' in analysis or 'disputed' in analysis.lower():
            return 0.60
        elif '낮음' in analysis or 'false' in analysis.lower():
            return 0.30
        
        return 0.50  # 기본값
    
    def _calculate_confidence(
        self,
        article,
        supporting_count: int,
        contradicting_count: int,
        past_accuracy: float,
        llm_confidence: float
    ) -> Tuple[float, str]:
        """
        최종 신뢰도 계산
        
        Returns:
            (신뢰도 점수, 검증 상태)
        """
        # 가중치
        weights = {
            'source_tier': 0.2,      # 소스 Tier
            'cross_verify': 0.3,     # 교차 검증
            'past_accuracy': 0.2,    # 과거 정확도
            'llm': 0.3               # LLM 판단
        }
        
        # 1. 소스 Tier 점수
        tier_score = {1: 0.98, 2: 0.85, 3: 0.65}.get(article.source_tier, 0.70)
        
        # 2. 교차 검증 점수
        total_checks = supporting_count + contradicting_count
        if total_checks > 0:
            cross_verify_score = supporting_count / total_checks
        else:
            cross_verify_score = 0.50
        
        # 3. 종합 점수
        final_score = (
            tier_score * weights['source_tier'] +
            cross_verify_score * weights['cross_verify'] +
            past_accuracy * weights['past_accuracy'] +
            llm_confidence * weights['llm']
        )
        
        # 4. 상태 판정
        if final_score >= 0.85:
            status = 'verified'
        elif final_score >= 0.60:
            status = 'unverified'
        elif final_score >= 0.40:
            status = 'disputed'
        else:
            status = 'false'
        
        # 5. 예외 처리
        if contradicting_count > supporting_count * 2:
            status = 'disputed'
            final_score = min(final_score, 0.50)
        
        return round(final_score, 2), status
    
    def batch_verify(
        self, 
        articles: List, 
        use_llm: bool = True
    ) -> List[FactCheckResult]:
        """
        여러 기사 일괄 검증
        
        Args:
            articles: 기사 리스트
            use_llm: LLM 사용 여부
        """
        results = []
        
        for article in articles:
            try:
                # 같은 주제 기사 찾기 (교차 검증용)
                related = [
                    a for a in articles 
                    if a.url != article.url and 
                    self._is_related(article, a)
                ]
                
                result = self.verify_article(article, related, use_llm)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error verifying article {article.title[:50]}: {e}")
                continue
        
        logger.info(f"Batch verification completed: {len(results)}/{len(articles)}")
        return results
    
    def _is_related(self, article1, article2, threshold: float = 0.3) -> bool:
        """두 기사가 관련있는지 판단"""
        # 키워드 중복도
        keywords1 = set(article1.keywords) if article1.keywords else set()
        keywords2 = set(article2.keywords) if article2.keywords else set()
        
        if not keywords1 or not keywords2:
            return False
        
        overlap = len(keywords1 & keywords2)
        total = len(keywords1 | keywords2)
        
        similarity = overlap / total if total > 0 else 0
        
        return similarity >= threshold


# ================================================================
# 팩트 체크 결과 요약
# ================================================================

class FactCheckSummary:
    """팩트 체크 결과 요약"""
    
    @staticmethod
    def summarize(results: List[FactCheckResult]) -> Dict:
        """
        결과 요약 생성
        
        Returns:
            통계 딕셔너리
        """
        if not results:
            return {}
        
        # 검증 상태 분포
        status_dist = Counter([r.verification_status for r in results])
        
        # 평균 신뢰도
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        
        # 교차 검증 통계
        avg_sources_checked = sum(r.total_sources_checked for r in results) / len(results)
        
        return {
            'total_articles': len(results),
            'status_distribution': dict(status_dist),
            'average_confidence': round(avg_confidence, 2),
            'verified_count': status_dist.get('verified', 0),
            'disputed_count': status_dist.get('disputed', 0),
            'false_count': status_dist.get('false', 0),
            'unverified_count': status_dist.get('unverified', 0),
            'average_sources_checked': round(avg_sources_checked, 1),
        }
    
    @staticmethod
    def print_summary(results: List[FactCheckResult]):
        """요약 출력"""
        summary = FactCheckSummary.summarize(results)
        
        print("=" * 60)
        print("팩트 체크 결과 요약")
        print("=" * 60)
        print(f"총 기사: {summary['total_articles']}개")
        print(f"평균 신뢰도: {summary['average_confidence']}")
        print(f"\n검증 상태:")
        print(f"  ✅ Verified: {summary['verified_count']}개")
        print(f"  ⚠️  Unverified: {summary['unverified_count']}개")
        print(f"  ⚡ Disputed: {summary['disputed_count']}개")
        print(f"  ❌ False: {summary['false_count']}개")
        print(f"\n평균 교차 검증 소스: {summary['average_sources_checked']}개")
        print("=" * 60)


# ================================================================
# 테스트 코드
# ================================================================

if __name__ == '__main__':
    from news_crawler import NewsArticle, NewsCrawlerManager
    
    print("=== 팩트 체크 엔진 테스트 ===\n")
    
    # 뉴스 크롤링
    manager = NewsCrawlerManager()
    articles = manager.crawl_all()
    
    if not articles:
        print("수집된 기사가 없습니다.")
        exit()
    
    print(f"수집된 기사: {len(articles)}개\n")
    
    # 팩트 체크 (Ollama 사용)
    engine = FactCheckEngine(use_ollama=True, ollama_model='llama3')
    
    # 일부만 테스트 (5개)
    test_articles = articles[:5]
    
    print("팩트 체크 시작...\n")
    results = engine.batch_verify(test_articles, use_llm=True)
    
    # 결과 출력
    print("\n개별 결과:")
    for i, result in enumerate(results, 1):
        article = test_articles[i-1]
        print(f"\n{i}. {article.title[:60]}...")
        print(f"   출처: {article.source} (Tier {article.source_tier})")
        print(f"   신뢰도: {result.confidence_score} ({result.verification_status})")
        print(f"   지지: {len(result.supporting_sources)}개, 반박: {len(result.contradicting_sources)}개")
    
    # 요약
    print("\n")
    FactCheckSummary.print_summary(results)

