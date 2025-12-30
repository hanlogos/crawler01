# crawler_manager.py
"""
크롤러 매니저

크롤러와 모니터링 위젯을 연결하는 중간 계층
"""

import logging
from typing import Dict, Optional
from enhanced_health_monitor import EnhancedHealthMonitor
from crawler_38com import ThirtyEightComCrawler

class CrawlerManager:
    """
    크롤러 관리자
    
    크롤러와 모니터링 시스템을 통합 관리
    """
    
    def __init__(self, use_adaptive: bool = True):
        """
        초기화
        
        Args:
            use_adaptive: 대응형 크롤러 사용 여부
        """
        self.use_adaptive = use_adaptive
        
        # 건강도 모니터
        self.health_monitor = EnhancedHealthMonitor('38com')
        
        # 크롤러
        self.crawler = ThirtyEightComCrawler(
            use_adaptive=use_adaptive,
            site_domain="www.38.co.kr"
        )
        
        # 통계
        self.stats = {
            'total_collected': 0,
            'total_validated': 0,
            'consensus_count': 0,
            'active_sources': 1
        }
        
        # 크롤러 상태
        self.crawler_status = {
            'status': 'idle',
            'total': 0,
            'completed': 0,
            'failed': 0,
            'queue_size': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    def get_global_stats(self) -> Dict:
        """전체 통계 반환"""
        return self.stats
    
    def get_crawler_stats(self) -> Dict:
        """크롤러 통계 반환"""
        return self.crawler_status
    
    def update_crawler_status(self, status: str = 'idle', 
                              completed: int = 0, failed: int = 0):
        """크롤러 상태 업데이트"""
        self.crawler_status['status'] = status
        self.crawler_status['completed'] = completed
        self.crawler_status['failed'] = failed
        self.crawler_status['total'] = completed + failed
    
    def record_request(self, success: bool, response_time: float,
                      status_code: Optional[int] = None,
                      error_msg: Optional[str] = None):
        """요청 기록 (건강도 모니터에 전달)"""
        self.health_monitor.record_request(
            success=success,
            response_time=response_time,
            status_code=status_code,
            error_msg=error_msg
        )
    
    def crawl_recent_reports(self, days: int = 1, max_reports: int = 20):
        """최근 보고서 수집"""
        self.update_crawler_status('working')
        
        try:
            reports = self.crawler.crawl_recent_reports(
                days=days,
                max_reports=max_reports
            )
            
            self.stats['total_collected'] += len(reports)
            self.update_crawler_status('idle', completed=len(reports))
            
            return reports
        
        except Exception as e:
            self.logger.error(f"크롤링 실패: {e}")
            self.update_crawler_status('error', failed=1)
            return []
    
    @property
    def health_monitors(self) -> Dict[str, EnhancedHealthMonitor]:
        """건강도 모니터 목록"""
        return {'38com': self.health_monitor}
    
    def get_crawler_as_avatar(self):
        """크롤러를 아바타처럼 반환 (위젯 호환성)"""
        class CrawlerAvatar:
            def __init__(self, manager):
                self.manager = manager
            
            def get_stats(self):
                return self.manager.get_crawler_stats()
        
        return CrawlerAvatar(self)


