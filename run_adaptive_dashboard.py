# run_adaptive_dashboard.py
"""
적응형 시스템 통합 대시보드

사이트 구조, 적응형 파서, 모니터링 정보를 통합 표시
"""

import sys
import io
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from crawler_monitoring_widget import CrawlerDashboardWidget
from crawler_manager import CrawlerManager
from structure_monitor import StructureMonitor
from crawler_38com_adaptive import AdaptiveThirtyEightComCrawler
import logging

class AdaptiveDashboard(QMainWindow):
    """적응형 시스템 통합 대시보드"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("적응형 크롤러 모니터링 대시보드")
        self.resize(1400, 900)
        
        # 컴포넌트 초기화
        self.manager = CrawlerManager()
        self.monitor = StructureMonitor("http://www.38.co.kr")
        self.crawler = AdaptiveThirtyEightComCrawler(
            delay=3.0,
            use_adaptive=True,
            use_adaptive_parsing=True
        )
        
        # 기존 대시보드 위젯
        self.dashboard = CrawlerDashboardWidget()
        self.dashboard.set_system(self.manager)
        
        # 구조 정보 위젯
        self.structure_widget = self._create_structure_widget()
        
        # 메인 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 상단: 구조 정보
        main_layout.addWidget(self.structure_widget)
        
        # 하단: 기존 대시보드
        main_layout.addWidget(self.dashboard)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 초기화
        self._initialize()
        
        # 타이머 설정
        self._setup_timers()
    
    def _create_structure_widget(self) -> QWidget:
        """구조 정보 위젯 생성"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🔍 사이트 구조 정보")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 구조 정보 텍스트
        self.structure_text = QTextEdit()
        self.structure_text.setMaximumHeight(150)
        self.structure_text.setReadOnly(True)
        layout.addWidget(self.structure_text)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.update_structure_btn = QPushButton("구조 업데이트")
        self.update_structure_btn.clicked.connect(self.update_structure)
        button_layout.addWidget(self.update_structure_btn)
        
        self.check_changes_btn = QPushButton("변경 확인")
        self.check_changes_btn.clicked.connect(self.check_structure_changes)
        button_layout.addWidget(self.check_changes_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _initialize(self):
        """초기화"""
        
        # 구조 정보 로드
        structure = self.monitor.get_latest_structure()
        if structure:
            self._update_structure_display(structure)
        else:
            self.structure_text.setText("구조 정보가 없습니다. '구조 업데이트' 버튼을 클릭하세요.")
        
        # 사이트 등록
        if self.manager.health_monitor:
            self.dashboard.register_site('38com', self.manager.health_monitor)
        
        # 초기 로그
        self.dashboard.log("시스템 초기화 완료", "SUCCESS")
        self.dashboard.log("적응형 크롤러 활성화", "INFO")
        if structure:
            self.dashboard.log(f"사이트 구조 로드 완료 (메뉴: {len(structure.menus)}개)", "INFO")
        else:
            self.dashboard.log("사이트 구조 분석 필요", "WARNING")
    
    def _update_structure_display(self, structure):
        """구조 정보 표시 업데이트"""
        
        info = f"""
도메인: {structure.domain}
메뉴 수: {len(structure.menus)}개
링크 패턴: {len(structure.link_patterns)}개
데이터 구조: {len(structure.data_structures)}개
체크섬: {structure.checksum[:16]}...
마지막 업데이트: {structure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        self.structure_text.setText(info)
    
    def update_structure(self):
        """구조 업데이트"""
        
        self.dashboard.log("구조 분석 시작...", "INFO")
        self.update_structure_btn.setEnabled(False)
        
        try:
            result = self.monitor.check_structure()
            structure = result['structure']
            
            self._update_structure_display(structure)
            
            if result['changes'].get('has_changes'):
                self.dashboard.log("⚠️  구조 변경 감지!", "WARNING")
                
                changes = result['changes']
                if changes.get('menu_changes'):
                    self.dashboard.log(f"  - 메뉴 변경: {len(changes['menu_changes'])}개", "WARNING")
                if changes.get('link_pattern_changes'):
                    self.dashboard.log(f"  - 링크 패턴 변경: {len(changes['link_pattern_changes'])}개", "WARNING")
                if changes.get('data_structure_changes'):
                    self.dashboard.log(f"  - 데이터 구조 변경: {len(changes['data_structure_changes'])}개", "WARNING")
                
                # 적응형 파서 업데이트
                self.crawler.parser.structure = structure
                self.dashboard.log("적응형 파서 업데이트 완료", "SUCCESS")
            else:
                self.dashboard.log("✅ 구조 변경 없음", "SUCCESS")
            
        except Exception as e:
            self.dashboard.log(f"❌ 구조 업데이트 실패: {e}", "ERROR")
        finally:
            self.update_structure_btn.setEnabled(True)
    
    def check_structure_changes(self):
        """구조 변경 확인"""
        
        self.dashboard.log("구조 변경 확인 중...", "INFO")
        
        try:
            result = self.monitor.check_structure()
            
            if result['changes'].get('has_changes'):
                self.dashboard.log("⚠️  구조 변경이 감지되었습니다!", "WARNING")
            else:
                self.dashboard.log("✅ 구조 변경 없음", "SUCCESS")
            
            self._update_structure_display(result['structure'])
            
        except Exception as e:
            self.dashboard.log(f"❌ 변경 확인 실패: {e}", "ERROR")
    
    def _setup_timers(self):
        """타이머 설정"""
        
        # 크롤러 활동 시뮬레이션 (5초마다)
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self._simulate_activity)
        self.activity_timer.start(5000)
        
        # 구조 모니터링 (30분마다, 선택적)
        # self.structure_timer = QTimer()
        # self.structure_timer.timeout.connect(self.check_structure_changes)
        # self.structure_timer.start(1800000)  # 30분
    
    def _simulate_activity(self):
        """크롤러 활동 시뮬레이션"""
        
        # 요청 시뮬레이션
        success = random.random() < 0.85
        response_time = random.uniform(0.5, 3.0)
        status_code = 200 if success else random.choice([403, 429, 500])
        
        if self.manager.health_monitor:
            self.manager.health_monitor.record_request(
                success=success,
                response_time=response_time,
                status_code=status_code
            )
        
        # 통계 업데이트
        if success:
            self.manager.stats['total_collected'] += 1
            self.dashboard.log(f"보고서 수집 완료: {self.manager.stats['total_collected']}개", "SUCCESS")
        else:
            self.dashboard.log(f"요청 실패: HTTP {status_code}", "WARNING")
        
        # 크롤러 상태 업데이트
        if self.manager.stats['total_collected'] % 5 == 0:
            self.manager.update_crawler_status('working', completed=self.manager.stats['total_collected'])
        else:
            self.manager.update_crawler_status('idle', completed=self.manager.stats['total_collected'])

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("적응형 크롤러 모니터링 대시보드")
    print("="*60)
    print()
    print("위젯 창이 열립니다...")
    print("창을 닫으면 프로그램이 종료됩니다.")
    print()
    
    app = QApplication(sys.argv)
    
    dashboard = AdaptiveDashboard()
    dashboard.show()
    
    print("✅ 대시보드가 표시되었습니다!")
    print()
    print("기능:")
    print("  - 사이트 구조 정보: 구조 분석 및 변경 감지")
    print("  - 사이트 건강도: 실시간 상태 모니터링")
    print("  - 크롤러 상태: 작업 진행 상황")
    print("  - 전체 통계: 수집/검증 통계")
    print("  - 활동 로그: 실시간 로그 표시")
    print()
    print("5초마다 새로운 요청이 시뮬레이션됩니다.")
    print()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()



