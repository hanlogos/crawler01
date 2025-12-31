# integrated_research_crawler.py
"""
통합 리서치 크롤러

한경 컨센서스 + 네이버 금융 리서치를 통합하여 수집

계약:
- 입력: stock_name (str, 종목명), stock_code (Optional[str], 종목코드), days (int, 최근 N일)
- 출력: Dict with keys: 'reports', 'scores', 'consensus'
- 예외: ValueError (잘못된 파라미터), ImportError (의존성 모듈 없음), requests.RequestException (네트워크 오류)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

try:
    from crawler_hankyung_consensus import HankyungConsensusCrawler
    HANKYUNG_AVAILABLE = True
except ImportError:
    HANKYUNG_AVAILABLE = False
    HankyungConsensusCrawler = None

try:
    from crawler_naver_finance_research import NaverFinanceResearchCrawler
    NAVER_AVAILABLE = True
except ImportError:
    NAVER_AVAILABLE = False
    NaverFinanceResearchCrawler = None

try:
    from analyst_report_scorer import AnalystReportScorer
    SCORER_AVAILABLE = True
except ImportError:
    SCORER_AVAILABLE = False
    AnalystReportScorer = None

class IntegratedResearchCrawler:
    """
    통합 리서치 크롤러
    
    한경 컨센서스와 네이버 금융 리서치를 통합하여 수집하고 점수화
    
    사용법:
        crawler = IntegratedResearchCrawler()
        reports = crawler.collect_stock_reports("삼성전자", "005930", days=7)
        
        # 점수화 포함
        scored_reports = crawler.collect_and_score("삼성전자", "005930", days=7)
    """
    
    def __init__(
        self,
        use_hankyung: bool = True,
        use_naver: bool = True,
        download_pdf: bool = False,
        download_dir: str = "AnalystReports"
    ):
        """
        초기화
        
        Args:
            use_hankyung: 한경 컨센서스 사용 여부
            use_naver: 네이버 금융 사용 여부
            download_pdf: PDF 다운로드 여부
            download_dir: 다운로드 디렉토리
        """
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.use_hankyung = use_hankyung and HANKYUNG_AVAILABLE
        self.use_naver = use_naver and NAVER_AVAILABLE
        self.download_pdf = download_pdf
        self.download_dir = download_dir
        
        # 크롤러 초기화
        self.hankyung_crawler = None
        if self.use_hankyung:
            try:
                self.hankyung_crawler = HankyungConsensusCrawler()
                self.logger.info("✅ 한경 컨센서스 크롤러 초기화 완료")
            except Exception as e:
                self.logger.warning(f"⚠️  한경 컨센서스 크롤러 초기화 실패: {e}")
                self.use_hankyung = False
        
        self.naver_crawler = None
        if self.use_naver:
            try:
                self.naver_crawler = NaverFinanceResearchCrawler(
                    download_dir=download_dir
                )
                self.logger.info("✅ 네이버 금융 리서치 크롤러 초기화 완료")
            except Exception as e:
                self.logger.warning(f"⚠️  네이버 금융 리서치 크롤러 초기화 실패: {e}")
                self.use_naver = False
        
        # 점수화 시스템
        self.scorer = None
        if SCORER_AVAILABLE:
            try:
                self.scorer = AnalystReportScorer()
                self.logger.info("✅ 리포트 점수화 시스템 초기화 완료")
            except Exception as e:
                self.logger.warning(f"⚠️  점수화 시스템 초기화 실패: {e}")
    
    def collect_stock_reports(
        self,
        stock_name: str,
        stock_code: Optional[str] = None,
        days: int = 7,
        max_reports: int = 100
    ) -> List[Dict]:
        """
        종목 리포트 수집 (통합)
        
        Args:
            stock_name: 종목명 (예: "삼성전자")
            stock_code: 종목코드 (None이면 자동 검색, 기본값: None)
            days: 최근 N일 (기본값: 7)
            max_reports: 최대 수집 개수 (기본값: 100)
            
        Returns:
            List[Dict]: 리포트 메타데이터 리스트 (dict 형식)
                - 각 dict는 ReportMetadata.to_dict() 결과와 동일한 구조
            
        Raises:
            ValueError: 잘못된 stock_name 또는 days < 0
            ImportError: 필요한 크롤러 모듈을 찾을 수 없음
            requests.RequestException: 네트워크 오류 또는 페이지 조회 실패
            
        계약:
        - 입력: stock_name은 비어있지 않은 문자열, days는 양수
        - 출력: Dict 리스트 (빈 리스트 가능, 중복 제거됨)
        - 예외: ValueError (잘못된 파라미터), ImportError (의존성 없음), RequestException (네트워크 오류)
        """
        
        # 입력 검증
        if not stock_name or not isinstance(stock_name, str):
            raise ValueError(f"stock_name must be a non-empty string, got {stock_name}")
        if days < 0:
            raise ValueError(f"days must be non-negative, got {days}")
        if max_reports < 0:
            raise ValueError(f"max_reports must be non-negative, got {max_reports}")
        
        self.logger.info(f"🔍 통합 리서치 수집 시작: {stock_name} ({stock_code})")
        
        all_reports = []
        
        # 1. 네이버 금융 수집 (우선순위 1)
        if self.use_naver and self.naver_crawler:
            try:
                self.logger.info("📊 네이버 금융 리서치 수집 중...")
                naver_reports = self.naver_crawler.search_by_stock(
                    stock_name=stock_name,
                    stock_code=stock_code,
                    days=days,
                    max_reports=max_reports,
                    download_pdf=self.download_pdf
                )
                
                # dict로 변환
                for report in naver_reports:
                    report_dict = report.to_dict() if hasattr(report, 'to_dict') else report
                    all_reports.append(report_dict)
                
                self.logger.info(f"✅ 네이버 금융: {len(naver_reports)}개 수집")
                
            except Exception as e:
                self.logger.error(f"❌ 네이버 금융 수집 실패: {e}")
        
        # 2. 한경 컨센서스 수집 (보조)
        if self.use_hankyung and self.hankyung_crawler:
            try:
                self.logger.info("📊 한경 컨센서스 수집 중...")
                hankyung_reports = self.hankyung_crawler.search_by_stock(
                    stock_name=stock_name,
                    days=days,
                    max_reports=max_reports
                )
                
                # dict로 변환
                for report in hankyung_reports:
                    report_dict = report.to_dict() if hasattr(report, 'to_dict') else report
                    # 중복 제거 (URL 기반)
                    if not any(r.get('source_url') == report_dict.get('source_url') for r in all_reports):
                        all_reports.append(report_dict)
                
                self.logger.info(f"✅ 한경 컨센서스: {len(hankyung_reports)}개 수집")
                
            except Exception as e:
                self.logger.error(f"❌ 한경 컨센서스 수집 실패: {e}")
        
        # 중복 제거 (report_id 기반)
        seen_ids = set()
        unique_reports = []
        for report in all_reports:
            report_id = report.get('report_id', '')
            if report_id and report_id not in seen_ids:
                seen_ids.add(report_id)
                unique_reports.append(report)
        
        self.logger.info(f"🎉 통합 수집 완료: {len(unique_reports)}개 (중복 제거 후)")
        
        return unique_reports
    
    def collect_and_score(
        self,
        stock_name: str,
        stock_code: Optional[str] = None,
        days: int = 7,
        max_reports: int = 100
    ) -> Dict:
        """
        리포트 수집 및 점수화
        
        Returns:
            {
                'reports': List[Dict],  # 원본 리포트
                'scores': List[ReportScore],  # 점수화된 리포트
                'consensus': Dict  # 컨센서스 정보
            }
        """
        
        # 리포트 수집
        reports = self.collect_stock_reports(
            stock_name=stock_name,
            stock_code=stock_code,
            days=days,
            max_reports=max_reports
        )
        
        if not reports:
            return {
                'reports': [],
                'scores': [],
                'consensus': {}
            }
        
        # 점수화
        scores = []
        if self.scorer:
            try:
                scores = self.scorer.score_multiple_reports(reports)
                self.logger.info(f"✅ 점수화 완료: {len(scores)}개")
            except Exception as e:
                self.logger.error(f"❌ 점수화 실패: {e}")
        
        # 컨센서스 계산
        consensus = {}
        if self.scorer and stock_code:
            try:
                consensus = self.scorer.get_stock_consensus_score(stock_code, days=days)
            except Exception as e:
                self.logger.error(f"❌ 컨센서스 계산 실패: {e}")
        
        return {
            'reports': reports,
            'scores': [s.to_dict() if hasattr(s, 'to_dict') else s for s in scores],
            'consensus': consensus
        }
    
    def save_summary(
        self,
        stock_name: str,
        stock_code: str,
        result: Dict,
        filename: Optional[str] = None
    ):
        """수집 결과 요약 저장"""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"research_summary_{stock_name}_{stock_code}_{timestamp}.json"
        
        summary = {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'collected_at': datetime.now().isoformat(),
            'reports': result.get('reports', []),
            'scores': result.get('scores', []),
            'consensus': result.get('consensus', {})
        }
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 요약 저장 완료: {filename}")

# ============================================================
# 사용 예제
# ============================================================

def main():
    """메인 함수"""
    
    crawler = IntegratedResearchCrawler(
        use_hankyung=True,
        use_naver=True,
        download_pdf=True
    )
    
    print("🚀 통합 리서치 크롤러 시작\n")
    
    # 삼성전자 리포트 수집 및 점수화
    result = crawler.collect_and_score(
        stock_name="삼성전자",
        stock_code="005930",
        days=7,
        max_reports=50
    )
    
    print(f"\n📊 수집 결과:")
    print(f"  리포트 수: {len(result['reports'])}개")
    print(f"  점수화된 리포트: {len(result['scores'])}개")
    
    if result['consensus']:
        consensus = result['consensus']
        print(f"\n📈 컨센서스:")
        print(f"  총 점수: {consensus.get('total_score', 0):.2f}")
        print(f"  평균 점수: {consensus.get('average_score', 0):.2f}")
        print(f"  BUY: {consensus.get('buy_count', 0)}개")
        print(f"  HOLD: {consensus.get('hold_count', 0)}개")
        print(f"  SELL: {consensus.get('sell_count', 0)}개")
    
    # 요약 저장
    crawler.save_summary("삼성전자", "005930", result)
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

