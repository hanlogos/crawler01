# enhanced_health_monitor.py
"""
향상된 건강도 모니터

참고 파일의 SiteHealthMonitor 기능을 통합
- 더 상세한 건강도 추적
- 상태 기반 자동 대응
- 오류 패턴 분석
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import logging

@dataclass
class HealthMetrics:
    """건강도 메트릭"""
    success_rate: float          # 성공률 (0-1)
    avg_response_time: float     # 평균 응답 시간 (초)
    error_count_1h: int          # 최근 1시간 오류 수
    last_success: Optional[datetime]  # 마지막 성공 시간
    consecutive_errors: int      # 연속 오류 수
    status: str                  # 'healthy', 'degraded', 'critical', 'blocked'

class EnhancedHealthMonitor:
    """
    향상된 건강도 모니터
    
    각 사이트의 상태를 실시간 추적하고
    문제 발생 시 자동으로 대응
    """
    
    def __init__(self, site_id: str):
        self.site_id = site_id
        
        # 최근 요청 기록 (최대 100개)
        self.recent_requests = deque(maxlen=100)
        
        # 에러 기록 (최근 1시간)
        self.recent_errors = deque(maxlen=50)
        
        # 통계
        self.total_requests = 0
        self.total_successes = 0
        self.total_errors = 0
        
        self.logger = logging.getLogger(f"HealthMonitor.{site_id}")
    
    def record_request(
        self, 
        success: bool, 
        response_time: float,
        status_code: Optional[int] = None,
        error_msg: Optional[str] = None
    ):
        """요청 기록"""
        
        now = datetime.now()
        
        request = {
            'timestamp': now,
            'success': success,
            'response_time': response_time,
            'status_code': status_code,
            'error_msg': error_msg
        }
        
        self.recent_requests.append(request)
        self.total_requests += 1
        
        if success:
            self.total_successes += 1
        else:
            self.total_errors += 1
            self.recent_errors.append(request)
    
    def get_health(self) -> HealthMetrics:
        """현재 건강도 계산"""
        
        if not self.recent_requests:
            return HealthMetrics(
                success_rate=0,
                avg_response_time=0,
                error_count_1h=0,
                last_success=None,
                consecutive_errors=0,
                status='unknown'
            )
        
        # 1. 성공률
        recent_100 = list(self.recent_requests)
        successes = sum(1 for r in recent_100 if r['success'])
        success_rate = successes / len(recent_100) if recent_100 else 0
        
        # 2. 평균 응답 시간
        response_times = [r['response_time'] for r in recent_100 if r['success']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 3. 최근 1시간 오류
        one_hour_ago = datetime.now() - timedelta(hours=1)
        error_count_1h = sum(
            1 for e in self.recent_errors 
            if e['timestamp'] > one_hour_ago
        )
        
        # 4. 마지막 성공
        successful_requests = [r for r in recent_100 if r['success']]
        last_success = successful_requests[-1]['timestamp'] if successful_requests else None
        
        # 5. 연속 오류
        consecutive_errors = 0
        for r in reversed(recent_100):
            if not r['success']:
                consecutive_errors += 1
            else:
                break
        
        # 6. 상태 결정
        status = self._determine_status(
            success_rate,
            consecutive_errors,
            error_count_1h,
            last_success
        )
        
        return HealthMetrics(
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            error_count_1h=error_count_1h,
            last_success=last_success,
            consecutive_errors=consecutive_errors,
            status=status
        )
    
    def _determine_status(
        self,
        success_rate: float,
        consecutive_errors: int,
        error_count_1h: int,
        last_success: Optional[datetime]
    ) -> str:
        """상태 결정"""
        
        # 차단 의심
        if consecutive_errors >= 5:
            return 'blocked'
        
        # 위험
        if success_rate < 0.5 or error_count_1h > 20:
            return 'critical'
        
        # 성능 저하
        if success_rate < 0.8 or error_count_1h > 10:
            return 'degraded'
        
        # 정상
        return 'healthy'
    
    def should_pause(self) -> bool:
        """일시 중지 필요 여부"""
        
        health = self.get_health()
        
        # 차단 의심 시 즉시 중지
        if health.status == 'blocked':
            return True
        
        # 위험 수준 시 중지
        if health.status == 'critical':
            return True
        
        return False
    
    def get_recommended_delay(self) -> float:
        """권장 지연 시간 (초)"""
        
        health = self.get_health()
        
        # 상태별 지연 시간
        if health.status == 'blocked':
            return 300.0  # 5분
        
        elif health.status == 'critical':
            return 60.0   # 1분
        
        elif health.status == 'degraded':
            return 10.0   # 10초
        
        else:  # healthy
            return 3.0    # 3초
    
    def get_error_patterns(self) -> Dict[str, int]:
        """오류 패턴 분석"""
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e for e in self.recent_errors 
            if e['timestamp'] > one_hour_ago
        ]
        
        # 상태 코드별 집계
        status_codes = {}
        
        for error in recent_errors:
            code = error.get('status_code', 'unknown')
            status_codes[str(code)] = status_codes.get(str(code), 0) + 1
        
        return status_codes


