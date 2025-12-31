"""
PostgreSQL Analyst Snapshot Storage
한국 애널리스트 리포트 스냅샷 저장/조회

계약:
- 입력: snapshot (Dict, KoreaAnalystSnapshot v1 형식)
- 출력: report_id (str, UUID) 또는 스냅샷 리스트
- 예외: psycopg2.Error (DB 오류), ValueError (필수 필드 누락)
"""

import psycopg2
import psycopg2.extras
import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, date
import os

logger = logging.getLogger(__name__)


class AnalystSnapshotStore:
    """
    애널리스트 스냅샷 PostgreSQL 저장소
    
    사용법:
        conn_params = {
            'host': 'localhost',
            'database': 'crawler_db',
            'user': 'postgres',
            'password': os.getenv('DB_PASSWORD')
        }
        
        with AnalystSnapshotStore(conn_params) as store:
            report_id = store.upsert_snapshot(snapshot)
            consensus = store.fetch_consensus('005930', days=30)
    """
    
    def __init__(self, connection_params: Dict[str, str]):
        """
        초기화
        
        Args:
            connection_params: PostgreSQL 연결 파라미터
                {
                    'host': 'localhost',
                    'database': 'crawler_db',
                    'user': 'postgres',
                    'password': 'password'
                }
        
        Raises:
            psycopg2.Error: 데이터베이스 연결 실패
        """
        self.conn_params = connection_params
        self._conn = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> psycopg2.extensions.connection:
        """
        데이터베이스 연결
        
        Returns:
            psycopg2.extensions.connection: 데이터베이스 연결 객체
            
        Raises:
            psycopg2.Error: 연결 실패
        """
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(**self.conn_params)
                # 자동 커밋 비활성화 (명시적 트랜잭션 관리)
                self._conn.autocommit = False
                self.logger.info("PostgreSQL 연결 성공")
            except psycopg2.Error as e:
                self.logger.error(f"PostgreSQL 연결 실패: {e}")
                raise
        return self._conn
    
    def close(self):
        """연결 종료"""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None
            self.logger.info("PostgreSQL 연결 종료")
    
    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        if exc_type is None:
            if self._conn:
                self._conn.commit()
        else:
            if self._conn:
                self._conn.rollback()
        self.close()
    
    def upsert_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """
        스냅샷 저장 또는 업데이트
        
        Args:
            snapshot: KoreaAnalystSnapshot v1 형식 데이터
                - 필수 키: 'stock_code', 'source', 'raw_refs'
                - 'raw_refs' 내부에 'source_url' 필수
        
        Returns:
            str: report_id (UUID 문자열)
            
        Raises:
            ValueError: source_url 누락 또는 필수 필드 누락
            psycopg2.Error: 데이터베이스 오류
            
        계약:
        - 입력: snapshot은 Dict, 필수 키 포함
        - 출력: UUID 문자열 (report_id)
        - 예외: ValueError (필수 필드), psycopg2.Error (DB 오류)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # source_url을 unique key로 사용 (중복 방지)
            raw_refs = snapshot.get('raw_refs', {})
            source_url = raw_refs.get('source_url')
            
            if not source_url:
                raise ValueError("source_url is required in raw_refs for upsert")
            
            # 기존 레코드 확인
            cursor.execute(
                "SELECT report_id FROM analyst_reports WHERE source_url = %s",
                (source_url,)
            )
            existing = cursor.fetchone()
            
            # 데이터 매핑
            stock_code = snapshot.get('stock_code', '').strip()
            stock_name = snapshot.get('stock_name')
            source = snapshot.get('source', 'unknown')
            asof = snapshot.get('asof')
            
            # 날짜 파싱
            if isinstance(asof, str):
                try:
                    published_date = datetime.strptime(asof, '%Y-%m-%d').date()
                except:
                    published_date = date.today()
            elif isinstance(asof, date):
                published_date = asof
            elif isinstance(asof, datetime):
                published_date = asof.date()
            else:
                published_date = date.today()
            
            recommendation = snapshot.get('recommendation', {})
            price_target = snapshot.get('price_target', {})
            valuation = snapshot.get('valuation', {})
            confidence = snapshot.get('confidence', {})
            analyst_info = snapshot.get('analyst_info', {})
            
            # structured_data 구성 (전체 스냅샷 저장)
            structured_data = {
                'recommendation': recommendation,
                'price_target': price_target,
                'valuation': valuation,
                'confidence': confidence,
                'version': snapshot.get('version', 'v1'),
                'market': snapshot.get('market'),
                'analyst_info': analyst_info
            }
            
            # opinion (rating_text)
            opinion = recommendation.get('rating_text')
            
            # target_price (mean)
            target_price = price_target.get('mean')
            if target_price is not None:
                try:
                    target_price = float(target_price)
                except (ValueError, TypeError):
                    target_price = None
            
            # trust_score (source_quality)
            trust_score = confidence.get('source_quality', 0.0)
            
            # analyst_name, analyst_firm
            analyst_name = analyst_info.get('name') if analyst_info else None
            analyst_firm = analyst_info.get('firm') if analyst_info else None
            
            if existing:
                # UPDATE
                report_id = existing[0]
                cursor.execute("""
                    UPDATE analyst_reports SET
                        stock_code = %s,
                        stock_name = %s,
                        published_at = %s,
                        opinion = %s,
                        target_price = %s,
                        analyst_name = %s,
                        analyst_firm = %s,
                        trust_score = %s,
                        structured_data = %s,
                        updated_at = NOW()
                    WHERE report_id = %s
                """, (
                    stock_code,
                    stock_name,
                    published_date,
                    opinion,
                    target_price,
                    analyst_name,
                    analyst_firm,
                    trust_score,
                    json.dumps(structured_data, ensure_ascii=False),
                    report_id
                ))
                self.logger.info(f"리포트 업데이트: {report_id} ({stock_code})")
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO analyst_reports (
                        source,
                        source_url,
                        stock_code,
                        stock_name,
                        market,
                        published_at,
                        opinion,
                        target_price,
                        analyst_name,
                        analyst_firm,
                        trust_score,
                        structured_data,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    RETURNING report_id
                """, (
                    source,
                    source_url,
                    stock_code,
                    stock_name,
                    snapshot.get('market'),
                    published_date,
                    opinion,
                    target_price,
                    analyst_name,
                    analyst_firm,
                    trust_score,
                    json.dumps(structured_data, ensure_ascii=False)
                ))
                report_id = cursor.fetchone()[0]
                self.logger.info(f"리포트 저장: {report_id} ({stock_code})")
            
            conn.commit()
            return str(report_id)
        
        except Exception as e:
            conn.rollback()
            self.logger.error(f"스냅샷 저장 실패: {e}")
            raise
        finally:
            cursor.close()
    
    def fetch_latest(
        self,
        stock_code: str,
        source: Optional[str] = None,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        최신 스냅샷 조회
        
        Args:
            stock_code: 종목 코드 (6자리)
            source: 소스 필터 (옵션, 기본값: None)
            limit: 최대 결과 수 (기본값: 1)
        
        Returns:
            List[Dict]: 스냅샷 리스트 (KoreaAnalystSnapshot v1 형식)
            
        Raises:
            psycopg2.Error: 데이터베이스 오류
        """
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            if source:
                cursor.execute("""
                    SELECT
                        report_id,
                        source,
                        source_url,
                        stock_code,
                        stock_name,
                        published_at,
                        opinion,
                        target_price,
                        analyst_name,
                        analyst_firm,
                        trust_score,
                        structured_data
                    FROM analyst_reports
                    WHERE stock_code = %s AND source = %s
                    ORDER BY published_at DESC
                    LIMIT %s
                """, (stock_code, source, limit))
            else:
                cursor.execute("""
                    SELECT
                        report_id,
                        source,
                        source_url,
                        stock_code,
                        stock_name,
                        published_at,
                        opinion,
                        target_price,
                        analyst_name,
                        analyst_firm,
                        trust_score,
                        structured_data
                    FROM analyst_reports
                    WHERE stock_code = %s
                    ORDER BY published_at DESC
                    LIMIT %s
                """, (stock_code, limit))
            
            rows = cursor.fetchall()
            
            # 스냅샷 형식으로 변환
            snapshots = []
            for row in rows:
                structured = row['structured_data'] if row['structured_data'] else {}
                
                snapshot = {
                    'version': structured.get('version', 'v1'),
                    'asof': row['published_at'].strftime('%Y-%m-%d') if row['published_at'] else None,
                    'stock_code': row['stock_code'],
                    'stock_name': row['stock_name'],
                    'source': row['source'],
                    'market': structured.get('market'),
                    'recommendation': structured.get('recommendation', {}),
                    'price_target': structured.get('price_target', {}),
                    'valuation': structured.get('valuation', {}),
                    'confidence': structured.get('confidence', {}),
                    'raw_refs': {
                        'source_url': row['source_url'],
                        'report_id': str(row['report_id'])
                    }
                }
                
                # 애널리스트 정보 추가
                analyst_info = structured.get('analyst_info')
                if analyst_info or (row['analyst_name'] or row['analyst_firm']):
                    snapshot['analyst_info'] = analyst_info or {
                        'name': row['analyst_name'],
                        'firm': row['analyst_firm']
                    }
                
                snapshots.append(snapshot)
            
            return snapshots
        
        finally:
            cursor.close()
    
    def fetch_consensus(
        self,
        stock_code: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        컨센서스 계산 (최근 N일 리포트 집계)
        
        Args:
            stock_code: 종목 코드
            days: 집계 기간 (일, 기본값: 30)
        
        Returns:
            Optional[Dict]: 컨센서스 스냅샷 (KoreaAnalystSnapshot v1 형식)
                리포트가 없으면 None
        
        Raises:
            psycopg2.Error: 데이터베이스 오류
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # 최근 N일 리포트 조회
            cursor.execute("""
                SELECT
                    COUNT(*) as total_reports,
                    AVG(target_price) as avg_target,
                    MIN(target_price) as min_target,
                    MAX(target_price) as max_target,
                    AVG(trust_score) as avg_trust,
                    MAX(published_at) as latest_date
                FROM analyst_reports
                WHERE stock_code = %s
                  AND published_at >= CURRENT_DATE - INTERVAL '%s days'
                  AND target_price IS NOT NULL
            """, (stock_code, days))
            
            result = cursor.fetchone()
            
            if not result or result[0] == 0:
                return None
            
            # 의견 분포 조회
            cursor.execute("""
                SELECT
                    opinion,
                    COUNT(*) as count
                FROM analyst_reports
                WHERE stock_code = %s
                  AND published_at >= CURRENT_DATE - INTERVAL '%s days'
                  AND opinion IS NOT NULL
                GROUP BY opinion
            """, (stock_code, days))
            
            opinion_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 정규화된 의견 분포 생성
            recommendation = {
                'strong_buy': opinion_dist.get('Strong Buy', 0),
                'buy': opinion_dist.get('Buy', 0),
                'hold': opinion_dist.get('Hold', 0),
                'sell': opinion_dist.get('Sell', 0),
                'strong_sell': opinion_dist.get('Strong Sell', 0),
                'rating_text': self._determine_consensus_rating(opinion_dist),
                'analyst_count': result[0]
            }
            
            # 종목명 조회
            cursor.execute("""
                SELECT DISTINCT stock_name 
                FROM analyst_reports 
                WHERE stock_code = %s 
                LIMIT 1
            """, (stock_code,))
            stock_name_result = cursor.fetchone()
            stock_name = stock_name_result[0] if stock_name_result else None
            
            # 컨센서스 스냅샷 생성
            consensus = {
                'version': 'v1',
                'asof': result[5].strftime('%Y-%m-%d') if result[5] else None,
                'stock_code': stock_code,
                'stock_name': stock_name,
                'source': 'consensus',
                'recommendation': recommendation,
                'price_target': {
                    'low': float(result[2]) if result[2] else None,
                    'mean': float(result[1]) if result[1] else None,
                    'high': float(result[3]) if result[3] else None,
                    'median': None,  # 별도 계산 필요
                    'currency': 'KRW',
                    'horizon_months': 12
                },
                'valuation': {
                    'fair_value': float(result[1]) if result[1] else None,
                    'price_to_fair_value': None
                },
                'confidence': {
                    'source_quality': float(result[4]) if result[4] else 0.0,
                    'freshness_days': 0,
                    'coverage_score': min(1.0, result[0] / 20.0)  # 20개 리포트 = 1.0
                },
                'raw_refs': {
                    'source_url': None,
                    'report_id': None
                }
            }
            
            return consensus
        
        finally:
            cursor.close()
    
    def _determine_consensus_rating(self, opinion_dist: Dict[str, int]) -> str:
        """
        의견 분포에서 컨센서스 등급 결정
        
        Args:
            opinion_dist: 의견별 리포트 수 {'Strong Buy': 5, 'Buy': 10, ...}
        
        Returns:
            str: 컨센서스 등급 ('Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell')
        """
        total = sum(opinion_dist.values())
        if total == 0:
            return 'Hold'
        
        # 가중치 부여
        score = 0
        for opinion, count in opinion_dist.items():
            if 'Strong' in opinion:
                if 'Buy' in opinion:
                    score += count * 2
                elif 'Sell' in opinion:
                    score -= count * 2
            elif 'Buy' in opinion:
                score += count * 1
            elif 'Sell' in opinion:
                score -= count * 1
        
        avg = score / total
        
        if avg >= 1.2:
            return 'Strong Buy'
        elif avg >= 0.4:
            return 'Buy'
        elif avg > -0.4:
            return 'Hold'
        elif avg > -1.2:
            return 'Sell'
        else:
            return 'Strong Sell'


if __name__ == '__main__':
    # 사용 예시
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'crawler_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    try:
        with AnalystSnapshotStore(conn_params) as store:
            # 더미 스냅샷 저장 테스트
            snapshot = {
                'version': 'v1',
                'asof': '2025-12-31',
                'stock_code': '005930',
                'stock_name': '삼성전자',
                'source': 'naver',
                'recommendation': {
                    'strong_buy': 5,
                    'buy': 10,
                    'hold': 3,
                    'sell': 1,
                    'strong_sell': 0,
                    'rating_text': 'Buy',
                    'analyst_count': 19
                },
                'price_target': {
                    'low': 85000,
                    'mean': 95000,
                    'high': 110000,
                    'median': 96000,
                    'currency': 'KRW',
                    'horizon_months': 12
                },
                'valuation': {
                    'fair_value': 95000,
                    'price_to_fair_value': None
                },
                'confidence': {
                    'source_quality': 0.85,
                    'freshness_days': 0,
                    'coverage_score': 0.95
                },
                'raw_refs': {
                    'source_url': 'https://finance.naver.com/research/example/12345',
                    'pdf_url': None,
                    'report_id': '12345'
                }
            }
            
            report_id = store.upsert_snapshot(snapshot)
            print(f"Saved report_id: {report_id}")
            
            # 조회 테스트
            latest = store.fetch_latest('005930', limit=5)
            print(f"\nFound {len(latest)} reports for 005930")
            
            # 컨센서스 조회
            consensus = store.fetch_consensus('005930', days=30)
            if consensus:
                print(f"\nConsensus: {consensus['recommendation']['rating_text']}")
                print(f"Target: {consensus['price_target']['mean']:,.0f} KRW")
    
    except Exception as e:
        print(f"Error: {e}")


