# structure_monitor.py
"""
구조 변경 모니터링 시스템

주기적으로 사이트 구조를 확인하고 변경을 감지
"""

import sys
import io
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from site_structure_analyzer import SiteStructureAnalyzer, StructureChangeDetector, SiteStructure
from adaptive_parser import StructureChangeHandler

class StructureMonitor:
    """구조 변경 모니터"""
    
    def __init__(self, base_url: str, check_interval_hours: int = 24):
        self.base_url = base_url
        self.check_interval_hours = check_interval_hours
        self.logger = logging.getLogger(__name__)
        
        self.analyzer = SiteStructureAnalyzer(base_url)
        self.detector = StructureChangeDetector()
        self.handler = StructureChangeHandler()
        
        # 구조 저장 디렉토리
        self.structure_dir = Path("site_structures")
        self.structure_dir.mkdir(exist_ok=True)
    
    def get_latest_structure(self) -> Optional[SiteStructure]:
        """최신 구조 가져오기"""
        
        # 구조 파일 찾기
        pattern = f"structure_*_{self.analyzer.domain}_*.json"
        structure_files = list(self.structure_dir.glob(pattern))
        
        if not structure_files:
            return None
        
        # 가장 최근 파일
        latest_file = max(structure_files, key=lambda p: p.stat().st_mtime)
        
        return self.detector.load_structure(str(latest_file))
    
    def check_structure(self, test_urls: List[str] = None) -> Dict:
        """구조 확인 및 변경 감지"""
        
        self.logger.info(f"🔍 구조 확인 시작: {self.base_url}")
        
        # 1. 현재 구조 분석
        current_structure = self.analyzer.analyze()
        
        # 2. 이전 구조 로드
        previous_structure = self.get_latest_structure()
        
        # 3. 변경 감지
        if previous_structure:
            changes = self.detector.detect_changes(current_structure, previous_structure)
            
            if changes.get('has_changes'):
                self.logger.warning("⚠️  구조 변경 감지!")
                
                # 변경 처리
                if test_urls:
                    handling_result = self.handler.handle_structure_change(
                        previous_structure,
                        current_structure,
                        test_urls
                    )
                    changes['handling'] = handling_result
                
                # 알림
                self._notify_changes(changes)
            else:
                self.logger.info("✅ 구조 변경 없음")
        else:
            self.logger.info("ℹ️  이전 구조가 없습니다. (첫 분석)")
            changes = {'has_changes': False, 'message': '첫 분석'}
        
        # 4. 현재 구조 저장
        timestamp = current_structure.timestamp.strftime('%Y%m%d_%H%M%S')
        filename = self.structure_dir / f"structure_{current_structure.domain}_{timestamp}.json"
        self.detector.save_structure(current_structure, str(filename))
        
        return {
            'timestamp': datetime.now().isoformat(),
            'changes': changes,
            'structure': current_structure
        }
    
    def _notify_changes(self, changes: Dict):
        """변경 사항 알림"""
        
        self.logger.warning("="*60)
        self.logger.warning("구조 변경 알림")
        self.logger.warning("="*60)
        
        if changes.get('menu_changes'):
            self.logger.warning("메뉴 변경:")
            for change in changes['menu_changes']:
                self.logger.warning(f"  - {change['type']}: {change['count']}개")
        
        if changes.get('link_pattern_changes'):
            self.logger.warning("링크 패턴 변경:")
            for change in changes['link_pattern_changes']:
                self.logger.warning(f"  - {change['type']}: {change.get('types', [])}")
        
        if changes.get('data_structure_changes'):
            self.logger.warning("데이터 구조 변경:")
            for change in changes['data_structure_changes']:
                self.logger.warning(f"  - {change['type']}: {change.get('types', [])}")
        
        if changes.get('handling'):
            recommendations = changes['handling'].get('recommendations', [])
            if recommendations:
                self.logger.warning("\n추천 조치:")
                for rec in recommendations:
                    self.logger.warning(f"  {rec}")
    
    def monitor_loop(self, test_urls: List[str] = None, run_once: bool = False):
        """모니터링 루프"""
        
        self.logger.info(f"🚀 구조 모니터링 시작 (간격: {self.check_interval_hours}시간)")
        
        while True:
            try:
                result = self.check_structure(test_urls)
                
                if run_once:
                    break
                
                # 다음 확인까지 대기
                self.logger.info(f"⏰ 다음 확인까지 {self.check_interval_hours}시간 대기...")
                time.sleep(self.check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                self.logger.info("⚠️  사용자에 의해 중단되었습니다.")
                break
            except Exception as e:
                self.logger.error(f"❌ 모니터링 오류: {e}")
                if run_once:
                    break
                time.sleep(3600)  # 1시간 후 재시도

# ============================================================
# 크롤러 통합
# ============================================================

class AdaptiveCrawler38Com:
    """적응형 38커뮤니케이션 크롤러"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 모니터 초기화
        self.monitor = StructureMonitor("http://www.38.co.kr")
        
        # 적응형 파서
        from adaptive_parser import AdaptiveParser
        self.parser = AdaptiveParser()
        
        # 최신 구조 로드
        self.current_structure = self.monitor.get_latest_structure()
        if self.current_structure:
            self.parser.structure = self.current_structure
            self.logger.info("✅ 사이트 구조 로드 완료")
        else:
            self.logger.warning("⚠️  사이트 구조가 없습니다. 첫 분석을 실행하세요.")
    
    def update_structure(self):
        """구조 업데이트"""
        
        self.logger.info("구조 업데이트 중...")
        result = self.monitor.check_structure()
        
        if result['changes'].get('has_changes'):
            self.logger.warning("구조가 변경되었습니다. 파서를 업데이트합니다.")
            self.current_structure = result['structure']
            self.parser.structure = self.current_structure
        
        return result
    
    def parse_report(self, html: str) -> Dict:
        """보고서 파싱 (적응형)"""
        
        results = self.parser.parse(html, page_type='detail')
        
        # 결과를 딕셔너리로 변환
        parsed_data = {}
        for field, result in results.items():
            if result.success:
                parsed_data[field] = result.value
            else:
                parsed_data[field] = None
        
        return parsed_data

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("구조 변경 모니터링 시스템")
    print("="*60)
    print()
    
    # 모니터 생성
    monitor = StructureMonitor("http://www.38.co.kr", check_interval_hours=24)
    
    # 테스트 URL (선택적)
    test_urls = [
        "http://www.38.co.kr/html/news/?m=kosdaq&nkey=report",
    ]
    
    # 구조 확인 (1회)
    print("구조 확인 실행 (1회)...")
    result = monitor.check_structure(test_urls)
    
    print("\n" + "="*60)
    print("결과")
    print("="*60)
    print(f"변경 감지: {'예' if result['changes'].get('has_changes') else '아니오'}")
    
    if result['changes'].get('has_changes'):
        print("\n변경 사항:")
        changes = result['changes']
        if changes.get('menu_changes'):
            print(f"  - 메뉴: {len(changes['menu_changes'])}개 변경")
        if changes.get('link_pattern_changes'):
            print(f"  - 링크 패턴: {len(changes['link_pattern_changes'])}개 변경")
        if changes.get('data_structure_changes'):
            print(f"  - 데이터 구조: {len(changes['data_structure_changes'])}개 변경")
    
    print("\n✅ 완료!")
    print(f"\n구조 파일 저장 위치: {monitor.structure_dir}")



