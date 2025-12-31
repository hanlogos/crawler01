# enhanced_rate_limiter.py
"""
향상된 속도 제한기

참고 파일의 AdaptiveRateLimiter 기능 통합
- 건강도 기반 자동 일시 중지
- 상태별 지연 시간 조절
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from enhanced_health_monitor import EnhancedHealthMonitor

class EnhancedRateLimiter:
    """
    향상된 속도 제한기
    
    사이트 건강도에 따라 자동으로 요청 속도 조절
    """
    
    def __init__(self, site_id: str, health_monitor: EnhancedHealthMonitor):
        self.site_id = site_id
        self.health = health_monitor
        
        # 기본 설정
        self.base_delay = 3.0           # 기본 지연 (초)
        self.min_delay = 1.0            # 최소 지연
        self.max_delay = 300.0          # 최대 지연 (5분)
        
        # 상태
        self.last_request_time = None
        self.paused_until: Optional[datetime] = None
        
        self.logger = logging.getLogger(f"RateLimiter.{site_id}")
    
    def wait_if_needed(self):
        """필요 시 대기"""
        
        # 1. 일시 중지 확인
        if self.paused_until:
            if datetime.now() < self.paused_until:
                wait_time = (self.paused_until - datetime.now()).total_seconds()
                self.logger.warning(f"일시 중지됨. {wait_time:.0f}초 대기")
                time.sleep(wait_time)
            
            self.paused_until = None
        
        # 2. 건강도 확인
        if self.health.should_pause():
            self._trigger_pause()
            return self.wait_if_needed()
        
        # 3. 지연 시간 계산
        delay = self._calculate_delay()
        
        # 4. 대기
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            
            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)
        
        # 5. 기록
        self.last_request_time = time.time()
    
    def _calculate_delay(self) -> float:
        """지연 시간 계산"""
        
        # 건강도 기반 지연 시간
        recommended = self.health.get_recommended_delay()
        
        # 범위 제한
        delay = max(self.min_delay, min(self.max_delay, recommended))
        
        return delay
    
    def _trigger_pause(self):
        """일시 중지 트리거"""
        
        health_metrics = self.health.get_health()
        
        if health_metrics.status == 'blocked':
            # 차단 의심: 5분 중지
            pause_duration = 300
            self.logger.error(f"차단 의심! {pause_duration}초 중지")
        
        elif health_metrics.status == 'critical':
            # 위험: 1분 중지
            pause_duration = 60
            self.logger.warning(f"위험 수준! {pause_duration}초 중지")
        
        else:
            pause_duration = 30
        
        self.paused_until = datetime.now() + timedelta(seconds=pause_duration)




