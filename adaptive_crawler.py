# adaptive_crawler.py
"""
대응형 크롤러 시스템

웹사이트 규제를 피하고 안정적으로 크롤링하기 위한 AI 로직
- 사전 테스트 및 검증
- 차단 감지 및 대응
- 동적 요청 간격 조절
- 사이트별 프로필 관리
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import json
from pathlib import Path
import requests
from urllib.parse import urlparse

@dataclass
class SiteProfile:
    """사이트별 프로필"""
    domain: str
    base_delay: float = 3.0  # 기본 대기 시간
    min_delay: float = 1.0   # 최소 대기 시간
    max_delay: float = 10.0  # 최대 대기 시간
    request_timeout: int = 10
    max_retries: int = 3
    
    # 차단 감지 임계값
    block_threshold_fail_rate: float = 0.3  # 실패율 30% 이상 시 차단 의심
    block_threshold_status_code: List[int] = field(default_factory=lambda: [403, 429, 503])
    block_threshold_response_time: float = 30.0  # 응답 시간 30초 이상 시 의심
    
    # 안정성 지표
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    consecutive_failures: int = 0
    last_request_time: Optional[datetime] = None
    
    # 동적 조절 파라미터
    current_delay: float = 3.0
    delay_multiplier: float = 1.5  # 실패 시 지연 시간 배수
    delay_reduction_rate: float = 0.9  # 성공 시 지연 시간 감소율
    
    # User-Agent 로테이션
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ])
    current_user_agent_index: int = 0
    
    def get_user_agent(self) -> str:
        """User-Agent 가져오기 (로테이션)"""
        agent = self.user_agents[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
        return agent
    
    def adjust_delay(self, success: bool):
        """성공/실패에 따라 지연 시간 조절"""
        if success:
            # 성공 시 지연 시간 감소 (최소값 유지)
            self.current_delay = max(
                self.min_delay,
                self.current_delay * self.delay_reduction_rate
            )
            self.consecutive_failures = 0
        else:
            # 실패 시 지연 시간 증가 (최대값 제한)
            self.current_delay = min(
                self.max_delay,
                self.current_delay * self.delay_multiplier
            )
            self.consecutive_failures += 1
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'domain': self.domain,
            'base_delay': self.base_delay,
            'current_delay': self.current_delay,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'consecutive_failures': self.consecutive_failures,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SiteProfile':
        """딕셔너리에서 생성"""
        profile = cls(domain=data['domain'])
        profile.base_delay = data.get('base_delay', 3.0)
        profile.current_delay = data.get('current_delay', 3.0)
        profile.success_rate = data.get('success_rate', 1.0)
        profile.avg_response_time = data.get('avg_response_time', 0.0)
        profile.consecutive_failures = data.get('consecutive_failures', 0)
        return profile


class BlockDetector:
    """차단 감지기"""
    
    def __init__(self, profile: SiteProfile):
        self.profile = profile
        self.recent_requests = deque(maxlen=20)  # 최근 20개 요청 기록
        
    def detect_block(self, response: Optional[requests.Response], 
                    error: Optional[Exception] = None) -> Tuple[bool, str]:
        """
        차단 감지
        
        Returns:
            (is_blocked, reason)
        """
        # 1. 상태 코드 확인
        if response:
            if response.status_code in self.profile.block_threshold_status_code:
                return True, f"차단 상태 코드: {response.status_code}"
            
            # 2. 응답 시간 확인
            if hasattr(response, 'elapsed') and response.elapsed:
                if response.elapsed.total_seconds() > self.profile.block_threshold_response_time:
                    return True, f"응답 시간 초과: {response.elapsed.total_seconds():.2f}초"
        
        # 3. 에러 확인
        if error:
            error_str = str(error).lower()
            if any(keyword in error_str for keyword in ['forbidden', 'blocked', 'rate limit', '429']):
                return True, f"차단 에러: {error}"
        
        # 4. 최근 실패율 확인
        if len(self.recent_requests) >= 10:
            recent_failures = sum(1 for req in self.recent_requests if not req['success'])
            failure_rate = recent_failures / len(self.recent_requests)
            
            if failure_rate >= self.profile.block_threshold_fail_rate:
                return True, f"높은 실패율: {failure_rate:.1%}"
        
        # 5. 연속 실패 확인
        if self.profile.consecutive_failures >= 5:
            return True, f"연속 실패: {self.profile.consecutive_failures}회"
        
        return False, ""
    
    def record_request(self, success: bool, response_time: float = 0.0):
        """요청 기록"""
        self.recent_requests.append({
            'success': success,
            'response_time': response_time,
            'timestamp': datetime.now()
        })


class HealthMonitor:
    """크롤러 상태 모니터"""
    
    def __init__(self, profile: SiteProfile):
        self.profile = profile
        self.request_history = deque(maxlen=100)
        
    def update_metrics(self, success: bool, response_time: float):
        """메트릭 업데이트"""
        self.request_history.append({
            'success': success,
            'response_time': response_time,
            'timestamp': datetime.now()
        })
        
        # 성공률 계산
        if len(self.request_history) > 0:
            successes = sum(1 for req in self.request_history if req['success'])
            self.profile.success_rate = successes / len(self.request_history)
        
        # 평균 응답 시간 계산
        if len(self.request_history) > 0:
            total_time = sum(req['response_time'] for req in self.request_history)
            self.profile.avg_response_time = total_time / len(self.request_history)
    
    def get_health_status(self) -> Dict[str, any]:
        """건강 상태 반환"""
        return {
            'success_rate': self.profile.success_rate,
            'avg_response_time': self.profile.avg_response_time,
            'consecutive_failures': self.profile.consecutive_failures,
            'current_delay': self.profile.current_delay,
            'total_requests': len(self.request_history),
        }
    
    def is_healthy(self) -> bool:
        """건강 상태 확인"""
        return (
            self.profile.success_rate >= 0.7 and
            self.profile.consecutive_failures < 5 and
            self.profile.avg_response_time < 10.0
        )


class AdaptiveCrawler:
    """대응형 크롤러"""
    
    def __init__(self, site_profile: Optional[SiteProfile] = None, 
                 profile_file: str = "site_profiles.json"):
        self.profile = site_profile or SiteProfile(domain="default")
        self.profile_file = profile_file
        self.detector = BlockDetector(self.profile)
        self.monitor = HealthMonitor(self.profile)
        self.session = requests.Session()
        
        self.logger = logging.getLogger(__name__)
        
        # 프로필 로드
        self.load_profile()
        
        # 세션 설정
        self._setup_session()
    
    def _setup_session(self):
        """세션 설정"""
        self.session.headers.update({
            'User-Agent': self.profile.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def load_profile(self):
        """프로필 로드"""
        profile_path = Path(self.profile_file)
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    domain = self.profile.domain
                    if domain in data:
                        self.profile = SiteProfile.from_dict(data[domain])
                        self.detector = BlockDetector(self.profile)
                        self.monitor = HealthMonitor(self.profile)
                        self.logger.info(f"프로필 로드 완료: {domain}")
            except Exception as e:
                self.logger.warning(f"프로필 로드 실패: {e}")
    
    def save_profile(self):
        """프로필 저장"""
        profile_path = Path(self.profile_file)
        data = {}
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        data[self.profile.domain] = self.profile.to_dict()
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"프로필 저장 실패: {e}")
    
    def pre_test(self, url: str, test_requests: int = 3) -> Tuple[bool, str]:
        """
        사전 테스트
        
        Args:
            url: 테스트할 URL
            test_requests: 테스트 요청 횟수
            
        Returns:
            (success, message)
        """
        self.logger.info(f"사전 테스트 시작: {url} ({test_requests}회)")
        
        successes = 0
        total_time = 0.0
        
        for i in range(test_requests):
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    timeout=self.profile.request_timeout,
                    verify=False
                )
                elapsed = time.time() - start_time
                total_time += elapsed
                
                # 차단 감지
                is_blocked, reason = self.detector.detect_block(response)
                
                if is_blocked:
                    self.logger.warning(f"테스트 {i+1}/{test_requests}: 차단 감지 - {reason}")
                    return False, f"차단 감지: {reason}"
                
                if response.status_code == 200:
                    successes += 1
                    self.detector.record_request(True, elapsed)
                    self.monitor.update_metrics(True, elapsed)
                else:
                    self.detector.record_request(False, elapsed)
                    self.monitor.update_metrics(False, elapsed)
                
                # 요청 간 대기
                if i < test_requests - 1:
                    time.sleep(self.profile.current_delay)
                    
            except Exception as e:
                elapsed = time.time() - start_time
                self.detector.record_request(False, elapsed)
                self.monitor.update_metrics(False, elapsed)
                self.logger.warning(f"테스트 {i+1}/{test_requests} 실패: {e}")
        
        success_rate = successes / test_requests
        avg_time = total_time / test_requests
        
        if success_rate >= 0.7:
            self.logger.info(f"사전 테스트 성공: 성공률 {success_rate:.1%}, 평균 응답 시간 {avg_time:.2f}초")
            return True, f"성공률 {success_rate:.1%}, 평균 응답 시간 {avg_time:.2f}초"
        else:
            self.logger.warning(f"사전 테스트 실패: 성공률 {success_rate:.1%}")
            return False, f"낮은 성공률: {success_rate:.1%}"
    
    def fetch(self, url: str, max_retries: Optional[int] = None) -> Optional[requests.Response]:
        """
        안전한 요청
        
        Args:
            url: 요청할 URL
            max_retries: 최대 재시도 횟수
            
        Returns:
            Response 객체 또는 None
        """
        max_retries = max_retries or self.profile.max_retries
        
        # 건강 상태 확인
        if not self.monitor.is_healthy():
            self.logger.warning("크롤러 건강 상태 불량, 대기 시간 증가")
            time.sleep(self.profile.current_delay * 2)
        
        # 동적 지연 시간 적용 (약간의 랜덤성 추가)
        delay = self.profile.current_delay * (0.8 + random.random() * 0.4)
        time.sleep(delay)
        
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                
                # User-Agent 로테이션
                self.session.headers['User-Agent'] = self.profile.get_user_agent()
                
                response = self.session.get(
                    url,
                    timeout=self.profile.request_timeout,
                    verify=False
                )
                
                elapsed = time.time() - start_time
                
                # 차단 감지
                is_blocked, reason = self.detector.detect_block(response)
                
                if is_blocked:
                    self.logger.warning(f"차단 감지: {reason}")
                    self.profile.adjust_delay(False)
                    self.detector.record_request(False, elapsed)
                    self.monitor.update_metrics(False, elapsed)
                    
                    # 차단 시 긴 대기
                    if attempt < max_retries:
                        wait_time = self.profile.current_delay * (2 ** attempt)
                        self.logger.info(f"{wait_time:.1f}초 대기 후 재시도...")
                        time.sleep(wait_time)
                    continue
                
                # 성공
                if response.status_code == 200:
                    self.profile.adjust_delay(True)
                    self.detector.record_request(True, elapsed)
                    self.monitor.update_metrics(True, elapsed)
                    self.profile.last_request_time = datetime.now()
                    return response
                else:
                    self.profile.adjust_delay(False)
                    self.detector.record_request(False, elapsed)
                    self.monitor.update_metrics(False, elapsed)
                    
            except Exception as e:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0
                self.profile.adjust_delay(False)
                self.detector.record_request(False, elapsed)
                self.monitor.update_metrics(False, elapsed)
                
                if attempt < max_retries:
                    wait_time = self.profile.current_delay * (1.5 ** attempt)
                    self.logger.warning(f"요청 실패 (시도 {attempt}/{max_retries}): {e}. {wait_time:.1f}초 후 재시도...")
                    time.sleep(wait_time)
        
        # 모든 재시도 실패
        self.logger.error(f"요청 최종 실패: {url}")
        return None
    
    def get_status(self) -> Dict[str, any]:
        """현재 상태 반환"""
        health = self.monitor.get_health_status()
        return {
            **health,
            'domain': self.profile.domain,
            'is_healthy': self.monitor.is_healthy(),
        }
    
    def reset(self):
        """상태 리셋 (필요 시)"""
        self.profile.current_delay = self.profile.base_delay
        self.profile.consecutive_failures = 0
        self.profile.success_rate = 1.0
        self.logger.info("크롤러 상태 리셋 완료")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_profile()



