# fake_face_system.py
"""
페이크 페이스 시스템

인간처럼 행동하여 차단 위험을 최소화
"""

import sys
import io
import random
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class HumanBehaviorProfile:
    """인간 행동 프로필"""
    name: str
    min_delay: float  # 최소 대기 시간 (초)
    max_delay: float  # 최대 대기 시간 (초)
    scroll_probability: float  # 스크롤 확률 (0.0 ~ 1.0)
    click_probability: float  # 클릭 확률
    reading_time_per_page: float  # 페이지당 읽기 시간 (초)
    session_duration: float  # 세션 지속 시간 (초)
    break_probability: float  # 휴식 확률
    break_duration: float  # 휴식 시간 (초)

class FakeFaceSystem:
    """페이크 페이스 시스템"""
    
    # 사전 정의된 프로필들
    PROFILES = {
        'casual': HumanBehaviorProfile(
            name='casual',
            min_delay=3.0,
            max_delay=8.0,
            scroll_probability=0.6,
            click_probability=0.4,
            reading_time_per_page=15.0,
            session_duration=1800.0,  # 30분
            break_probability=0.3,
            break_duration=300.0  # 5분
        ),
        'researcher': HumanBehaviorProfile(
            name='researcher',
            min_delay=5.0,
            max_delay=15.0,
            scroll_probability=0.8,
            click_probability=0.6,
            reading_time_per_page=30.0,
            session_duration=3600.0,  # 1시간
            break_probability=0.2,
            break_duration=600.0  # 10분
        ),
        'quick_scan': HumanBehaviorProfile(
            name='quick_scan',
            min_delay=1.0,
            max_delay=3.0,
            scroll_probability=0.3,
            click_probability=0.2,
            reading_time_per_page=5.0,
            session_duration=600.0,  # 10분
            break_probability=0.1,
            break_duration=60.0  # 1분
        ),
        'thorough': HumanBehaviorProfile(
            name='thorough',
            min_delay=8.0,
            max_delay=20.0,
            scroll_probability=0.9,
            click_probability=0.7,
            reading_time_per_page=45.0,
            session_duration=7200.0,  # 2시간
            break_probability=0.4,
            break_duration=900.0  # 15분
        )
    }
    
    def __init__(self, profile_name: str = 'casual'):
        """
        초기화
        
        Args:
            profile_name: 사용할 프로필 이름
        """
        self.profile = self.PROFILES.get(profile_name, self.PROFILES['casual'])
        self.logger = logging.getLogger(__name__)
        
        # 세션 추적
        self.session_start = datetime.now()
        self.request_count = 0
        self.last_request_time = None
        self.break_until = None
        
        self.logger.info(f"페이크 페이스 시스템 초기화: {self.profile.name} 프로필")
    
    def should_take_break(self) -> bool:
        """휴식이 필요한지 확인"""
        
        # 이미 휴식 중이면
        if self.break_until and datetime.now() < self.break_until:
            return True
        
        # 세션 시간 확인
        session_elapsed = (datetime.now() - self.session_start).total_seconds()
        if session_elapsed > self.profile.session_duration:
            return True
        
        # 확률 기반 휴식
        if random.random() < self.profile.break_probability:
            return True
        
        return False
    
    def take_break(self):
        """휴식"""
        
        if not self.should_take_break():
            return
        
        # 휴식 시간 계산 (약간의 랜덤성 추가)
        break_time = self.profile.break_duration * random.uniform(0.8, 1.2)
        self.break_until = datetime.now() + timedelta(seconds=break_time)
        
        self.logger.info(f"휴식 시작: {break_time:.0f}초")
        time.sleep(break_time)
        
        self.logger.info("휴식 종료")
        self.break_until = None
        self.session_start = datetime.now()  # 세션 재시작
    
    def wait_before_request(self):
        """요청 전 대기 (인간처럼)"""
        
        # 휴식 확인
        if self.should_take_break():
            self.take_break()
        
        # 마지막 요청 이후 경과 시간
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            
            # 최소 대기 시간이 지났는지 확인
            min_wait = self.profile.min_delay
            if elapsed < min_wait:
                time.sleep(min_wait - elapsed)
        
        # 랜덤 대기 시간 (인간의 불규칙성)
        wait_time = random.uniform(
            self.profile.min_delay,
            self.profile.max_delay
        )
        
        # 가우시안 분포로 더 자연스럽게
        wait_time = max(
            self.profile.min_delay,
            random.gauss(wait_time, wait_time * 0.2)
        )
        
        self.logger.debug(f"요청 전 대기: {wait_time:.2f}초")
        time.sleep(wait_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def simulate_reading(self, content_length: int = 1000):
        """읽기 시뮬레이션"""
        
        # 내용 길이에 따른 읽기 시간 계산
        base_time = self.profile.reading_time_per_page
        length_factor = content_length / 1000.0  # 1000자 기준
        
        reading_time = base_time * length_factor * random.uniform(0.8, 1.2)
        
        self.logger.debug(f"읽기 시뮬레이션: {reading_time:.2f}초")
        time.sleep(reading_time)
    
    def simulate_scrolling(self):
        """스크롤 시뮬레이션"""
        
        if random.random() < self.profile.scroll_probability:
            # 스크롤 횟수 (1-3회)
            scroll_count = random.randint(1, 3)
            
            for _ in range(scroll_count):
                # 스크롤 간격
                time.sleep(random.uniform(0.5, 2.0))
    
    def get_random_user_agent(self) -> str:
        """랜덤 User-Agent"""
        
        user_agents = [
            # Chrome (Windows)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            
            # Chrome (Mac)
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox (Windows)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Safari (Mac)
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        
        return random.choice(user_agents)
    
    def get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """인간처럼 보이는 헤더 생성"""
        
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Cache-Control': 'max-age=0',
        }
        
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    def get_session_stats(self) -> Dict:
        """세션 통계"""
        
        session_elapsed = (datetime.now() - self.session_start).total_seconds()
        
        return {
            'profile': self.profile.name,
            'request_count': self.request_count,
            'session_elapsed': session_elapsed,
            'session_duration': self.profile.session_duration,
            'is_break': self.break_until is not None and datetime.now() < self.break_until,
            'break_until': self.break_until.isoformat() if self.break_until else None
        }

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("페이크 페이스 시스템 테스트")
    print("="*60)
    print()
    
    # 시스템 생성
    fake_face = FakeFaceSystem(profile_name='researcher')
    
    # 시뮬레이션
    print("요청 시뮬레이션 (5회)...")
    for i in range(5):
        print(f"\n[{i+1}/5] 요청 준비...")
        fake_face.wait_before_request()
        
        # 헤더 생성
        headers = fake_face.get_headers()
        print(f"  User-Agent: {headers['User-Agent'][:50]}...")
        
        # 읽기 시뮬레이션
        if random.random() < 0.5:
            fake_face.simulate_reading(random.randint(500, 2000))
            print("  읽기 완료")
        
        # 통계
        stats = fake_face.get_session_stats()
        print(f"  요청 수: {stats['request_count']}, 세션 시간: {stats['session_elapsed']:.0f}초")
    
    print("\n✅ 테스트 완료!")



