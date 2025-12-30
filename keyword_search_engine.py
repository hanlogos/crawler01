"""
키워드 검색 엔진
구글 검색창처럼 키워드로 관련 회사/산업군/섹터 검색
"""

import sys
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from collections import Counter

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과"""
    result_id: str
    title: str
    content: str
    source: str  # 'report', 'news', 'stock'
    source_id: str
    url: Optional[str] = None
    stock_codes: List[str] = None
    sectors: List[str] = None
    keywords: List[str] = None
    relevance_score: float = 0.0
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    
    def __post_init__(self):
        if self.stock_codes is None:
            self.stock_codes = []
        if self.sectors is None:
            self.sectors = []
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.published_at:
            data['published_at'] = self.published_at.isoformat()
        return data


@dataclass
class SearchQuery:
    """검색 쿼리"""
    query_id: str
    keyword: str
    search_type: str  # 'all', 'reports', 'news', 'stocks'
    filters: Dict = None
    created_at: datetime = None
    result_count: int = 0
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data


class KeywordSearchEngine:
    """키워드 검색 엔진"""
    
    def __init__(
        self,
        report_manager=None,
        news_crawler_manager=None,
        stock_info_db=None
    ):
        """
        초기화
        
        Args:
            report_manager: ReportTitleManager 인스턴스
            news_crawler_manager: NewsCrawlerManager 인스턴스
            stock_info_db: 종목 정보 데이터베이스 (선택)
        """
        self.report_manager = report_manager
        self.news_crawler_manager = news_crawler_manager
        self.stock_info_db = stock_info_db
        self.logger = logging.getLogger(__name__)
    
    def search(
        self,
        keyword: str,
        search_type: str = 'all',
        filters: Dict = None,
        limit: int = 50
    ) -> Tuple[List[SearchResult], SearchQuery]:
        """
        키워드 검색
        
        Args:
            keyword: 검색 키워드
            search_type: 검색 타입 ('all', 'reports', 'news', 'stocks')
            filters: 필터 (sector, stock_code, date_range 등)
            limit: 결과 제한
        
        Returns:
            (검색 결과 리스트, 검색 쿼리)
        """
        self.logger.info(f"검색 시작: '{keyword}' (타입: {search_type})")
        
        query = SearchQuery(
            query_id=f"Q_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            keyword=keyword,
            search_type=search_type,
            filters=filters or {}
        )
        
        results = []
        
        # 1. 보고서 검색
        if search_type in ('all', 'reports') and self.report_manager:
            report_results = self._search_reports(keyword, filters)
            results.extend(report_results)
        
        # 2. 뉴스 검색
        if search_type in ('all', 'news') and self.news_crawler_manager:
            news_results = self._search_news(keyword, filters)
            results.extend(news_results)
        
        # 3. 종목 검색
        if search_type in ('all', 'stocks'):
            stock_results = self._search_stocks(keyword, filters)
            results.extend(stock_results)
        
        # 관련도 점수 계산 및 정렬
        results = self._calculate_relevance(results, keyword)
        results = sorted(results, key=lambda x: x.relevance_score, reverse=True)[:limit]
        
        query.result_count = len(results)
        
        self.logger.info(f"검색 완료: {len(results)}개 결과")
        
        return results, query
    
    def _search_reports(self, keyword: str, filters: Dict = None) -> List[SearchResult]:
        """보고서 검색"""
        if not self.report_manager:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        # ReportTitleManager의 search_titles 사용
        matching_titles = self.report_manager.search_titles(keyword)
        
        for title_obj in matching_titles:
            # 필터 적용
            if filters:
                if 'stock_code' in filters:
                    # 키워드에서 종목 코드 추출 (간단 버전)
                    if not any(code in str(title_obj.keywords) for code in filters['stock_code']):
                        continue
            
            # 관련도 계산
            relevance = self._calculate_text_relevance(
                keyword_lower,
                title_obj.original_title.lower(),
                title_obj.keywords
            )
            
            result = SearchResult(
                result_id=f"RPT_{title_obj.report_id}",
                title=title_obj.get_display_title(),
                content=title_obj.original_title,
                source='report',
                source_id=title_obj.report_id,
                keywords=title_obj.keywords,
                relevance_score=relevance,
                published_at=title_obj.created_at
            )
            
            results.append(result)
        
        return results
    
    def _search_news(self, keyword: str, filters: Dict = None) -> List[SearchResult]:
        """뉴스 검색"""
        if not self.news_crawler_manager:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        # 최근 크롤링된 뉴스에서 검색 (실제로는 DB에서 조회)
        # 여기서는 시뮬레이션
        try:
            # 뉴스 크롤러에서 최근 기사 가져오기
            # 크롤링은 시간이 걸릴 수 있으므로 비동기 처리 권장
            # 여기서는 빈 리스트 반환 (실제 뉴스 검색은 DB에서)
            articles = []
            
            # 실제로는 DB에서 검색해야 함
            # articles = self.news_crawler_manager.crawl_all()  # 이건 너무 느림
            
            for article in articles:
                # 키워드 매칭
                if (keyword_lower in article.title.lower() or
                    (article.content and keyword_lower in article.content.lower()) or
                    any(keyword_lower in kw.lower() for kw in (article.keywords or []))):
                    
                    relevance = self._calculate_text_relevance(
                        keyword_lower,
                        article.title.lower(),
                        article.keywords or []
                    )
                    
                    result = SearchResult(
                        result_id=f"NEWS_{article.content_hash[:8] if hasattr(article, 'content_hash') else 'unknown'}",
                        title=article.title,
                        content=article.content or article.summary or "",
                        source='news',
                        source_id=getattr(article, 'content_hash', 'unknown'),
                        url=getattr(article, 'url', ''),
                        stock_codes=getattr(article, 'stock_codes', []),
                        sectors=getattr(article, 'sectors', []),
                        keywords=getattr(article, 'keywords', []),
                        relevance_score=relevance,
                        published_at=getattr(article, 'published_at', None),
                        summary=getattr(article, 'summary', None)
                    )
                    
                    results.append(result)
        except Exception as e:
            self.logger.error(f"뉴스 검색 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        return results
    
    def _search_stocks(self, keyword: str, filters: Dict = None) -> List[SearchResult]:
        """종목 검색"""
        results = []
        keyword_lower = keyword.lower()
        
        # 종목 정보 검색 (실제로는 종목 DB에서)
        # 여기서는 키워드에서 종목 코드 추출 시도
        stock_codes = self._extract_stock_codes(keyword)
        
        # 종목명 매칭 (간단 버전)
        # 실제로는 종목 정보 DB에서 검색
        common_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660',
            'LG에너지솔루션': '373220',
            '현대차': '005380',
            'NAVER': '035420',
            '카카오': '035720',
        }
        
        for stock_name, stock_code in common_stocks.items():
            if keyword_lower in stock_name.lower() or stock_code in keyword:
                result = SearchResult(
                    result_id=f"STOCK_{stock_code}",
                    title=f"{stock_name} ({stock_code})",
                    content=f"{stock_name} 종목 정보",
                    source='stock',
                    source_id=stock_code,
                    stock_codes=[stock_code],
                    relevance_score=1.0 if keyword_lower in stock_name.lower() else 0.8
                )
                results.append(result)
        
        return results
    
    def _calculate_text_relevance(
        self,
        keyword: str,
        text: str,
        keywords: List[str] = None
    ) -> float:
        """텍스트 관련도 계산"""
        score = 0.0
        
        # 제목에 키워드 포함
        if keyword in text:
            score += 0.5
        
        # 키워드 리스트에 포함
        if keywords:
            keyword_matches = sum(1 for kw in keywords if keyword in kw.lower())
            score += keyword_matches * 0.2
        
        # 정확 일치
        if keyword == text:
            score = 1.0
        
        return min(score, 1.0)
    
    def _calculate_relevance(
        self,
        results: List[SearchResult],
        keyword: str
    ) -> List[SearchResult]:
        """결과 관련도 재계산"""
        keyword_lower = keyword.lower()
        
        for result in results:
            score = result.relevance_score
            
            # 제목에 키워드 포함 여부
            if keyword_lower in result.title.lower():
                score += 0.3
            
            # 내용에 키워드 포함
            if keyword_lower in result.content.lower():
                score += 0.2
            
            # 키워드 리스트 매칭
            if result.keywords:
                matches = sum(1 for kw in result.keywords if keyword_lower in kw.lower())
                score += matches * 0.1
            
            result.relevance_score = min(score, 1.0)
        
        return results
    
    def _extract_stock_codes(self, text: str) -> List[str]:
        """텍스트에서 종목 코드 추출"""
        pattern = r'\b\d{6}\b'
        codes = re.findall(pattern, text)
        return list(set(codes))
    
    def search_by_stock_code(self, stock_code: str) -> List[SearchResult]:
        """종목 코드로 검색"""
        results = []
        
        # 보고서에서 검색
        if self.report_manager:
            for title_obj in self.report_manager.list_titles():
                if stock_code in str(title_obj.keywords):
                    result = SearchResult(
                        result_id=f"RPT_{title_obj.report_id}",
                        title=title_obj.get_display_title(),
                        content=title_obj.original_title,
                        source='report',
                        source_id=title_obj.report_id,
                        stock_codes=[stock_code],
                        relevance_score=0.9,
                        published_at=title_obj.created_at
                    )
                    results.append(result)
        
        return results
    
    def search_by_sector(self, sector: str) -> List[SearchResult]:
        """섹터로 검색"""
        results = []
        
        # 보고서에서 검색
        if self.report_manager:
            for title_obj in self.report_manager.list_titles():
                # 키워드에 섹터 포함 여부 확인
                if any(sector.lower() in kw.lower() for kw in title_obj.keywords):
                    result = SearchResult(
                        result_id=f"RPT_{title_obj.report_id}",
                        title=title_obj.get_display_title(),
                        content=title_obj.original_title,
                        source='report',
                        source_id=title_obj.report_id,
                        sectors=[sector],
                        relevance_score=0.8,
                        published_at=title_obj.created_at
                    )
                    results.append(result)
        
        return results


# ================================================================
# 검색 히스토리 관리
# ================================================================

class SearchHistoryManager:
    """검색 히스토리 관리"""
    
    def __init__(self, storage_file: str = "search_history.json"):
        self.storage_file = storage_file
        self.history: List[SearchQuery] = []
        self.logger = logging.getLogger(__name__)
        self._load_history()
    
    def add_search(self, query: SearchQuery):
        """검색 히스토리 추가"""
        self.history.append(query)
        # 최근 1000개만 보관
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        self._save_history()
    
    def get_recent_searches(self, limit: int = 20) -> List[SearchQuery]:
        """최근 검색 내역"""
        return self.history[-limit:][::-1]
    
    def get_popular_keywords(self, limit: int = 10) -> List[Tuple[str, int]]:
        """인기 검색어"""
        keyword_counts = Counter([q.keyword for q in self.history])
        return keyword_counts.most_common(limit)
    
    def get_frequent_searches(self, limit: int = 10) -> List[SearchQuery]:
        """자주 검색한 키워드"""
        keyword_counts = Counter([q.keyword for q in self.history])
        frequent_keywords = [kw for kw, _ in keyword_counts.most_common(limit)]
        
        # 각 키워드의 최근 검색 쿼리 반환
        results = []
        for keyword in frequent_keywords:
            for query in reversed(self.history):
                if query.keyword == keyword:
                    results.append(query)
                    break
        
        return results
    
    def _load_history(self):
        """히스토리 로드"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for query_data in data.get('history', []):
                query = SearchQuery(**query_data)
                if isinstance(query.created_at, str):
                    query.created_at = datetime.fromisoformat(query.created_at)
                self.history.append(query)
            
            self.logger.info(f"검색 히스토리 로드: {len(self.history)}개")
        
        except FileNotFoundError:
            self.logger.info("검색 히스토리 파일이 없습니다.")
        except Exception as e:
            self.logger.error(f"히스토리 로드 실패: {e}")
    
    def _save_history(self):
        """히스토리 저장"""
        try:
            data = {
                'history': [q.to_dict() for q in self.history],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"히스토리 저장 실패: {e}")


# ================================================================
# 즐겨찾기 관리
# ================================================================

@dataclass
class FavoriteItem:
    """즐겨찾기 항목"""
    item_id: str
    item_type: str  # 'stock', 'keyword', 'sector'
    name: str
    value: str  # 종목코드, 키워드, 섹터명
    created_at: datetime = None
    last_used: datetime = None
    use_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_used is None:
            self.last_used = datetime.now()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.last_used:
            data['last_used'] = self.last_used.isoformat()
        return data


class FavoriteManager:
    """즐겨찾기 관리"""
    
    def __init__(self, storage_file: str = "favorites.json"):
        self.storage_file = storage_file
        self.favorites: Dict[str, FavoriteItem] = {}
        self.logger = logging.getLogger(__name__)
        self._load_favorites()
    
    def add_favorite(
        self,
        item_type: str,
        name: str,
        value: str
    ) -> FavoriteItem:
        """즐겨찾기 추가"""
        item_id = f"{item_type}_{value}"
        
        if item_id in self.favorites:
            # 이미 있으면 사용 횟수 증가
            item = self.favorites[item_id]
            item.use_count += 1
            item.last_used = datetime.now()
        else:
            item = FavoriteItem(
                item_id=item_id,
                item_type=item_type,
                name=name,
                value=value
            )
            self.favorites[item_id] = item
        
        self._save_favorites()
        return item
    
    def remove_favorite(self, item_id: str):
        """즐겨찾기 제거"""
        if item_id in self.favorites:
            del self.favorites[item_id]
            self._save_favorites()
    
    def get_favorites(self, item_type: str = None) -> List[FavoriteItem]:
        """즐겨찾기 목록"""
        if item_type:
            return [item for item in self.favorites.values() if item.item_type == item_type]
        return list(self.favorites.values())
    
    def get_frequent_favorites(self, limit: int = 10) -> List[FavoriteItem]:
        """자주 사용한 즐겨찾기"""
        items = sorted(
            self.favorites.values(),
            key=lambda x: (x.use_count, x.last_used),
            reverse=True
        )
        return items[:limit]
    
    def use_favorite(self, item_id: str):
        """즐겨찾기 사용 (횟수 증가)"""
        if item_id in self.favorites:
            item = self.favorites[item_id]
            item.use_count += 1
            item.last_used = datetime.now()
            self._save_favorites()
    
    def _load_favorites(self):
        """즐겨찾기 로드"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item_data in data.get('favorites', []):
                item = FavoriteItem(**item_data)
                if isinstance(item.created_at, str):
                    item.created_at = datetime.fromisoformat(item.created_at)
                if isinstance(item.last_used, str):
                    item.last_used = datetime.fromisoformat(item.last_used)
                self.favorites[item.item_id] = item
            
            self.logger.info(f"즐겨찾기 로드: {len(self.favorites)}개")
        
        except FileNotFoundError:
            self.logger.info("즐겨찾기 파일이 없습니다.")
        except Exception as e:
            self.logger.error(f"즐겨찾기 로드 실패: {e}")
    
    def _save_favorites(self):
        """즐겨찾기 저장"""
        try:
            data = {
                'favorites': [item.to_dict() for item in self.favorites.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"즐겨찾기 저장 실패: {e}")


# ================================================================
# 테스트 코드
# ================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("키워드 검색 엔진 테스트")
    print("=" * 60)
    
    # ReportTitleManager 로드
    from report_title_manager import ReportTitleManager
    report_manager = ReportTitleManager()
    
    # 검색 엔진 초기화
    search_engine = KeywordSearchEngine(report_manager=report_manager)
    
    # 검색 히스토리 관리자
    history_manager = SearchHistoryManager()
    
    # 즐겨찾기 관리자
    favorite_manager = FavoriteManager()
    
    # 검색 테스트
    keyword = "삼성전자"
    print(f"\n검색어: '{keyword}'")
    
    results, query = search_engine.search(keyword, search_type='all', limit=10)
    
    print(f"\n검색 결과: {len(results)}개")
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. [{result.source}] {result.title}")
        print(f"   관련도: {result.relevance_score:.2f}")
        if result.stock_codes:
            print(f"   종목코드: {', '.join(result.stock_codes)}")
    
    # 히스토리 저장
    history_manager.add_search(query)
    
    # 즐겨찾기 추가
    favorite_manager.add_favorite('stock', '삼성전자', '005930')
    
    print("\n✅ 테스트 완료!")

