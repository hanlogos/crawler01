# crawling_scenarios.py
"""
크롤링 시나리오 시스템

다양한 수집 전략 및 시나리오 정의
"""

import sys
import io
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class ScenarioType(Enum):
    """시나리오 타입"""
    SCHEDULED = "scheduled"  # 정기 수집
    KEYWORD_BASED = "keyword_based"  # 키워드 기반
    ISSUE_TRACKING = "issue_tracking"  # 이슈 추적
    FULL_SCAN = "full_scan"  # 전체 스캔
    INCREMENTAL = "incremental"  # 증분 수집
    TARGETED = "targeted"  # 특정 대상 수집

@dataclass
class CrawlingScenario:
    """크롤링 시나리오"""
    name: str
    scenario_type: ScenarioType
    description: str
    
    # 수집 범위
    days: int = 1  # 최근 N일
    max_reports: int = 100  # 최대 수집 개수
    
    # 키워드/이슈
    keywords: List[str] = None  # 검색 키워드
    stock_codes: List[str] = None  # 특정 종목 코드
    analysts: List[str] = None  # 특정 애널리스트
    firms: List[str] = None  # 특정 증권사
    
    # 필터
    min_confidence: float = 0.0  # 최소 신뢰도
    categories: List[str] = None  # 카테고리 필터
    
    # 스케줄
    schedule: Dict = None  # {'interval': 'daily', 'time': '09:00'}
    
    # 옵션
    use_analysis: bool = True  # 분석 사용 여부
    use_ollama: bool = False  # Ollama 사용 여부
    fake_face_profile: str = 'casual'  # 페이크 페이스 프로필
    
    # 콜백
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.stock_codes is None:
            self.stock_codes = []
        if self.analysts is None:
            self.analysts = []
        if self.firms is None:
            self.firms = []
        if self.categories is None:
            self.categories = []
        if self.schedule is None:
            self.schedule = {}
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['scenario_type'] = self.scenario_type.value
        # 콜백은 직렬화 불가
        data.pop('on_progress', None)
        data.pop('on_complete', None)
        return data

class ScenarioManager:
    """시나리오 관리자"""
    
    def __init__(self):
        self.scenarios: Dict[str, CrawlingScenario] = {}
        self.logger = logging.getLogger(__name__)
        self._load_default_scenarios()
    
    def _load_default_scenarios(self):
        """기본 시나리오 로드"""
        
        # 1. 일일 정기 수집
        daily_scenario = CrawlingScenario(
            name="일일 정기 수집",
            scenario_type=ScenarioType.SCHEDULED,
            description="매일 아침 9시에 최근 1일 보고서 수집",
            days=1,
            max_reports=50,
            schedule={'interval': 'daily', 'time': '09:00'},
            use_analysis=True,
            fake_face_profile='casual'
        )
        self.scenarios["daily"] = daily_scenario
        
        # 2. 주간 전체 스캔
        weekly_scenario = CrawlingScenario(
            name="주간 전체 스캔",
            scenario_type=ScenarioType.FULL_SCAN,
            description="매주 월요일 전체 보고서 스캔",
            days=7,
            max_reports=500,
            schedule={'interval': 'weekly', 'day': 'monday', 'time': '10:00'},
            use_analysis=True,
            fake_face_profile='thorough'
        )
        self.scenarios["weekly"] = weekly_scenario
        
        # 3. 키워드 기반 수집
        keyword_scenario = CrawlingScenario(
            name="키워드 기반 수집",
            scenario_type=ScenarioType.KEYWORD_BASED,
            description="특정 키워드가 포함된 보고서만 수집",
            days=30,
            max_reports=200,
            keywords=["AI", "반도체", "HBM"],
            use_analysis=True,
            fake_face_profile='researcher'
        )
        self.scenarios["keyword"] = keyword_scenario
        
        # 4. 이슈 추적
        issue_scenario = CrawlingScenario(
            name="이슈 추적",
            scenario_type=ScenarioType.ISSUE_TRACKING,
            description="특정 이슈/이벤트 관련 보고서 추적",
            days=7,
            max_reports=100,
            keywords=["실적 발표", "목표가 상향", "신규 수주"],
            use_analysis=True,
            fake_face_profile='researcher'
        )
        self.scenarios["issue"] = issue_scenario
        
        # 5. 특정 종목 추적
        stock_scenario = CrawlingScenario(
            name="특정 종목 추적",
            scenario_type=ScenarioType.TARGETED,
            description="특정 종목의 모든 보고서 수집",
            days=90,
            max_reports=1000,
            stock_codes=["005930", "000660"],  # 삼성전자, SK하이닉스
            use_analysis=True,
            fake_face_profile='thorough'
        )
        self.scenarios["stock"] = stock_scenario
        
        # 6. 증분 수집
        incremental_scenario = CrawlingScenario(
            name="증분 수집",
            scenario_type=ScenarioType.INCREMENTAL,
            description="이전 수집 이후 새로 추가된 보고서만 수집",
            days=1,
            max_reports=50,
            use_analysis=True,
            fake_face_profile='quick_scan'
        )
        self.scenarios["incremental"] = incremental_scenario
        
        # 7. 특정 애널리스트 추적
        analyst_scenario = CrawlingScenario(
            name="특정 애널리스트 추적",
            scenario_type=ScenarioType.TARGETED,
            description="특정 애널리스트의 보고서만 수집",
            days=180,
            max_reports=500,
            analysts=["홍길동", "김철수"],
            firms=["삼성증권", "KB증권"],
            use_analysis=True,
            fake_face_profile='researcher'
        )
        self.scenarios["analyst"] = analyst_scenario
    
    def register_scenario(self, scenario: CrawlingScenario):
        """시나리오 등록"""
        self.scenarios[scenario.name] = scenario
        self.logger.info(f"시나리오 등록: {scenario.name}")
    
    def get_scenario(self, name: str) -> Optional[CrawlingScenario]:
        """시나리오 가져오기"""
        return self.scenarios.get(name)
    
    def list_scenarios(self) -> List[CrawlingScenario]:
        """시나리오 목록"""
        return list(self.scenarios.values())
    
    def suggest_scenario(
        self,
        requirements: Dict[str, Any]
    ) -> List[CrawlingScenario]:
        """요구사항에 맞는 시나리오 제안"""
        
        suggestions = []
        
        # 키워드가 있으면 키워드 기반
        if requirements.get('keywords'):
            suggestions.append(self.scenarios.get("keyword"))
        
        # 종목 코드가 있으면 종목 추적
        if requirements.get('stock_codes'):
            suggestions.append(self.scenarios.get("stock"))
        
        # 애널리스트가 있으면 애널리스트 추적
        if requirements.get('analysts'):
            suggestions.append(self.scenarios.get("analyst"))
        
        # 이슈 추적이 필요하면
        if requirements.get('track_issues'):
            suggestions.append(self.scenarios.get("issue"))
        
        # 기본: 일일 수집
        if not suggestions:
            suggestions.append(self.scenarios.get("daily"))
        
        # None 제거
        suggestions = [s for s in suggestions if s is not None]
        
        return suggestions
    
    def create_custom_scenario(
        self,
        name: str,
        requirements: Dict[str, Any]
    ) -> CrawlingScenario:
        """커스텀 시나리오 생성"""
        
        # 기본값
        scenario_type = ScenarioType.SCHEDULED
        if requirements.get('keywords'):
            scenario_type = ScenarioType.KEYWORD_BASED
        elif requirements.get('stock_codes'):
            scenario_type = ScenarioType.TARGETED
        elif requirements.get('track_issues'):
            scenario_type = ScenarioType.ISSUE_TRACKING
        
        scenario = CrawlingScenario(
            name=name,
            scenario_type=scenario_type,
            description=requirements.get('description', '커스텀 시나리오'),
            days=requirements.get('days', 1),
            max_reports=requirements.get('max_reports', 100),
            keywords=requirements.get('keywords', []),
            stock_codes=requirements.get('stock_codes', []),
            analysts=requirements.get('analysts', []),
            firms=requirements.get('firms', []),
            categories=requirements.get('categories', []),
            use_analysis=requirements.get('use_analysis', True),
            use_ollama=requirements.get('use_ollama', False),
            fake_face_profile=requirements.get('fake_face_profile', 'casual')
        )
        
        return scenario

# ============================================================
# 시나리오 실행기
# ============================================================

class ScenarioExecutor:
    """시나리오 실행기"""
    
    def __init__(self, crawler, fake_face_system=None):
        self.crawler = crawler
        self.fake_face = fake_face_system
        self.logger = logging.getLogger(__name__)
    
    def execute(self, scenario: CrawlingScenario) -> Dict:
        """시나리오 실행"""
        
        self.logger.info(f"시나리오 실행 시작: {scenario.name}")
        
        # 페이크 페이스 적용
        if self.fake_face:
            self.fake_face.profile = self.fake_face.PROFILES.get(
                scenario.fake_face_profile,
                self.fake_face.PROFILES['casual']
            )
        
        # 필터 함수 생성
        filter_func = self._create_filter(scenario)
        
        # 크롤링 실행
        try:
            reports = self.crawler.crawl_recent_reports(
                days=scenario.days,
                max_reports=scenario.max_reports
            )
            
            # 필터 적용
            if filter_func:
                reports = [r for r in reports if filter_func(r)]
            
            # 진행 콜백
            if scenario.on_progress:
                scenario.on_progress(len(reports), scenario.max_reports)
            
            # 완료 콜백
            if scenario.on_complete:
                scenario.on_complete(reports)
            
            result = {
                'success': True,
                'scenario': scenario.name,
                'reports_count': len(reports),
                'reports': reports
            }
            
            self.logger.info(f"시나리오 실행 완료: {scenario.name} ({len(reports)}개 수집)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"시나리오 실행 실패: {e}")
            return {
                'success': False,
                'scenario': scenario.name,
                'error': str(e)
            }
    
    def _create_filter(self, scenario: CrawlingScenario) -> Optional[Callable]:
        """필터 함수 생성"""
        
        filters = []
        
        # 키워드 필터
        if scenario.keywords:
            def keyword_filter(report):
                text = f"{report.title} {report.stock_name}".lower()
                return any(kw.lower() in text for kw in scenario.keywords)
            filters.append(keyword_filter)
        
        # 종목 코드 필터
        if scenario.stock_codes:
            def stock_filter(report):
                return report.stock_code in scenario.stock_codes
            filters.append(stock_filter)
        
        # 애널리스트 필터
        if scenario.analysts:
            def analyst_filter(report):
                return report.analyst_name in scenario.analysts
            filters.append(analyst_filter)
        
        # 증권사 필터
        if scenario.firms:
            def firm_filter(report):
                return report.firm in scenario.firms
            filters.append(firm_filter)
        
        # 필터 결합
        if filters:
            def combined_filter(report):
                return all(f(report) for f in filters)
            return combined_filter
        
        return None

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("크롤링 시나리오 시스템 테스트")
    print("="*60)
    print()
    
    manager = ScenarioManager()
    
    # 시나리오 목록
    print("등록된 시나리오:")
    for scenario in manager.list_scenarios():
        print(f"\n  [{scenario.scenario_type.value}] {scenario.name}")
        print(f"    설명: {scenario.description}")
        print(f"    범위: 최근 {scenario.days}일, 최대 {scenario.max_reports}개")
        if scenario.keywords:
            print(f"    키워드: {', '.join(scenario.keywords)}")
        if scenario.stock_codes:
            print(f"    종목: {', '.join(scenario.stock_codes)}")
        if scenario.schedule:
            print(f"    스케줄: {scenario.schedule}")
    
    # 시나리오 제안
    print("\n" + "="*60)
    print("시나리오 제안 테스트")
    print("="*60)
    
    requirements = {
        'keywords': ['AI', '반도체'],
        'days': 7,
        'max_reports': 50
    }
    
    suggestions = manager.suggest_scenario(requirements)
    print(f"\n요구사항: {requirements}")
    print(f"\n제안된 시나리오: {len(suggestions)}개")
    for sug in suggestions:
        print(f"  - {sug.name}: {sug.description}")
    
    # 커스텀 시나리오 생성
    print("\n" + "="*60)
    print("커스텀 시나리오 생성")
    print("="*60)
    
    custom_req = {
        'description': '삼성전자 AI 관련 보고서만 수집',
        'days': 30,
        'max_reports': 100,
        'keywords': ['AI', '삼성전자'],
        'stock_codes': ['005930'],
        'use_analysis': True,
        'fake_face_profile': 'researcher'
    }
    
    custom_scenario = manager.create_custom_scenario("삼성전자 AI 추적", custom_req)
    print(f"\n생성된 시나리오: {custom_scenario.name}")
    print(f"  타입: {custom_scenario.scenario_type.value}")
    print(f"  키워드: {custom_scenario.keywords}")
    print(f"  종목: {custom_scenario.stock_codes}")
    
    print("\n✅ 테스트 완료!")



