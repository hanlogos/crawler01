"""
Analyst Report Pipeline
애널리스트 리포트 수집 → 정규화 → 저장 파이프라인

계약:
- 입력: ReportMetadata 객체 리스트
- 출력: 저장된 리포트 수 (int)
- 예외: ValueError (필수 필드 누락), psycopg2.Error (DB 오류)
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from korea_normalize import normalize_report_metadata
from analyst_snapshot_store import AnalystSnapshotStore

logger = logging.getLogger(__name__)


class AnalystReportPipeline:
    """
    애널리스트 리포트 파이프라인
    
    크롤러 → 정규화 → PostgreSQL 저장
    
    사용법:
        pipeline = AnalystReportPipeline(db_params)
        saved_count = pipeline.process_reports(reports, source='naver')
    """
    
    def __init__(
        self,
        db_params: Optional[Dict[str, str]] = None,
        enable_db: bool = True
    ):
        """
        초기화
        
        Args:
            db_params: PostgreSQL 연결 파라미터
                {
                    'host': 'localhost',
                    'database': 'crawler_db',
                    'user': 'postgres',
                    'password': os.getenv('DB_PASSWORD')
                }
                None이면 환경변수에서 자동 로드
            enable_db: DB 저장 활성화 여부 (기본값: True)
        """
        self.enable_db = enable_db
        self.db_params = db_params or self._load_db_params()
        self.store = None
        
        if self.enable_db and self.db_params:
            try:
                self.store = AnalystSnapshotStore(self.db_params)
                logger.info("PostgreSQL 저장소 초기화 완료")
            except Exception as e:
                logger.warning(f"PostgreSQL 저장소 초기화 실패: {e}. DB 저장 비활성화.")
                self.enable_db = False
    
    def _load_db_params(self) -> Dict[str, str]:
        """
        환경변수에서 DB 파라미터 로드
        
        Returns:
            Dict: DB 연결 파라미터
        """
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'crawler_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    def process_reports(
        self,
        reports: List[Any],
        source: str = 'auto',
        skip_errors: bool = True
    ) -> int:
        """
        리포트 리스트 처리 (정규화 + 저장)
        
        Args:
            reports: ReportMetadata 객체 리스트
            source: 소스 타입 ('auto', '38com', 'hankyung', 'naver')
                'auto'이면 report의 source 필드로 자동 판단
            skip_errors: 오류 발생 시 건너뛰기 여부 (기본값: True)
        
        Returns:
            int: 저장된 리포트 수
            
        Raises:
            ValueError: 필수 필드 누락 (skip_errors=False일 때)
            psycopg2.Error: 데이터베이스 오류 (skip_errors=False일 때)
        """
        if not reports:
            logger.warning("처리할 리포트가 없습니다.")
            return 0
        
        saved_count = 0
        error_count = 0
        
        logger.info(f"📊 리포트 처리 시작: {len(reports)}개 (소스: {source})")
        
        for i, report in enumerate(reports, 1):
            try:
                # dict로 변환
                if hasattr(report, 'to_dict'):
                    raw_data = report.to_dict()
                elif isinstance(report, dict):
                    raw_data = report
                else:
                    raise ValueError(f"Unsupported report type: {type(report)}")
                
                # 정규화
                snapshot = normalize_report_metadata(raw_data, source=source)
                
                # DB 저장
                if self.enable_db and self.store:
                    with self.store:
                        report_id = self.store.upsert_snapshot(snapshot)
                        logger.debug(f"[{i}/{len(reports)}] 저장 완료: {report_id} ({snapshot.get('stock_code')})")
                        saved_count += 1
                else:
                    # DB 저장 비활성화 시에도 정규화는 수행
                    logger.debug(f"[{i}/{len(reports)}] 정규화 완료 (DB 저장 비활성화): {snapshot.get('stock_code')}")
                    saved_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"리포트 처리 실패 [{i}/{len(reports)}]: {e}"
                
                if skip_errors:
                    logger.warning(error_msg)
                    continue
                else:
                    logger.error(error_msg)
                    raise
        
        logger.info(f"✅ 처리 완료: {saved_count}개 저장, {error_count}개 오류")
        return saved_count
    
    def get_consensus(
        self,
        stock_code: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        컨센서스 조회
        
        Args:
            stock_code: 종목 코드
            days: 집계 기간 (일)
        
        Returns:
            Optional[Dict]: 컨센서스 스냅샷 (리포트 없으면 None)
        """
        if not self.enable_db or not self.store:
            logger.warning("DB 저장소가 활성화되지 않았습니다.")
            return None
        
        try:
            with self.store:
                consensus = self.store.fetch_consensus(stock_code, days=days)
                return consensus
        except Exception as e:
            logger.error(f"컨센서스 조회 실패: {e}")
            return None
    
    def get_latest_reports(
        self,
        stock_code: str,
        source: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        최신 리포트 조회
        
        Args:
            stock_code: 종목 코드
            source: 소스 필터 (옵션)
            limit: 최대 결과 수
        
        Returns:
            List[Dict]: 스냅샷 리스트
        """
        if not self.enable_db or not self.store:
            logger.warning("DB 저장소가 활성화되지 않았습니다.")
            return []
        
        try:
            with self.store:
                reports = self.store.fetch_latest(stock_code, source=source, limit=limit)
                return reports
        except Exception as e:
            logger.error(f"리포트 조회 실패: {e}")
            return []


if __name__ == '__main__':
    # 테스트
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 더미 리포트 생성
    from dataclasses import dataclass
    from datetime import datetime
    
    @dataclass
    class TestReport:
        stock_code: str
        stock_name: str
        published_date: datetime
        analyst_name: str
        firm: str
        investment_opinion: str
        target_price: int
        source_url: str
        source: str = "naver"
        
        def to_dict(self):
            return {
                'stock_code': self.stock_code,
                'stock_name': self.stock_name,
                'published_date': self.published_date.isoformat(),
                'analyst_name': self.analyst_name,
                'analyst_firm': self.firm,
                'investment_opinion': self.investment_opinion,
                'target_price': self.target_price,
                'source_url': self.source_url,
                'source': self.source
            }
    
    test_reports = [
        TestReport(
            stock_code='005930',
            stock_name='삼성전자',
            published_date=datetime.now(),
            analyst_name='홍길동',
            firm='KB증권',
            investment_opinion='매수',
            target_price=95000,
            source_url='https://finance.naver.com/research/test1',
            source='naver'
        ),
        TestReport(
            stock_code='005930',
            stock_name='삼성전자',
            published_date=datetime.now(),
            analyst_name='김철수',
            firm='NH투자증권',
            investment_opinion='매수(강력)',
            target_price=98000,
            source_url='https://finance.naver.com/research/test2',
            source='naver'
        )
    ]
    
    # 파이프라인 실행
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'crawler_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    pipeline = AnalystReportPipeline(db_params, enable_db=False)  # DB 비활성화로 테스트
    saved = pipeline.process_reports(test_reports, source='naver')
    print(f"\n저장된 리포트: {saved}개")

