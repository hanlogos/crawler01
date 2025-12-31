# ai_insights_system.py
"""
AI 인사이트 시스템

크롤링 운영, 데이터 관리, 데이터 활용에 대한 AI 인사이트 제공
"""

import sys
import io
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class Insight:
    """인사이트"""
    category: str  # 'operation', 'data_management', 'data_utilization'
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    actionable: bool  # 실행 가능한 조언인지
    recommendation: str  # 구체적인 권장사항

class AIInsightsSystem:
    """AI 인사이트 시스템"""
    
    def __init__(self, llm_processor=None):
        self.llm_processor = llm_processor
        self.logger = logging.getLogger(__name__)
        self.insights_history: List[Insight] = []
    
    def analyze_crawling_operation(
        self,
        stats: Dict,
        site_states: List[Dict],
        recent_errors: List[Dict] = None
    ) -> List[Insight]:
        """크롤링 운영 분석"""
        
        insights = []
        
        # 1. 성공률 분석
        if stats.get('total_requests', 0) > 0:
            success_rate = stats.get('success_count', 0) / stats.get('total_requests', 1)
            
            if success_rate < 0.7:
                insights.append(Insight(
                    category='operation',
                    title='낮은 성공률 감지',
                    description=f'현재 성공률이 {success_rate:.1%}로 낮습니다.',
                    priority='high',
                    actionable=True,
                    recommendation='페이크 페이스 프로필을 "thorough"로 변경하거나 대기 시간을 늘리세요.'
                ))
            elif success_rate > 0.95:
                insights.append(Insight(
                    category='operation',
                    title='높은 성공률',
                    description=f'성공률이 {success_rate:.1%}로 양호합니다.',
                    priority='low',
                    actionable=False,
                    recommendation='현재 설정을 유지하거나 약간 더 빠른 프로필을 시도해볼 수 있습니다.'
                ))
        
        # 2. 에러 패턴 분석
        if recent_errors:
            error_types = {}
            for error in recent_errors:
                error_type = error.get('type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            most_common = max(error_types.items(), key=lambda x: x[1]) if error_types else None
            
            if most_common and most_common[1] >= 3:
                insights.append(Insight(
                    category='operation',
                    title='반복되는 오류',
                    description=f'"{most_common[0]}" 오류가 {most_common[1]}회 발생했습니다.',
                    priority='high',
                    actionable=True,
                    recommendation='사이트 구조 변경 가능성이 있습니다. 구조 분석을 다시 실행하세요.'
                ))
        
        # 3. 수집 효율성
        if stats.get('total_collected', 0) > 0:
            avg_time = stats.get('total_time', 0) / stats.get('total_collected', 1)
            
            if avg_time > 30:
                insights.append(Insight(
                    category='operation',
                    title='느린 수집 속도',
                    description=f'보고서당 평균 {avg_time:.1f}초 소요됩니다.',
                    priority='medium',
                    actionable=True,
                    recommendation='Ollama 모델을 더 작은 모델로 변경하거나 분석을 선택적으로 사용하세요.'
                ))
        
        # 4. 사이트별 상태
        for site_state in site_states:
            if site_state.get('status') == 'error':
                insights.append(Insight(
                    category='operation',
                    title=f'{site_state.get("site_name")} 오류',
                    description=f'{site_state.get("last_error", "알 수 없는 오류")}',
                    priority='high',
                    actionable=True,
                    recommendation='사이트 연결을 확인하고 구조 분석을 다시 실행하세요.'
                ))
        
        return insights
    
    def analyze_data_management(
        self,
        data_stats: Dict,
        storage_info: Dict = None
    ) -> List[Insight]:
        """데이터 관리 분석"""
        
        insights = []
        
        # 1. 데이터 양
        total_reports = data_stats.get('total_reports', 0)
        
        if total_reports > 1000:
            insights.append(Insight(
                category='data_management',
                title='대량 데이터 관리 필요',
                description=f'{total_reports}개의 보고서가 수집되었습니다.',
                priority='medium',
                actionable=True,
                recommendation='데이터베이스로 마이그레이션하거나 인덱싱 시스템을 구축하세요.'
            ))
        
        # 2. 중복 데이터
        duplicate_rate = data_stats.get('duplicate_rate', 0)
        if duplicate_rate > 0.1:
            insights.append(Insight(
                category='data_management',
                title='중복 데이터 감지',
                description=f'중복률이 {duplicate_rate:.1%}입니다.',
                priority='medium',
                actionable=True,
                recommendation='중복 제거 로직을 추가하거나 report_id 기반 중복 체크를 강화하세요.'
            ))
        
        # 3. 데이터 품질
        incomplete_rate = data_stats.get('incomplete_rate', 0)
        if incomplete_rate > 0.2:
            insights.append(Insight(
                category='data_management',
                title='불완전한 데이터',
                description=f'불완전한 데이터가 {incomplete_rate:.1%}입니다.',
                priority='high',
                actionable=True,
                recommendation='파서 로직을 개선하거나 적응형 파서의 신뢰도 임계값을 조정하세요.'
            ))
        
        # 4. 저장 공간
        if storage_info:
            storage_used = storage_info.get('used_gb', 0)
            if storage_used > 10:
                insights.append(Insight(
                    category='data_management',
                    title='저장 공간 관리',
                    description=f'{storage_used:.1f}GB의 저장 공간을 사용 중입니다.',
                    priority='low',
                    actionable=True,
                    recommendation='오래된 데이터를 아카이브하거나 압축을 고려하세요.'
                ))
        
        # 5. 백업
        last_backup = data_stats.get('last_backup')
        if not last_backup:
            insights.append(Insight(
                category='data_management',
                title='백업 필요',
                description='데이터 백업이 설정되지 않았습니다.',
                priority='high',
                actionable=True,
                recommendation='정기적인 백업 스케줄을 설정하세요.'
            ))
        
        return insights
    
    def analyze_data_utilization(
        self,
        analysis_stats: Dict,
        usage_patterns: Dict = None
    ) -> List[Insight]:
        """데이터 활용 분석"""
        
        insights = []
        
        # 1. 분석 활용도
        analyzed_count = analysis_stats.get('analyzed_count', 0)
        total_count = analysis_stats.get('total_count', 0)
        
        if total_count > 0:
            analysis_rate = analyzed_count / total_count
            
            if analysis_rate < 0.5:
                insights.append(Insight(
                    category='data_utilization',
                    title='낮은 분석 활용도',
                    description=f'수집된 데이터의 {analysis_rate:.1%}만 분석되었습니다.',
                    priority='medium',
                    actionable=True,
                    recommendation='자동 분석을 활성화하거나 배치 분석 작업을 설정하세요.'
                ))
        
        # 2. 아바타 활용
        avatar_count = analysis_stats.get('avatar_count', 0)
        if avatar_count == 0:
            insights.append(Insight(
                category='data_utilization',
                title='아바타 미활용',
                description='아바타 분석이 활성화되지 않았습니다.',
                priority='low',
                actionable=True,
                recommendation='아바타 시스템을 활성화하여 다각도 분석을 수행하세요.'
            ))
        
        # 3. 트렌드 분석
        if usage_patterns:
            trend_data = usage_patterns.get('trends', [])
            if len(trend_data) < 10:
                insights.append(Insight(
                    category='data_utilization',
                    title='트렌드 분석 데이터 부족',
                    description='트렌드 분석을 위한 충분한 데이터가 없습니다.',
                    priority='low',
                    actionable=True,
                    recommendation='더 많은 데이터를 수집하거나 분석 기간을 늘리세요.'
                ))
        
        # 4. 리포트 활용
        report_usage = analysis_stats.get('report_usage_rate', 0)
        if report_usage < 0.3:
            insights.append(Insight(
                category='data_utilization',
                title='낮은 리포트 활용도',
                description=f'수집된 리포트의 {report_usage:.1%}만 활용되고 있습니다.',
                priority='medium',
                actionable=True,
                recommendation='필터링 및 검색 기능을 개선하거나 자동 알림을 설정하세요.'
            ))
        
        # 5. 통합 활용
        integration_count = analysis_stats.get('integration_count', 0)
        if integration_count == 0:
            insights.append(Insight(
                category='data_utilization',
                title='외부 시스템 통합 부재',
                description='다른 시스템과의 통합이 없습니다.',
                priority='low',
                actionable=True,
                recommendation='API를 제공하거나 데이터베이스 연동을 고려하세요.'
            ))
        
        return insights
    
    def generate_comprehensive_insights(
        self,
        operation_stats: Dict,
        data_stats: Dict,
        analysis_stats: Dict,
        site_states: List[Dict] = None
    ) -> Dict[str, List[Insight]]:
        """종합 인사이트 생성"""
        
        all_insights = {
            'operation': self.analyze_crawling_operation(
                operation_stats,
                site_states or []
            ),
            'data_management': self.analyze_data_management(data_stats),
            'data_utilization': self.analyze_data_utilization(analysis_stats)
        }
        
        # 인사이트 저장
        for category, insights in all_insights.items():
            self.insights_history.extend(insights)
        
        return all_insights
    
    def get_priority_insights(self, limit: int = 5) -> List[Insight]:
        """우선순위 높은 인사이트"""
        
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        sorted_insights = sorted(
            self.insights_history,
            key=lambda x: (priority_order.get(x.priority, 0), x.actionable),
            reverse=True
        )
        
        return sorted_insights[:limit]

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("AI 인사이트 시스템 테스트")
    print("="*60)
    print()
    
    system = AIInsightsSystem()
    
    # 테스트 데이터
    operation_stats = {
        'total_requests': 100,
        'success_count': 65,
        'total_collected': 50,
        'total_time': 2000
    }
    
    data_stats = {
        'total_reports': 500,
        'duplicate_rate': 0.15,
        'incomplete_rate': 0.25
    }
    
    analysis_stats = {
        'analyzed_count': 100,
        'total_count': 500,
        'avatar_count': 6
    }
    
    # 인사이트 생성
    insights = system.generate_comprehensive_insights(
        operation_stats,
        data_stats,
        analysis_stats
    )
    
    # 결과 출력
    for category, category_insights in insights.items():
        print(f"\n[{category.upper()}] 인사이트: {len(category_insights)}개")
        for insight in category_insights:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(insight.priority, '⚪')
            print(f"\n{priority_icon} {insight.title}")
            print(f"   {insight.description}")
            if insight.actionable:
                print(f"   💡 {insight.recommendation}")
    
    # 우선순위 인사이트
    print("\n" + "="*60)
    print("우선순위 높은 인사이트 (Top 5)")
    print("="*60)
    
    priority_insights = system.get_priority_insights(5)
    for i, insight in enumerate(priority_insights, 1):
        print(f"\n{i}. [{insight.priority.upper()}] {insight.title}")
        print(f"   {insight.description}")
        if insight.actionable:
            print(f"   💡 {insight.recommendation}")
    
    print("\n✅ 테스트 완료!")



