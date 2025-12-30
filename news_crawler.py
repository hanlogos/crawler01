"""
Phase A-1: 뉴스 크롤러 - 기본 구조
다중 소스에서 뉴스를 수집하는 크롤러
"""

import sys
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import feedparser
import requests
from bs4 import BeautifulSoup
import time

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    content: Optional[str]
    summary: Optional[str]
    url: str
    source: str
    source_tier: int
    author: Optional[str]
    published_at: datetime
    
    # 자동 생성 필드
    category: Optional[str] = None
    urgency_level: int = 1
    stock_codes: List[str] = None
    sectors: List[str] = None
    keywords: List[str] = None
    sentiment: Optional[str] = None
    sentiment_score: float = 0.0
    credibility_score: float = 0.0
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """초기화 후 자동 처리"""
        if self.stock_codes is None:
            self.stock_codes = []
        if self.sectors is None:
            self.sectors = []
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        
        # 콘텐츠 해시 생성
        if self.content_hash is None:
            self.content_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """콘텐츠 기반 해시 생성 (중복 방지)"""
        content = f"{self.title}|{self.url}|{self.published_at}"
        return hashlib.sha256(content.encode()).hexdigest()


class BaseNewsCrawler(ABC):
    """뉴스 크롤러 기본 클래스"""
    
    def __init__(self, source_name: str, source_tier: int):
        self.source_name = source_name
        self.source_tier = source_tier
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def crawl(self) -> List[NewsArticle]:
        """뉴스 크롤링 (하위 클래스에서 구현)"""
        pass
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # HTML 태그 제거
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # 공백 정리
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_stock_codes(self, text: str) -> List[str]:
        """텍스트에서 종목 코드 추출"""
        import re
        
        # 6자리 숫자 패턴 (한국 주식 코드)
        pattern = r'\b\d{6}\b'
        codes = re.findall(pattern, text)
        
        return list(set(codes))  # 중복 제거
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """키워드 추출 (간단 버전)"""
        # 실제로는 KoNLPy 등으로 명사 추출 권장
        words = text.split()
        
        # 불용어 제거 (간단 버전)
        stopwords = {'은', '는', '이', '가', '을', '를', '에', '의', '와', '과'}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 빈도수 기반 상위 키워드
        from collections import Counter
        counter = Counter(keywords)
        
        return [word for word, _ in counter.most_common(max_keywords)]


class RSSNewsCrawler(BaseNewsCrawler):
    """RSS 피드 기반 뉴스 크롤러"""
    
    def __init__(self, source_name: str, source_tier: int, rss_url: str):
        super().__init__(source_name, source_tier)
        self.rss_url = rss_url
    
    def crawl(self) -> List[NewsArticle]:
        """RSS 피드에서 뉴스 수집"""
        try:
            logger.info(f"Crawling RSS: {self.source_name} - {self.rss_url}")
            
            # RSS 피드 파싱
            feed = feedparser.parse(self.rss_url)
            
            articles = []
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing entry: {e}")
                    continue
            
            logger.info(f"Collected {len(articles)} articles from {self.source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error crawling RSS {self.source_name}: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[NewsArticle]:
        """RSS 엔트리를 NewsArticle로 변환"""
        try:
            # 제목
            title = self._clean_text(entry.get('title', ''))
            if not title:
                return None
            
            # URL
            url = entry.get('link', '')
            if not url:
                return None
            
            # 내용
            content = self._clean_text(entry.get('description', ''))
            summary = self._clean_text(entry.get('summary', ''))
            
            # 작성자
            author = entry.get('author', None)
            
            # 발행 시간
            published_time = entry.get('published_parsed', entry.get('updated_parsed'))
            if published_time:
                published_at = datetime(*published_time[:6])
            else:
                published_at = datetime.now()
            
            # 종목 코드 추출
            full_text = f"{title} {content}"
            stock_codes = self._extract_stock_codes(full_text)
            
            # 키워드 추출
            keywords = self._extract_keywords(full_text)
            
            return NewsArticle(
                title=title,
                content=content,
                summary=summary or content[:200],
                url=url,
                source=self.source_name,
                source_tier=self.source_tier,
                author=author,
                published_at=published_at,
                stock_codes=stock_codes,
                keywords=keywords
            )
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None


class HTMLNewsCrawler(BaseNewsCrawler):
    """HTML 페이지 크롤링 (동적 구조)"""
    
    def __init__(
        self, 
        source_name: str, 
        source_tier: int, 
        base_url: str,
        selectors: Dict[str, str]
    ):
        super().__init__(source_name, source_tier)
        self.base_url = base_url
        self.selectors = selectors  # CSS 선택자
    
    def crawl(self) -> List[NewsArticle]:
        """HTML 페이지에서 뉴스 수집"""
        try:
            logger.info(f"Crawling HTML: {self.source_name} - {self.base_url}")
            
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            
            # 기사 리스트 찾기
            article_elements = soup.select(self.selectors.get('article_list', 'article'))
            
            for element in article_elements[:20]:  # 최대 20개
                try:
                    article = self._parse_element(element, soup)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing element: {e}")
                    continue
            
            logger.info(f"Collected {len(articles)} articles from {self.source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error crawling HTML {self.source_name}: {e}")
            return []
    
    def _parse_element(self, element, soup) -> Optional[NewsArticle]:
        """HTML 요소를 NewsArticle로 변환"""
        try:
            # 제목
            title_elem = element.select_one(self.selectors.get('title', 'h2, h3'))
            title = self._clean_text(title_elem.text) if title_elem else None
            
            if not title:
                return None
            
            # URL
            link_elem = element.select_one(self.selectors.get('link', 'a'))
            url = link_elem.get('href', '') if link_elem else ''
            
            # 상대 경로 → 절대 경로
            if url and not url.startswith('http'):
                from urllib.parse import urljoin
                url = urljoin(self.base_url, url)
            
            if not url:
                return None
            
            # 내용
            content_elem = element.select_one(self.selectors.get('content', 'p'))
            content = self._clean_text(content_elem.text) if content_elem else ''
            
            # 시간
            time_elem = element.select_one(self.selectors.get('time', 'time'))
            published_at = self._parse_time(time_elem) if time_elem else datetime.now()
            
            return NewsArticle(
                title=title,
                content=content,
                summary=content[:200] if content else title,
                url=url,
                source=self.source_name,
                source_tier=self.source_tier,
                author=None,
                published_at=published_at,
                stock_codes=self._extract_stock_codes(f"{title} {content}"),
                keywords=self._extract_keywords(f"{title} {content}")
            )
            
        except Exception as e:
            logger.error(f"Error parsing element: {e}")
            return None
    
    def _parse_time(self, time_elem) -> datetime:
        """시간 요소 파싱"""
        try:
            # datetime 속성 먼저 시도
            dt_str = time_elem.get('datetime', '')
            if dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            
            # 텍스트 파싱
            text = time_elem.text.strip()
            
            # "1시간 전", "30분 전" 같은 상대 시간
            if '분 전' in text or '시간 전' in text:
                return datetime.now()
            
            return datetime.now()
            
        except Exception:
            return datetime.now()


# ================================================================
# 실제 소스별 크롤러 구현
# ================================================================

class YonhapNewsCrawler(RSSNewsCrawler):
    """연합뉴스 크롤러"""
    
    def __init__(self):
        super().__init__(
            source_name='연합뉴스',
            source_tier=2,
            rss_url='https://www.yna.co.kr/rss/economy.xml'
        )


class NaverFinanceCrawler(HTMLNewsCrawler):
    """네이버 금융 뉴스 크롤러"""
    
    def __init__(self):
        super().__init__(
            source_name='네이버금융',
            source_tier=2,
            base_url='https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
            selectors={
                'article_list': '.newsList li',
                'title': '.articleSubject a',
                'link': '.articleSubject a',
                'content': '.articleSummary',
                'time': '.wdate'
            }
        )


class HankyungNewsCrawler(RSSNewsCrawler):
    """한국경제 크롤러"""
    
    def __init__(self):
        super().__init__(
            source_name='한국경제',
            source_tier=2,
            rss_url='https://www.hankyung.com/feed/economy'
        )


# ================================================================
# 크롤링 매니저 (여러 크롤러 통합)
# ================================================================

class NewsCrawlerManager:
    """여러 크롤러를 통합 관리"""
    
    def __init__(self):
        self.crawlers = []
        self._register_default_crawlers()
    
    def _register_default_crawlers(self):
        """기본 크롤러 등록"""
        self.crawlers = [
            YonhapNewsCrawler(),
            NaverFinanceCrawler(),
            HankyungNewsCrawler(),
        ]
    
    def add_crawler(self, crawler: BaseNewsCrawler):
        """크롤러 추가"""
        self.crawlers.append(crawler)
    
    def crawl_all(self) -> List[NewsArticle]:
        """모든 크롤러 실행"""
        all_articles = []
        
        for crawler in self.crawlers:
            try:
                articles = crawler.crawl()
                all_articles.extend(articles)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in crawler {crawler.source_name}: {e}")
                continue
        
        logger.info(f"Total collected: {len(all_articles)} articles")
        return all_articles
    
    def crawl_by_tier(self, tier: int) -> List[NewsArticle]:
        """특정 Tier만 크롤링"""
        articles = []
        
        for crawler in self.crawlers:
            if crawler.source_tier == tier:
                articles.extend(crawler.crawl())
                time.sleep(1)
        
        return articles


# ================================================================
# 테스트 코드
# ================================================================

if __name__ == '__main__':
    # 단일 크롤러 테스트
    print("=== 연합뉴스 크롤러 테스트 ===")
    yonhap = YonhapNewsCrawler()
    articles = yonhap.crawl()
    
    if articles:
        print(f"\n수집된 기사: {len(articles)}개")
        print(f"\n첫 번째 기사:")
        first = articles[0]
        print(f"제목: {first.title}")
        print(f"URL: {first.url}")
        print(f"발행: {first.published_at}")
        print(f"종목코드: {first.stock_codes}")
        print(f"키워드: {first.keywords[:5]}")
    
    # 통합 매니저 테스트
    print("\n\n=== 통합 크롤러 테스트 ===")
    manager = NewsCrawlerManager()
    all_articles = manager.crawl_all()
    
    print(f"\n총 수집: {len(all_articles)}개")
    
    # 소스별 통계
    from collections import Counter
    source_count = Counter([a.source for a in all_articles])
    print("\n소스별 수집 현황:")
    for source, count in source_count.items():
        print(f"  {source}: {count}개")

