# integrated_crawler_manager.py
"""
통합 크롤러 매니저

페이크 페이스, 데이터 구조, 시나리오를 통합 관리
"""

import sys
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from fake_face_system import FakeFaceSystem
from data_structure_templates import DataStructureManager
from crawling_scenarios import ScenarioManager, ScenarioExecutor, CrawlingScenario
from crawler_38com_adaptive import AdaptiveThirtyEightComCrawler
from structure_monitor import AdaptiveCrawler38Com

class IntegratedCrawlerManager:
    """통합 크롤러 매니저"""
    
    def __init__(
        self,
        use_fake_face: bool = True,
        fake_face_profile: str = 'casual',
        use_adaptive_parsing: bool = True,
        use_ollama: bool = False
    ):
        """
        초기화
        
        Args:
            use_fake_face: 페이크 페이스 사용 여부
            fake_face_profile: 페이크 페이스 프로필
            use_adaptive_parsing: 적응형 파싱 사용 여부
            use_ollama: Ollama 사용 여부
        """
        self.logger = logging.getLogger(__name__)
        
        # 페이크 페이스 시스템
        if use_fake_face:
            self.fake_face = FakeFaceSystem(profile_name=fake_face_profile)
            self.logger.info(f"✅ 페이크 페이스 활성화: {fake_face_profile} 프로필")
        else:
            self.fake_face = None
        
        # 데이터 구조 관리자
        self.data_manager = DataStructureManager()
        self.logger.info("✅ 데이터 구조 관리자 초기화")
        
        # 시나리오 관리자
        self.scenario_manager = ScenarioManager()
        self.logger.info("✅ 시나리오 관리자 초기화")
        
        # 적응형 크롤러
        self.crawler = AdaptiveThirtyEightComCrawler(
            delay=3.0,
            use_adaptive=True,
            use_adaptive_parsing=use_adaptive_parsing
        )
        self.logger.info("✅ 적응형 크롤러 초기화")
        
        # 시나리오 실행기
        self.executor = ScenarioExecutor(self.crawler, self.fake_face)
        
        # 통계
        self.stats = {
            'total_scenarios_run': 0,
            'total_reports_collected': 0,
            'last_run': None
        }
    
    def run_scenario(self, scenario_name: str, **kwargs) -> Dict:
        """시나리오 실행"""
        
        scenario = self.scenario_manager.get_scenario(scenario_name)
        if not scenario:
            return {'success': False, 'error': f'시나리오를 찾을 수 없습니다: {scenario_name}'}
        
        # 옵션 오버라이드
        if kwargs:
            for key, value in kwargs.items():
                if hasattr(scenario, key):
                    setattr(scenario, key, value)
        
        self.logger.info(f"시나리오 실행: {scenario.name}")
        
        # 페이크 페이스 적용
        if self.fake_face:
            self.fake_face.profile = self.fake_face.PROFILES.get(
                scenario.fake_face_profile,
                self.fake_face.PROFILES['casual']
            )
        
        # 크롤러에 페이크 페이스 적용
        if self.fake_face and hasattr(self.crawler, 'session'):
            # 요청 전 대기
            self.fake_face.wait_before_request()
            
            # 헤더 업데이트
            headers = self.fake_face.get_headers()
            self.crawler.session.headers.update(headers)
        
        # 시나리오 실행
        result = self.executor.execute(scenario)
        
        # 통계 업데이트
        if result.get('success'):
            self.stats['total_scenarios_run'] += 1
            self.stats['total_reports_collected'] += result.get('reports_count', 0)
            self.stats['last_run'] = datetime.now().isoformat()
        
        return result
    
    def create_and_run(
        self,
        name: str,
        requirements: Dict[str, Any]
    ) -> Dict:
        """커스텀 시나리오 생성 및 실행"""
        
        scenario = self.scenario_manager.create_custom_scenario(name, requirements)
        return self.run_scenario(scenario.name, **requirements)
    
    def suggest_scenarios(self, requirements: Dict[str, Any]) -> List[Dict]:
        """시나리오 제안"""
        
        scenarios = self.scenario_manager.suggest_scenario(requirements)
        
        suggestions = []
        for scenario in scenarios:
            suggestions.append({
                'name': scenario.name,
                'type': scenario.scenario_type.value,
                'description': scenario.description,
                'days': scenario.days,
                'max_reports': scenario.max_reports,
                'keywords': scenario.keywords,
                'stock_codes': scenario.stock_codes
            })
        
        return suggestions
    
    def get_data_structure(self, template_name: str) -> Optional[Dict]:
        """데이터 구조 가져오기"""
        
        template = self.data_manager.get_template(template_name)
        if template:
            return template.to_dict()
        return None
    
    def suggest_fields(self, data: Dict, template_name: str = None) -> List[Dict]:
        """필드 제안"""
        
        return self.data_manager.suggest_fields(data, template_name)
    
    def validate_data(self, data: Dict, template_name: str) -> tuple[bool, List[str]]:
        """데이터 검증"""
        
        template = self.data_manager.get_template(template_name)
        if not template:
            return False, [f'템플릿을 찾을 수 없습니다: {template_name}']
        
        return template.validate(data)
    
    def get_stats(self) -> Dict:
        """통계 가져오기"""
        
        stats = self.stats.copy()
        
        # 페이크 페이스 통계
        if self.fake_face:
            stats['fake_face'] = self.fake_face.get_session_stats()
        
        # 크롤러 상태
        if hasattr(self.crawler, 'get_crawler_status'):
            status = self.crawler.get_crawler_status()
            if status:
                stats['crawler_status'] = status
        
        return stats
    
    def list_available_scenarios(self) -> List[Dict]:
        """사용 가능한 시나리오 목록"""
        
        scenarios = []
        for scenario in self.scenario_manager.list_scenarios():
            scenarios.append({
                'name': scenario.name,
                'type': scenario.scenario_type.value,
                'description': scenario.description,
                'days': scenario.days,
                'max_reports': scenario.max_reports,
                'keywords': scenario.keywords,
                'stock_codes': scenario.stock_codes
            })
        
        return scenarios
    
    def list_available_templates(self) -> List[Dict]:
        """사용 가능한 템플릿 목록"""
        
        templates = []
        for name in self.data_manager.list_templates():
            template = self.data_manager.get_template(name)
            if template:
                templates.append({
                    'name': template.name,
                    'description': template.description,
                    'field_count': len(template.fields),
                    'version': template.version
                })
        
        return templates

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("통합 크롤러 매니저 테스트")
    print("="*60)
    print()
    
    # 매니저 생성
    manager = IntegratedCrawlerManager(
        use_fake_face=True,
        fake_face_profile='researcher',
        use_adaptive_parsing=True
    )
    
    # 사용 가능한 시나리오
    print("사용 가능한 시나리오:")
    scenarios = manager.list_available_scenarios()
    for i, scenario in enumerate(scenarios[:5], 1):
        print(f"  {i}. [{scenario['type']}] {scenario['name']}")
        print(f"     {scenario['description']}")
    
    # 사용 가능한 템플릿
    print("\n사용 가능한 템플릿:")
    templates = manager.list_available_templates()
    for template in templates:
        print(f"  - {template['name']}: {template['description']} ({template['field_count']}개 필드)")
    
    # 시나리오 제안
    print("\n시나리오 제안 테스트:")
    requirements = {
        'keywords': ['AI', '반도체'],
        'days': 7
    }
    suggestions = manager.suggest_scenarios(requirements)
    print(f"요구사항: {requirements}")
    print(f"제안: {len(suggestions)}개")
    for sug in suggestions:
        print(f"  - {sug['name']}: {sug['description']}")
    
    # 통계
    print("\n통계:")
    stats = manager.get_stats()
    print(f"  실행된 시나리오: {stats['total_scenarios_run']}개")
    print(f"  수집된 보고서: {stats['total_reports_collected']}개")
    if 'fake_face' in stats:
        print(f"  페이크 페이스 요청 수: {stats['fake_face']['request_count']}개")
    
    print("\n✅ 테스트 완료!")



