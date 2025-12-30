"""
통합 검색 엔진
사용자(a) + 시스템(b) + 정보품질(c) 완전 통합
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

from enhanced_search_result import (
    EnhancedSearchResult,
    SearchResultItem,
    AIInsight,
    SystemMetrics,
    ErrorInfo,
    ActionButton,
    CredibilityScore,
    TimeInfo,
    VerificationStatus,
    SourceTier,
    RelatedStock
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class IntegratedSearchEngine:
    """통합 검색 엔진 (a + b + c)"""
    
    def __init__(self, db_params: Dict, enable_ai: bool = True):
        """
        초기화
        
        Args:
            db_params: PostgreSQL 연결 파라미터
            enable_ai: AI 인사이트 활성화
        """
        self.db_params = db_params
        self.enable_ai = enable_ai
        self.conn = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            logger.info("Database connected")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
    
    def search(
        self, 
        query: str,
        limit: int = 50,
        include_ai_insight: bool = True
    ) -> EnhancedSearchResult:
        """
        통합 검색 수행
        
        Args:
            query: 검색어
            limit: 최대 결과 수
            include_ai_insight: AI 인사이트 포함 여부
        
        Returns:
            EnhancedSearchResult
        """
        start_time = time.time()
        
        try:
            self.connect()
            
            # 1. 기본 검색 (정보 품질 c)
            items = self._search_database(query, limit)
            
            if not items:
                return self._create_empty_result(query)
            
            # 2. 신뢰도 강화 (정보 품질 c)
            items = self._enhance_credibility(items)
            
            # 3. 관련 종목 정보 추가 (사용자 관점 a)
            items = self._add_related_stocks(items)
            
            # 4. AI 인사이트 생성 (사용자 관점 a)
            ai_insight = None
            if include_ai_insight and self.enable_ai:
                ai_insight = self._generate_ai_insight(query, items)
            
            # 5. 시스템 메트릭 수집 (시스템 관점 b)
            metrics = self._collect_metrics(start_time)
            
            # 6. 액션 버튼 생성 (사용자 관점 a)
            actions = self._create_action_buttons(query, items)
            
            return EnhancedSearchResult(
                query=query,
                items=items,
                ai_insight=ai_insight,
                metrics=metrics,
                action_buttons=actions
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_msg = str(e)
            # 사용자 친화적 메시지
            if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                error_msg = "데이터베이스 테이블이 없습니다. news_ingestion_schema.sql을 실행하여 스키마를 생성하세요."
            elif "connection" in error_msg.lower() or "could not connect" in error_msg.lower():
                error_msg = "데이터베이스 연결에 실패했습니다. DB 서버가 실행 중인지 확인하세요."
            return self._create_error_result(query, error_msg)
        
        finally:
            try:
                self.disconnect()
            except:
                pass
    
    def _search_database(self, query: str, limit: int) -> List[SearchResultItem]:
        """데이터베이스 검색"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'news_articles'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.warning("news_articles 테이블이 없습니다. 빈 결과를 반환합니다.")
                return []
            
            # 종목명/종목코드 매칭
            stock_codes = self._find_stock_codes(query)
            
            # 복합 검색 쿼리 (안전한 쿼리)
            sql = """
                SELECT 
                    na.article_id,
                    na.title,
                    COALESCE(na.content, '') as content,
                    COALESCE(na.summary, na.title) as summary,
                    COALESCE(na.url, '') as url,
                    COALESCE(na.source, 'Unknown') as source,
                    COALESCE(na.source_tier, 2) as source_tier,
                    na.published_at,
                    COALESCE(na.stock_codes, ARRAY[]::text[]) as stock_codes,
                    COALESCE(na.keywords, ARRAY[]::text[]) as keywords,
                    COALESCE(na.urgency_level, 1) as urgency_level,
                    COALESCE(na.sentiment, 'neutral') as sentiment,
                    COALESCE(na.credibility_score, 0.5) as credibility_score,
                    fc.verification_status,
                    fc.confidence_score,
                    COALESCE(fc.supporting_sources, ARRAY[]::text[]) as supporting_sources,
                    COALESCE(fc.contradicting_sources, ARRAY[]::text[]) as contradicting_sources,
                    'news' as item_type
                FROM news_articles na
                LEFT JOIN fact_checks fc ON na.article_id = fc.article_id
                WHERE 
                    (
                        na.title ILIKE %s 
                        OR COALESCE(na.content, '') ILIKE %s
                        OR (%s != '' AND %s = ANY(COALESCE(na.stock_codes, ARRAY[]::text[])))
                    )
                    AND na.published_at > NOW() - INTERVAL '30 days'
                ORDER BY 
                    na.urgency_level DESC NULLS LAST,
                    na.published_at DESC NULLS LAST
                LIMIT %s;
            """
            
            search_pattern = f"%{query}%"
            stock_code = stock_codes[0] if stock_codes else ""
            
            cursor.execute(sql, (search_pattern, search_pattern, stock_code, stock_code, limit))
            rows = cursor.fetchall()
            
            # SearchResultItem 변환
            items = []
            for row in rows:
                try:
                    item = self._row_to_item(row)
                    items.append(item)
                except Exception as e:
                    logger.error(f"행 변환 실패: {e}")
                    continue
            
            return items
            
        except Exception as e:
            logger.error(f"데이터베이스 검색 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _row_to_item(self, row: Dict) -> SearchResultItem:
        """DB 행 → SearchResultItem 변환"""
        
        # 안전한 값 추출
        def safe_get(key, default):
            value = row.get(key, default)
            return default if value is None else value
        
        # VerificationStatus 안전 변환
        verification_str = safe_get('verification_status', 'unverified')
        try:
            verification_status = VerificationStatus(verification_str)
        except (ValueError, AttributeError):
            verification_status = VerificationStatus.UNVERIFIED
        
        # 신뢰도
        credibility = CredibilityScore(
            overall=float(safe_get('credibility_score', 0.5)),
            source_tier_score=0.0,  # 나중에 계산
            cross_verify_score=0.0,
            past_accuracy=0.0,
            llm_confidence=float(safe_get('confidence_score', 0.5)),
            verification_status=verification_status,
            supporting_sources=list(safe_get('supporting_sources', [])),
            contradicting_sources=list(safe_get('contradicting_sources', []))
        )
        
        # 시간 정보 (안전하게)
        published_at = safe_get('published_at', datetime.now())
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.now()
        
        time_info = TimeInfo(
            published_at=published_at,
            collected_at=datetime.now()
        )
        
        # 소스 Tier 안전 변환
        tier_value = safe_get('source_tier', 2)
        try:
            if isinstance(tier_value, str):
                tier_value = int(tier_value)
            source_tier = SourceTier(tier_value)
        except (ValueError, AttributeError):
            source_tier = SourceTier.TIER_2
        
        return SearchResultItem(
            title=str(safe_get('title', '제목 없음')),
            content=str(safe_get('content', '')),
            summary=str(safe_get('summary', safe_get('title', '요약 없음'))),
            url=str(safe_get('url', '')),
            item_type=str(safe_get('item_type', 'news')),
            source=str(safe_get('source', 'Unknown')),
            source_tier=source_tier,
            time_info=time_info,
            credibility=credibility,
            stock_codes=list(safe_get('stock_codes', [])),
            keywords=list(safe_get('keywords', [])),
            relevance_score=1.0,
            urgency_level=int(safe_get('urgency_level', 1)),
            sentiment=str(safe_get('sentiment', 'neutral'))
        )
    
    def _enhance_credibility(self, items: List[SearchResultItem]) -> List[SearchResultItem]:
        """신뢰도 재계산 (정보 품질 c)"""
        for item in items:
            # Tier별 점수
            tier_scores = {
                SourceTier.TIER_1: 0.98,
                SourceTier.TIER_2: 0.85,
                SourceTier.TIER_3: 0.65
            }
            item.credibility.source_tier_score = tier_scores.get(item.source_tier, 0.75)
            
            # 교차 검증 점수
            total = len(item.credibility.supporting_sources) + len(item.credibility.contradicting_sources)
            if total > 0:
                item.credibility.cross_verify_score = len(item.credibility.supporting_sources) / total
            else:
                item.credibility.cross_verify_score = 0.5
            
            # 과거 정확도 (소스별)
            source_accuracy = {
                '연합뉴스': 0.92,
                '네이버금융': 0.88,
                '한국경제': 0.90,
                '대신증권': 0.95,
            }
            item.credibility.past_accuracy = source_accuracy.get(item.source, 0.80)
            
            # 종합 점수 재계산
            weights = {'tier': 0.2, 'cross': 0.3, 'past': 0.2, 'llm': 0.3}
            item.credibility.overall = (
                item.credibility.source_tier_score * weights['tier'] +
                item.credibility.cross_verify_score * weights['cross'] +
                item.credibility.past_accuracy * weights['past'] +
                item.credibility.llm_confidence * weights['llm']
            )
        
        return items
    
    def _add_related_stocks(self, items: List[SearchResultItem]) -> List[SearchResultItem]:
        """관련 종목 정보 추가 (사용자 관점 a)"""
        # 실제로는 시세 API 호출
        # 여기서는 시뮬레이션
        
        for item in items:
            if item.stock_codes:
                for code in item.stock_codes[:3]:  # 최대 3개
                    stock = RelatedStock(
                        code=code,
                        name=self._get_stock_name(code),
                        current_price=76000.0,  # 실제로는 API 호출
                        change_rate=2.3,
                        volume_ratio=1.8
                    )
                    item.related_stocks.append(stock)
        
        return items
    
    def _generate_ai_insight(self, query: str, items: List[SearchResultItem]) -> AIInsight:
        """AI 인사이트 생성 (사용자 관점 a)"""
        
        # 간단한 휴리스틱 기반 (실제로는 LLM 호출)
        positive_count = sum(1 for item in items if item.sentiment == 'positive')
        negative_count = sum(1 for item in items if item.sentiment == 'negative')
        
        total = len(items)
        positive_ratio = positive_count / total if total > 0 else 0
        
        # 추천 결정
        if positive_ratio >= 0.7:
            recommendation = "강력 매수"
            confidence = 0.85
        elif positive_ratio >= 0.5:
            recommendation = "매수"
            confidence = 0.70
        elif positive_ratio >= 0.3:
            recommendation = "보유"
            confidence = 0.60
        else:
            recommendation = "매도"
            confidence = 0.65
        
        # 근거 추출
        reasoning = []
        risks = []
        
        # 긴급 뉴스 확인
        urgent_items = [item for item in items if item.urgency_level >= 4]
        if urgent_items:
            reasoning.append(f"긴급 뉴스 {len(urgent_items)}건 발생")
        
        # 신뢰도 높은 소스
        verified_items = [
            item for item in items 
            if item.credibility.verification_status == VerificationStatus.VERIFIED
        ]
        if verified_items:
            reasoning.append(f"{len(verified_items)}개 검증된 소스")
        
        # 키워드 분석
        all_keywords = []
        for item in items:
            all_keywords.extend(item.keywords)
        
        from collections import Counter
        top_keywords = Counter(all_keywords).most_common(3)
        if top_keywords:
            keywords_str = ", ".join([k for k, _ in top_keywords])
            reasoning.append(f"주요 키워드: {keywords_str}")
        
        # 리스크
        disputed_items = [
            item for item in items
            if item.credibility.verification_status == VerificationStatus.DISPUTED
        ]
        if disputed_items:
            risks.append(f"논쟁 중인 정보 {len(disputed_items)}건")
        
        # 핵심 포인트 (상위 3개 요약)
        key_points = []
        for item in items[:3]:
            if item.summary:
                point = item.summary[:100]
                key_points.append(point)
        
        return AIInsight(
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            risks=risks,
            key_points=key_points
        )
    
    def _collect_metrics(self, start_time: float) -> SystemMetrics:
        """시스템 메트릭 수집 (시스템 관점 b)"""
        
        # 검색 시간
        search_time_ms = int((time.time() - start_time) * 1000)
        
        # 크롤 상태 확인 (최근 작업 로그)
        crawl_status = {}
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            sql = """
                SELECT DISTINCT ON (source_name)
                    source_name,
                    status,
                    completed_at
                FROM crawl_jobs
                ORDER BY source_name, completed_at DESC;
            """
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            for row in rows:
                # 5분 이내 정상, 그 외 지연
                if row['completed_at'] and (datetime.now() - row['completed_at']).total_seconds() < 300:
                    status = "정상"
                else:
                    status = "지연 5분"
                
                crawl_status[row['source_name']] = status
        except Exception as e:
            logger.warning(f"Failed to collect crawl status: {e}")
            crawl_status = {}
        
        return SystemMetrics(
            search_time_ms=search_time_ms,
            total_sources_checked=len(crawl_status),
            cache_hit=False,  # 실제로는 캐시 체크
            data_freshness_minutes=2,
            crawl_status=crawl_status
        )
    
    def _create_action_buttons(
        self, 
        query: str, 
        items: List[SearchResultItem]
    ) -> List[ActionButton]:
        """액션 버튼 생성 (사용자 관점 a)"""
        
        buttons = []
        
        # 기본 액션
        buttons.append(ActionButton("📈 차트 보기", f"open_chart:{query}", "📈", "primary"))
        buttons.append(ActionButton("📰 뉴스 전체", f"view_all:{query}", "📰", "secondary"))
        
        # 종목코드가 있으면
        stock_codes = set()
        for item in items:
            stock_codes.update(item.stock_codes)
        
        if stock_codes:
            buttons.append(ActionButton("⭐ 관심종목", f"add_watchlist:{','.join(stock_codes)}", "⭐", "secondary"))
            buttons.append(ActionButton("🔔 알림 설정", f"setup_alert:{','.join(stock_codes)}", "🔔", "secondary"))
        
        return buttons
    
    def _find_stock_codes(self, query: str) -> List[str]:
        """검색어에서 종목코드 추출"""
        # 간단한 매핑 (실제로는 DB 조회)
        mapping = {
            '삼성전자': '005930',
            'SK하이닉스': '000660',
            '네이버': '035420',
            'NAVER': '035420',
        }
        
        return [mapping[query]] if query in mapping else []
    
    def _get_stock_name(self, code: str) -> str:
        """종목코드 → 종목명"""
        mapping = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': '네이버',
        }
        return mapping.get(code, code)
    
    def _create_empty_result(self, query: str) -> EnhancedSearchResult:
        """빈 결과 생성"""
        return EnhancedSearchResult(
            query=query,
            items=[],
            error=ErrorInfo(
                has_error=True,
                error_type="NO_DATA",
                error_message="검색 결과가 없습니다."
            )
        )
    
    def _create_error_result(self, query: str, error: str) -> EnhancedSearchResult:
        """오류 결과 생성"""
        return EnhancedSearchResult(
            query=query,
            items=[],
            error=ErrorInfo(
                has_error=True,
                error_type="UNKNOWN",
                error_message=error
            )
        )


# ================================================================
# 테스트
# ================================================================

if __name__ == '__main__':
    import json
    
    DB_PARAMS = {
        'host': 'localhost',
        'port': 5432,
        'database': 'abiseu',
        'user': 'postgres',
        'password': 'your_password'
    }
    
    engine = IntegratedSearchEngine(DB_PARAMS, enable_ai=True)
    
    # 검색 실행
    result = engine.search("삼성전자", limit=20, include_ai_insight=True)
    
    # JSON 출력
    print("=" * 60)
    print("통합 검색 결과")
    print("=" * 60)
    print(json.dumps(result.to_json(), ensure_ascii=False, indent=2))

