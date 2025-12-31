# time_based_strategy.py
"""
시간대별 크롤링 전략 시스템

참고 가이드의 시간대별/요일별 전략 구현
"""

import sys
import io
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class TimeSlot(Enum):
    """시간대"""
    DAWN = "dawn"      # 00:00-06:00
    MORNING = "morning"  # 06:00-09:00
    DAYTIME = "daytime"  # 09:00-18:00
    EVENING = "evening"  # 18:00-24:00

class DayOfWeek(Enum):
    """요일"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

@dataclass
class TimeStrategy:
    """시간대별 전략"""
    time_slot: TimeSlot
    speed: str  # "fast", "balanced", "safe"
    delay: float  # 대기 시간 (초)
    fake_face_profile: str
    max_reports: int
    description: str

@dataclass
class DayStrategy:
    """요일별 전략"""
    day: DayOfWeek
    focus: str
    priority: str
    volume_multiplier: float  # 1.0 = 100%, 1.5 = 150%
    description: str

class TimeBasedStrategyManager:
    """시간대별 전략 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 시간대별 전략
        self.time_strategies = {
            TimeSlot.DAWN: TimeStrategy(
                time_slot=TimeSlot.DAWN,
                speed="fast",
                delay=1.5,
                fake_face_profile="quick_scan",
                max_reports=200,
                description="대용량 백필, 히스토리 수집"
            ),
            TimeSlot.MORNING: TimeStrategy(
                time_slot=TimeSlot.MORNING,
                speed="balanced",
                delay=3.0,
                fake_face_profile="casual",
                max_reports=50,
                description="일일 보고서 수집"
            ),
            TimeSlot.DAYTIME: TimeStrategy(
                time_slot=TimeSlot.DAYTIME,
                speed="safe",
                delay=5.0,
                fake_face_profile="thorough",
                max_reports=30,
                description="실시간 모니터링, 키워드 감시"
            ),
            TimeSlot.EVENING: TimeStrategy(
                time_slot=TimeSlot.EVENING,
                speed="balanced",
                delay=3.0,
                fake_face_profile="casual",
                max_reports=50,
                description="정기 수집, 분석 보고서"
            )
        }
        
        # 요일별 전략
        self.day_strategies = {
            DayOfWeek.MONDAY: DayStrategy(
                day=DayOfWeek.MONDAY,
                focus="주말 뉴스 수집 (백필)",
                priority="긴급 이슈, 속보",
                volume_multiplier=1.5,
                description="주말 동안 쌓인 뉴스 수집"
            ),
            DayOfWeek.TUESDAY: DayStrategy(
                day=DayOfWeek.TUESDAY,
                focus="정기 수집 (안정적)",
                priority="일일 루틴",
                volume_multiplier=1.0,
                description="정상적인 일일 수집"
            ),
            DayOfWeek.WEDNESDAY: DayStrategy(
                day=DayOfWeek.WEDNESDAY,
                focus="정기 수집 (안정적)",
                priority="일일 루틴",
                volume_multiplier=1.0,
                description="정상적인 일일 수집"
            ),
            DayOfWeek.THURSDAY: DayStrategy(
                day=DayOfWeek.THURSDAY,
                focus="정기 수집 (안정적)",
                priority="일일 루틴",
                volume_multiplier=1.0,
                description="정상적인 일일 수집"
            ),
            DayOfWeek.FRIDAY: DayStrategy(
                day=DayOfWeek.FRIDAY,
                focus="주간 요약, 전체 스캔",
                priority="종합 분석",
                volume_multiplier=1.2,
                description="주간 요약 및 전체 스캔"
            ),
            DayOfWeek.SATURDAY: DayStrategy(
                day=DayOfWeek.SATURDAY,
                focus="대용량 작업 (백필, 검증)",
                priority="시스템 유지보수",
                volume_multiplier=0.8,
                description="주말 대용량 작업"
            ),
            DayOfWeek.SUNDAY: DayStrategy(
                day=DayOfWeek.SUNDAY,
                focus="대용량 작업 (백필, 검증)",
                priority="시스템 유지보수",
                volume_multiplier=0.8,
                description="주말 대용량 작업"
            )
        }
    
    def get_current_strategy(self) -> Dict:
        """현재 시간에 맞는 전략 가져오기"""
        
        now = datetime.now()
        current_time = now.time()
        current_day = DayOfWeek(now.weekday())
        
        # 시간대 결정
        if time(0, 0) <= current_time < time(6, 0):
            time_slot = TimeSlot.DAWN
        elif time(6, 0) <= current_time < time(9, 0):
            time_slot = TimeSlot.MORNING
        elif time(9, 0) <= current_time < time(18, 0):
            time_slot = TimeSlot.DAYTIME
        else:
            time_slot = TimeSlot.EVENING
        
        time_strategy = self.time_strategies[time_slot]
        day_strategy = self.day_strategies[current_day]
        
        # 최종 설정 계산
        base_max_reports = time_strategy.max_reports
        final_max_reports = int(base_max_reports * day_strategy.volume_multiplier)
        
        return {
            'time_slot': time_slot.value,
            'day': current_day.name,
            'delay': time_strategy.delay,
            'fake_face_profile': time_strategy.fake_face_profile,
            'max_reports': final_max_reports,
            'time_description': time_strategy.description,
            'day_description': day_strategy.description,
            'focus': day_strategy.focus,
            'priority': day_strategy.priority
        }
    
    def get_strategy_for_time(self, target_time: time) -> TimeStrategy:
        """특정 시간의 전략 가져오기"""
        
        if time(0, 0) <= target_time < time(6, 0):
            return self.time_strategies[TimeSlot.DAWN]
        elif time(6, 0) <= target_time < time(9, 0):
            return self.time_strategies[TimeSlot.MORNING]
        elif time(9, 0) <= target_time < time(18, 0):
            return self.time_strategies[TimeSlot.DAYTIME]
        else:
            return self.time_strategies[TimeSlot.EVENING]
    
    def get_strategy_for_day(self, day: DayOfWeek) -> DayStrategy:
        """특정 요일의 전략 가져오기"""
        return self.day_strategies[day]

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("시간대별 전략 시스템 테스트")
    print("="*60)
    print()
    
    manager = TimeBasedStrategyManager()
    
    # 현재 전략
    strategy = manager.get_current_strategy()
    
    print("현재 시간에 맞는 전략:")
    print(f"  시간대: {strategy['time_slot']}")
    print(f"  요일: {strategy['day']}")
    print(f"  대기 시간: {strategy['delay']}초")
    print(f"  프로필: {strategy['fake_face_profile']}")
    print(f"  최대 수집: {strategy['max_reports']}개")
    print(f"  시간대 설명: {strategy['time_description']}")
    print(f"  요일 설명: {strategy['day_description']}")
    print(f"  집중: {strategy['focus']}")
    print(f"  우선순위: {strategy['priority']}")
    
    print("\n✅ 테스트 완료!")



