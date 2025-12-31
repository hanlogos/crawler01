# risk_management_system.py
"""
리스크 관리 시스템

3단계 리스크 레벨 및 자동 복구 프로토콜
"""

import sys
import io
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class RiskLevel(Enum):
    """리스크 레벨"""
    LOW = "low"      # 안전
    MEDIUM = "medium"  # 주의
    HIGH = "high"    # 위험

class RecoveryLevel(Enum):
    """복구 레벨"""
    SOFT = 1      # 연속 오류 3회
    MEDIUM = 2    # 연속 오류 5회
    HARD = 3      # 연속 오류 10회
    EMERGENCY = 4  # 차단 감지

@dataclass
class RiskMetrics:
    """리스크 지표"""
    success_rate: float  # 성공률 (0.0 ~ 1.0)
    avg_delay: float  # 평균 지연 시간 (초)
    consecutive_errors: int  # 연속 오류 횟수
    requests_per_minute: float  # 분당 요청 수
    last_error_time: Optional[datetime] = None
    blocked_detected: bool = False  # 차단 감지

@dataclass
class RiskAssessment:
    """리스크 평가"""
    level: RiskLevel
    metrics: RiskMetrics
    recommendations: List[str]
    auto_action: Optional[str] = None

class RiskManagementSystem:
    """리스크 관리 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history: List[RiskMetrics] = []
    
    def assess_risk(self, metrics: RiskMetrics) -> RiskAssessment:
        """리스크 평가"""
        
        # 지표 분석
        risk_level = self._determine_risk_level(metrics)
        recommendations = self._generate_recommendations(risk_level, metrics)
        auto_action = self._determine_auto_action(risk_level, metrics)
        
        assessment = RiskAssessment(
            level=risk_level,
            metrics=metrics,
            recommendations=recommendations,
            auto_action=auto_action
        )
        
        # 히스토리 저장
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return assessment
    
    def _determine_risk_level(self, metrics: RiskMetrics) -> RiskLevel:
        """리스크 레벨 결정"""
        
        # High Risk 조건
        if (metrics.success_rate < 0.7 or
            metrics.avg_delay < 2.0 or
            metrics.consecutive_errors > 5 or
            metrics.requests_per_minute > 20 or
            metrics.blocked_detected):
            return RiskLevel.HIGH
        
        # Medium Risk 조건
        if (0.7 <= metrics.success_rate < 0.9 or
            2.0 <= metrics.avg_delay < 3.0 or
            3 <= metrics.consecutive_errors <= 5 or
            15 <= metrics.requests_per_minute <= 20):
            return RiskLevel.MEDIUM
        
        # Low Risk (기본)
        return RiskLevel.LOW
    
    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        metrics: RiskMetrics
    ) -> List[str]:
        """권장사항 생성"""
        
        recommendations = []
        
        if risk_level == RiskLevel.HIGH:
            recommendations.append("⚠️ 즉시 크롤링 중지")
            recommendations.append("1-3시간 대기 후 재시도")
            recommendations.append("전체 세션 리셋")
            recommendations.append("관리자 알림 필요")
        
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("지연 시간 50% 증가")
            recommendations.append("세션당 요청 50% 감소")
            recommendations.append("User-Agent 로테이션")
            recommendations.append("10분마다 모니터링")
        
        else:  # LOW
            recommendations.append("현재 상태 유지")
            recommendations.append("1시간마다 모니터링")
        
        return recommendations
    
    def _determine_auto_action(
        self,
        risk_level: RiskLevel,
        metrics: RiskMetrics
    ) -> Optional[str]:
        """자동 조치 결정"""
        
        # 차단 감지
        if metrics.blocked_detected:
            return "emergency_stop"
        
        # 연속 오류 기반 복구 레벨
        if metrics.consecutive_errors >= 10:
            return "hard_recovery"
        elif metrics.consecutive_errors >= 5:
            return "medium_recovery"
        elif metrics.consecutive_errors >= 3:
            return "soft_recovery"
        
        # 리스크 레벨 기반
        if risk_level == RiskLevel.HIGH:
            return "stop_and_wait"
        elif risk_level == RiskLevel.MEDIUM:
            return "reduce_speed"
        
        return None
    
    def get_recovery_protocol(self, recovery_level: RecoveryLevel) -> Dict:
        """복구 프로토콜 가져오기"""
        
        protocols = {
            RecoveryLevel.SOFT: {
                'name': 'Soft Recovery',
                'delay_multiplier': 2.0,
                'wait_time': 300,  # 5분
                'actions': [
                    '지연 시간 2배 증가',
                    '5분 대기 후 재시도',
                    '성공 시 정상 속도로 복귀'
                ]
            },
            RecoveryLevel.MEDIUM: {
                'name': 'Medium Recovery',
                'delay_multiplier': 3.0,
                'wait_time': 1800,  # 30분
                'actions': [
                    '지연 시간 3배 증가',
                    '30분 대기',
                    'User-Agent 변경',
                    '세션 로테이션',
                    '50% 속도로 재시작'
                ]
            },
            RecoveryLevel.HARD: {
                'name': 'Hard Recovery',
                'delay_multiplier': 5.0,
                'wait_time': 10800,  # 3시간
                'actions': [
                    '크롤링 완전 중지',
                    '3시간 대기',
                    '전체 시스템 리셋',
                    '안전 모드로 재시작',
                    '관리자 승인 필요'
                ]
            },
            RecoveryLevel.EMERGENCY: {
                'name': 'Emergency Stop',
                'delay_multiplier': 0,
                'wait_time': 86400,  # 24시간
                'actions': [
                    '즉시 모든 크롤링 중지',
                    '24시간 대기',
                    '수동 검증 후에만 재시작'
                ]
            }
        }
        
        return protocols.get(recovery_level, protocols[RecoveryLevel.SOFT])

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("리스크 관리 시스템 테스트")
    print("="*60)
    print()
    
    system = RiskManagementSystem()
    
    # 테스트 케이스
    test_cases = [
        {
            'name': 'Low Risk',
            'metrics': RiskMetrics(
                success_rate=0.95,
                avg_delay=4.0,
                consecutive_errors=0,
                requests_per_minute=10
            )
        },
        {
            'name': 'Medium Risk',
            'metrics': RiskMetrics(
                success_rate=0.80,
                avg_delay=2.5,
                consecutive_errors=4,
                requests_per_minute=18
            )
        },
        {
            'name': 'High Risk',
            'metrics': RiskMetrics(
                success_rate=0.65,
                avg_delay=1.5,
                consecutive_errors=6,
                requests_per_minute=25
            )
        },
        {
            'name': 'Blocked',
            'metrics': RiskMetrics(
                success_rate=0.50,
                avg_delay=1.0,
                consecutive_errors=10,
                requests_per_minute=30,
                blocked_detected=True
            )
        }
    ]
    
    for test_case in test_cases:
        print(f"\n[{test_case['name']}]")
        print("-" * 60)
        
        assessment = system.assess_risk(test_case['metrics'])
        
        risk_icon = {
            RiskLevel.LOW: '🟢',
            RiskLevel.MEDIUM: '🟡',
            RiskLevel.HIGH: '🔴'
        }.get(assessment.level, '⚪')
        
        print(f"리스크 레벨: {risk_icon} {assessment.level.value.upper()}")
        print(f"성공률: {assessment.metrics.success_rate:.1%}")
        print(f"연속 오류: {assessment.metrics.consecutive_errors}회")
        
        if assessment.auto_action:
            print(f"자동 조치: {assessment.auto_action}")
        
        print("\n권장사항:")
        for rec in assessment.recommendations:
            print(f"  - {rec}")
    
    # 복구 프로토콜
    print("\n" + "="*60)
    print("복구 프로토콜")
    print("="*60)
    
    for level in RecoveryLevel:
        protocol = system.get_recovery_protocol(level)
        print(f"\n[{protocol['name']}]")
        print(f"  대기 시간: {protocol['wait_time']}초 ({protocol['wait_time']//60}분)")
        print(f"  지연 배수: {protocol['delay_multiplier']}배")
        print("  조치:")
        for action in protocol['actions']:
            print(f"    - {action}")
    
    print("\n✅ 테스트 완료!")




