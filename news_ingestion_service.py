"""
Phase A-1: 뉴스 수집 통합 서비스
크롤링 → 팩트 체크 → DB 저장 → 알림
"""

import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# PostgreSQL (선택적)
try:
    import psycopg2
    from psycopg2.extras import execute_values, Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from news_crawler import NewsArticle, NewsCrawlerManager
from fact_check_engine import FactCheckEngine, FactCheckResult

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsDatabase:
    """뉴스 데이터베이스 관리"""
    
    def __init__(self, conn_params: Dict):
        """
        초기화
        
        Args:
            conn_params: PostgreSQL 연결 파라미터
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'abiseu',
                    'user': 'postgres',
                    'password': 'password'
                }
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2가 설치되지 않았습니다. 'pip install psycopg2-binary'로 설치하세요.")
        
        self.conn_params = conn_params
        self.conn = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info("Database disconnected")
    
    def save_article(self, article: NewsArticle) -> Optional[int]:
        """
        기사 저장
        
        Returns:
            article_id (저장 성공) 또는 None (중복/실패)
        """
        try:
            cursor = self.conn.cursor()
            
            query = """
                INSERT INTO news_articles (
                    title, content, summary, url,
                    source, source_tier, author, published_at,
                    category, urgency_level,
                    stock_codes, sectors, keywords,
                    sentiment, sentiment_score,
                    credibility_score,
                    content_hash, metadata
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s
                )
                ON CONFLICT (content_hash) DO NOTHING
                RETURNING article_id;
            """
            
            cursor.execute(query, (
                article.title,
                article.content,
                article.summary,
                article.url,
                article.source,
                article.source_tier,
                article.author,
                article.published_at,
                article.category,
                article.urgency_level,
                article.stock_codes,
                article.sectors,
                article.keywords,
                article.sentiment,
                article.sentiment_score,
                article.credibility_score,
                article.content_hash,
                Json(article.metadata)
            ))
            
            result = cursor.fetchone()
            self.conn.commit()
            
            if result:
                article_id = result[0]
                logger.debug(f"Article saved: {article_id} - {article.title[:50]}")
                return article_id
            else:
                logger.debug(f"Article duplicate: {article.title[:50]}")
                return None
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving article: {e}")
            return None
    
    def save_fact_check(self, fact_check: FactCheckResult) -> bool:
        """팩트 체크 결과 저장"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                INSERT INTO fact_checks (
                    article_id, verification_status, confidence_score,
                    supporting_sources, contradicting_sources,
                    llm_analysis, llm_reasoning,
                    cross_verified_count, total_sources_checked,
                    similar_past_events, past_accuracy_rate
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s
                );
            """
            
            cursor.execute(query, (
                fact_check.article_id,
                fact_check.verification_status,
                fact_check.confidence_score,
                fact_check.supporting_sources,
                fact_check.contradicting_sources,
                fact_check.llm_analysis,
                fact_check.llm_reasoning,
                fact_check.cross_verified_count,
                fact_check.total_sources_checked,
                Json(fact_check.similar_past_events),
                fact_check.past_accuracy_rate
            ))
            
            self.conn.commit()
            logger.debug(f"Fact check saved for article: {fact_check.article_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving fact check: {e}")
            return False
    
    def get_urgent_news(self, hours: int = 24, min_urgency: int = 4) -> List[Dict]:
        """
        긴급 뉴스 조회
        
        Args:
            hours: 조회 기간 (시간)
            min_urgency: 최소 긴급도
        """
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT * FROM v_urgent_news
                WHERE urgency_level >= %s
                  AND published_at > NOW() - INTERVAL '%s hours'
                ORDER BY published_at DESC
                LIMIT 50;
            """
            
            cursor.execute(query, (min_urgency, hours))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching urgent news: {e}")
            return []
    
    def get_stock_news(self, stock_code: str, days: int = 7) -> List[Dict]:
        """특정 종목 뉴스 조회"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT * FROM v_stock_latest_news
                WHERE stock_code = %s
                  AND published_at > NOW() - INTERVAL '%s days'
                ORDER BY published_at DESC;
            """
            
            cursor.execute(query, (stock_code, days))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching stock news: {e}")
            return []
    
    def log_crawl_job(
        self, 
        source_name: str, 
        job_type: str,
        status: str,
        items_found: int = 0,
        items_new: int = 0,
        items_duplicate: int = 0
    ) -> int:
        """크롤링 작업 로그"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                INSERT INTO crawl_jobs (
                    source_name, job_type, status,
                    items_found, items_new, items_duplicate,
                    completed_at
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    NOW()
                )
                RETURNING job_id;
            """
            
            cursor.execute(query, (
                source_name, job_type, status,
                items_found, items_new, items_duplicate
            ))
            
            job_id = cursor.fetchone()[0]
            self.conn.commit()
            
            return job_id
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error logging crawl job: {e}")
            return 0


class AlertSystem:
    """알림 시스템"""
    
    def __init__(self):
        self.channels = []
    
    def add_channel(self, channel):
        """알림 채널 추가"""
        self.channels.append(channel)
    
    def send_urgent_alert(self, article: Dict):
        """긴급 알림 전송"""
        message = self._format_urgent_message(article)
        
        for channel in self.channels:
            try:
                channel.send(message)
            except Exception as e:
                logger.error(f"Alert failed on {channel.__class__.__name__}: {e}")
    
    def _format_urgent_message(self, article: Dict) -> str:
        """긴급 알림 메시지 포맷"""
        return f"""
🚨 긴급 뉴스 알림

제목: {article['title']}
출처: {article['source']}
시간: {article['published_at']}
신뢰도: {article.get('credibility_score', 'N/A')}

{article.get('summary', '')}

URL: {article.get('url', '')}
"""


class ConsoleChannel:
    """콘솔 알림 채널"""
    
    def send(self, message: str):
        print("=" * 60)
        print(message)
        print("=" * 60)


class SlackChannel:
    """Slack 알림 채널 (구현 예시)"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str):
        """Slack 웹훅으로 전송"""
        import requests
        
        payload = {
            "text": message
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info("Slack alert sent")
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")


# ================================================================
# 통합 뉴스 서비스
# ================================================================

class NewsIngestionService:
    """뉴스 수집 통합 서비스"""
    
    def __init__(
        self, 
        db_params: Optional[Dict] = None,
        openai_api_key: Optional[str] = None,
        use_ollama: bool = False,
        ollama_model: str = 'llama3',
        enable_fact_check: bool = True,
        enable_alerts: bool = True
    ):
        """
        초기화
        
        Args:
            db_params: 데이터베이스 연결 파라미터 (None이면 DB 사용 안함)
            openai_api_key: OpenAI API 키 (팩트 체크용)
            use_ollama: Ollama 사용 여부 (True면 OpenAI 대신 Ollama 사용)
            ollama_model: Ollama 모델명
            enable_fact_check: 팩트 체크 활성화
            enable_alerts: 알림 활성화
        """
        self.crawler_manager = NewsCrawlerManager()
        
        if enable_fact_check:
            self.fact_check_engine = FactCheckEngine(
                openai_api_key=openai_api_key,
                use_ollama=use_ollama,
                ollama_model=ollama_model
            )
        else:
            self.fact_check_engine = None
        
        if db_params:
            self.database = NewsDatabase(db_params)
        else:
            self.database = None
            logger.warning("데이터베이스 파라미터가 없습니다. DB 저장 기능이 비활성화됩니다.")
        
        self.alert_system = AlertSystem() if enable_alerts else None
        if self.alert_system:
            # 기본 콘솔 채널 추가
            self.alert_system.add_channel(ConsoleChannel())
    
    def run_ingestion_cycle(self, use_llm: bool = False):
        """
        1회 수집 사이클 실행
        
        Args:
            use_llm: LLM 팩트 체크 사용 여부
        """
        logger.info("=" * 60)
        logger.info("뉴스 수집 사이클 시작")
        logger.info("=" * 60)
        
        # 1. 데이터베이스 연결 (있는 경우)
        if self.database:
            self.database.connect()
        
        # 2. 뉴스 크롤링
        logger.info("\n[1/5] 뉴스 크롤링...")
        articles = self.crawler_manager.crawl_all()
        logger.info(f"수집된 기사: {len(articles)}개")
        
        if not articles:
            logger.info("수집된 기사가 없습니다. 종료.")
            if self.database:
                self.database.disconnect()
            return
        
        # 3. 팩트 체크 (선택)
        fact_check_results = {}
        if self.fact_check_engine:
            logger.info("\n[2/5] 팩트 체크...")
            results = self.fact_check_engine.batch_verify(articles, use_llm=use_llm)
            
            # article_id 매핑 (저장 전이므로 해시로)
            for i, result in enumerate(results):
                fact_check_results[articles[i].content_hash] = result
            
            logger.info(f"팩트 체크 완료: {len(results)}개")
        
        # 4. 데이터베이스 저장 (있는 경우)
        saved_count = 0
        duplicate_count = 0
        
        if self.database:
            logger.info("\n[3/5] 데이터베이스 저장...")
            for article in articles:
                # 팩트 체크 결과 반영
                if article.content_hash in fact_check_results:
                    fact_check = fact_check_results[article.content_hash]
                    article.credibility_score = fact_check.confidence_score
                
                # 기사 저장
                article_id = self.database.save_article(article)
                
                if article_id:
                    saved_count += 1
                    
                    # 팩트 체크 결과 저장
                    if article.content_hash in fact_check_results:
                        fact_check = fact_check_results[article.content_hash]
                        fact_check.article_id = article_id
                        self.database.save_fact_check(fact_check)
                else:
                    duplicate_count += 1
            
            logger.info(f"저장 완료: {saved_count}개 (중복: {duplicate_count}개)")
        else:
            logger.info("\n[3/5] 데이터베이스 저장 건너뜀 (DB 미설정)")
        
        # 5. 긴급 알림
        if self.alert_system:
            logger.info("\n[4/5] 긴급 알림 확인...")
            if self.database:
                urgent_news = self.database.get_urgent_news(hours=1, min_urgency=4)
            else:
                # DB 없으면 긴급도 4 이상인 기사만 필터링
                urgent_news = [
                    {
                        'title': a.title,
                        'source': a.source,
                        'published_at': a.published_at,
                        'credibility_score': a.credibility_score,
                        'summary': a.summary,
                        'url': a.url
                    }
                    for a in articles if a.urgency_level >= 4
                ]
            
            for news in urgent_news:
                self.alert_system.send_urgent_alert(news)
            
            logger.info(f"긴급 알림 전송: {len(urgent_news)}개")
        
        # 6. 크롤링 로그 (DB 있는 경우)
        if self.database:
            logger.info("\n[5/5] 작업 로그...")
            for crawler in self.crawler_manager.crawlers:
                self.database.log_crawl_job(
                    source_name=crawler.source_name,
                    job_type='rss',
                    status='completed',
                    items_found=len([a for a in articles if a.source == crawler.source_name]),
                    items_new=saved_count,
                    items_duplicate=duplicate_count
                )
        
        # 7. 연결 종료
        if self.database:
            self.database.disconnect()
        
        logger.info("\n" + "=" * 60)
        logger.info("수집 사이클 완료")
        logger.info("=" * 60)
    
    def run_continuous(self, interval_minutes: int = 5):
        """
        지속적 실행 (백그라운드 서비스)
        
        Args:
            interval_minutes: 실행 간격 (분)
        """
        import time
        
        logger.info(f"지속적 실행 모드 시작 (간격: {interval_minutes}분)")
        
        while True:
            try:
                self.run_ingestion_cycle()
            except Exception as e:
                logger.error(f"수집 사이클 오류: {e}")
            
            logger.info(f"\n{interval_minutes}분 대기...")
            time.sleep(interval_minutes * 60)


# ================================================================
# 테스트 및 실행
# ================================================================

if __name__ == '__main__':
    # 데이터베이스 설정 (선택)
    DB_PARAMS = {
        'host': 'localhost',
        'port': 5432,
        'database': 'abiseu',
        'user': 'postgres',
        'password': 'your_password'  # 실제 비밀번호로 변경
    }
    
    # 서비스 초기화 (DB 없이 테스트)
    service = NewsIngestionService(
        db_params=None,  # DB 없이 테스트
        openai_api_key=None,  # LLM 미사용
        use_ollama=True,  # Ollama 사용
        ollama_model='llama3',
        enable_fact_check=True,
        enable_alerts=True
    )
    
    # 1회 실행
    print("=== 뉴스 수집 서비스 시작 ===\n")
    service.run_ingestion_cycle(use_llm=True)
    
    # 지속적 실행 (주석 해제 시)
    # service.run_continuous(interval_minutes=5)


