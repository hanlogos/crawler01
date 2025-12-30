# run_ultimate_dashboard.py
"""
최종 통합 대시보드

사이트별 크롤링 상태, 제어, 보고서 관리, AI 인사이트를 모두 통합
"""

import sys
import io
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit, QTabWidget,
    QSplitter, QGroupBox, QCheckBox, QSpinBox, QProgressBar
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from crawler_monitoring_widget import CrawlerDashboardWidget
from crawler_manager import CrawlerManager
from site_crawling_manager import SiteCrawlingManager, SiteCrawlingState, CrawlingStatus, CrawlingMode
from report_title_manager import ReportTitleManager
from ai_insights_system import AIInsightsSystem
from integrated_crawler_manager import IntegratedCrawlerManager
import logging
from datetime import datetime
from typing import Dict

class SiteControlWidget(QWidget):
    """사이트 제어 위젯"""
    
    def __init__(self, site_manager: SiteCrawlingManager, parent=None):
        super().__init__(parent)
        self.site_manager = site_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("사이트별 크롤링 제어")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 사이트 선택
        site_layout = QHBoxLayout()
        site_layout.addWidget(QLabel("사이트:"))
        
        self.site_combo = QComboBox()
        self.update_site_list()
        site_layout.addWidget(self.site_combo)
        
        layout.addLayout(site_layout)
        
        # 상태 표시
        self.status_label = QLabel("상태: -")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
        
        # 진행 상황
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 모드 선택
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("모드:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["수동", "자동"])
        mode_layout.addWidget(self.mode_combo)
        
        layout.addLayout(mode_layout)
        
        # 제어 버튼
        button_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("▶ 시작")
        self.start_btn.clicked.connect(self.start_crawling)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ 일시정지")
        self.pause_btn.clicked.connect(self.pause_crawling)
        button_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("▶ 이어가기")
        self.resume_btn.clicked.connect(self.resume_crawling)
        button_layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("⏹ 정지")
        self.stop_btn.clicked.connect(self.stop_crawling)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addWidget(QLabel(""))  # 간격
        
        self.clear_btn = QPushButton("🗑 지우기")
        self.clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("💾 저장하기")
        self.save_btn.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 상태 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # 2초마다
    
    def update_site_list(self):
        """사이트 목록 업데이트"""
        
        self.site_combo.clear()
        states = self.site_manager.get_all_states()
        
        for state in states:
            self.site_combo.addItem(
                f"{state.site_name} ({state.site_id})",
                state.site_id
            )
    
    def get_current_site_id(self) -> str:
        """현재 선택된 사이트 ID"""
        return self.site_combo.currentData()
    
    def update_status(self):
        """상태 업데이트"""
        
        site_id = self.get_current_site_id()
        if not site_id:
            return
        
        state = self.site_manager.get_site_state(site_id)
        if not state:
            return
        
        # 상태 표시
        status_text = f"상태: {state.status.value}"
        if state.mode == CrawlingMode.AUTO:
            status_text += " (자동)"
            if state.next_run:
                status_text += f" | 다음 실행: {state.next_run.strftime('%Y-%m-%d %H:%M')}"
        else:
            status_text += " (수동)"
        
        self.status_label.setText(status_text)
        
        # 진행 상황
        if state.total_target > 0:
            progress = int((state.current_progress / state.total_target) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{state.current_progress}/{state.total_target} ({progress}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("진행 상황 없음")
        
        # 통계
        stats_text = f"수집: {state.total_collected}개 | 실패: {state.total_failed}개"
        if state.last_collected:
            stats_text += f" | 마지막: {state.last_collected.strftime('%Y-%m-%d %H:%M')}"
        
        # 버튼 상태
        self._update_button_states(state)
    
    def _update_button_states(self, state: SiteCrawlingState):
        """버튼 상태 업데이트"""
        
        if state.status == CrawlingStatus.RUNNING:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        elif state.status == CrawlingStatus.PAUSED:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        elif state.status == CrawlingStatus.STOPPED:
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:  # IDLE
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
    
    def start_crawling(self):
        """크롤링 시작"""
        
        site_id = self.get_current_site_id()
        if not site_id:
            return
        
        mode = CrawlingMode.AUTO if self.mode_combo.currentText() == "자동" else CrawlingMode.MANUAL
        
        if self.site_manager.start_crawling(site_id, mode):
            self.parent().log(f"크롤링 시작: {site_id} ({mode.value} 모드)", "INFO")
    
    def pause_crawling(self):
        """크롤링 일시정지"""
        
        site_id = self.get_current_site_id()
        if site_id and self.site_manager.pause_crawling(site_id):
            self.parent().log(f"크롤링 일시정지: {site_id}", "INFO")
    
    def resume_crawling(self):
        """크롤링 이어가기"""
        
        site_id = self.get_current_site_id()
        if site_id and self.site_manager.resume_crawling(site_id):
            self.parent().log(f"크롤링 재개: {site_id}", "INFO")
    
    def stop_crawling(self):
        """크롤링 정지"""
        
        site_id = self.get_current_site_id()
        if site_id and self.site_manager.stop_crawling(site_id):
            self.parent().log(f"크롤링 정지: {site_id}", "INFO")
    
    def clear_data(self):
        """데이터 지우기"""
        
        site_id = self.get_current_site_id()
        if site_id and self.site_manager.clear_site_data(site_id):
            self.parent().log(f"데이터 초기화: {site_id}", "INFO")
    
    def save_data(self):
        """데이터 저장"""
        
        site_id = self.get_current_site_id()
        if site_id and self.site_manager.save_site_data(site_id):
            self.parent().log(f"데이터 저장 완료: {site_id}", "SUCCESS")

class ReportListWidget(QWidget):
    """보고서 리스트 위젯"""
    
    def __init__(self, title_manager: ReportTitleManager, parent=None):
        super().__init__(parent)
        self.title_manager = title_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("수집된 보고서 목록")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 검색
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("키워드 입력...")
        self.search_input.textChanged.connect(self.search_reports)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "원본 제목", "AI 요약 제목", "키워드", "생성일"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_list)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def refresh_list(self):
        """목록 새로고침"""
        
        titles = self.title_manager.list_titles(limit=100)
        
        self.table.setRowCount(len(titles))
        
        for i, title_obj in enumerate(titles):
            # ID
            self.table.setItem(i, 0, QTableWidgetItem(title_obj.report_id))
            
            # 원본 제목
            original_item = QTableWidgetItem(title_obj.original_title)
            original_item.setToolTip(title_obj.original_title)
            self.table.setItem(i, 1, original_item)
            
            # AI 요약 제목
            ai_title = title_obj.ai_summary_title or "(생성 안 됨)"
            ai_item = QTableWidgetItem(ai_title)
            if title_obj.ai_summary_title:
                ai_item.setForeground(QColor(0, 128, 0))  # 녹색
            self.table.setItem(i, 2, ai_item)
            
            # 키워드
            keywords = ", ".join(title_obj.keywords[:3])
            self.table.setItem(i, 3, QTableWidgetItem(keywords))
            
            # 생성일
            date_str = title_obj.created_at.strftime('%Y-%m-%d %H:%M') if title_obj.created_at else "-"
            self.table.setItem(i, 4, QTableWidgetItem(date_str))
        
        self.table.resizeColumnsToContents()
    
    def search_reports(self):
        """보고서 검색"""
        
        keyword = self.search_input.text()
        if not keyword:
            self.refresh_list()
            return
        
        titles = self.title_manager.search_titles(keyword)
        
        self.table.setRowCount(len(titles))
        
        for i, title_obj in enumerate(titles):
            self.table.setItem(i, 0, QTableWidgetItem(title_obj.report_id))
            self.table.setItem(i, 1, QTableWidgetItem(title_obj.original_title))
            
            ai_title = title_obj.ai_summary_title or "(생성 안 됨)"
            self.table.setItem(i, 2, QTableWidgetItem(ai_title))
            
            keywords = ", ".join(title_obj.keywords[:3])
            self.table.setItem(i, 3, QTableWidgetItem(keywords))
            
            date_str = title_obj.created_at.strftime('%Y-%m-%d %H:%M') if title_obj.created_at else "-"
            self.table.setItem(i, 4, QTableWidgetItem(date_str))

class InsightsWidget(QWidget):
    """AI 인사이트 위젯"""
    
    def __init__(self, insights_system: AIInsightsSystem, parent=None):
        super().__init__(parent)
        self.insights_system = insights_system
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🤖 AI 인사이트")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 카테고리별 탭
        tabs = QTabWidget()
        
        # 운영 인사이트
        self.operation_text = QTextEdit()
        self.operation_text.setReadOnly(True)
        tabs.addTab(self.operation_text, "운영")
        
        # 데이터 관리 인사이트
        self.data_mgmt_text = QTextEdit()
        self.data_mgmt_text.setReadOnly(True)
        tabs.addTab(self.data_mgmt_text, "데이터 관리")
        
        # 데이터 활용 인사이트
        self.data_util_text = QTextEdit()
        self.data_util_text.setReadOnly(True)
        tabs.addTab(self.data_util_text, "데이터 활용")
        
        layout.addWidget(tabs)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 인사이트 새로고침")
        refresh_btn.clicked.connect(self.refresh_insights)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def refresh_insights(self):
        """인사이트 새로고침"""
        
        # 통계 수집 (실제로는 실제 데이터에서 가져와야 함)
        operation_stats = {
            'total_requests': 100,
            'success_count': 85,
            'total_collected': 50,
            'total_time': 2000
        }
        
        data_stats = {
            'total_reports': len(self.parent().title_manager.titles),
            'duplicate_rate': 0.1,
            'incomplete_rate': 0.15
        }
        
        analysis_stats = {
            'analyzed_count': 30,
            'total_count': 50,
            'avatar_count': 6
        }
        
        # 인사이트 생성
        insights = self.insights_system.generate_comprehensive_insights(
            operation_stats,
            data_stats,
            analysis_stats
        )
        
        # 표시
        self._display_insights(insights)
    
    def _display_insights(self, insights: Dict):
        """인사이트 표시"""
        
        # 운영 인사이트
        operation_text = ""
        for insight in insights.get('operation', []):
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(insight.priority, '⚪')
            operation_text += f"{priority_icon} {insight.title}\n"
            operation_text += f"   {insight.description}\n"
            if insight.actionable:
                operation_text += f"   💡 {insight.recommendation}\n"
            operation_text += "\n"
        
        self.operation_text.setText(operation_text or "인사이트가 없습니다.")
        
        # 데이터 관리 인사이트
        data_mgmt_text = ""
        for insight in insights.get('data_management', []):
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(insight.priority, '⚪')
            data_mgmt_text += f"{priority_icon} {insight.title}\n"
            data_mgmt_text += f"   {insight.description}\n"
            if insight.actionable:
                data_mgmt_text += f"   💡 {insight.recommendation}\n"
            data_mgmt_text += "\n"
        
        self.data_mgmt_text.setText(data_mgmt_text or "인사이트가 없습니다.")
        
        # 데이터 활용 인사이트
        data_util_text = ""
        for insight in insights.get('data_utilization', []):
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(insight.priority, '⚪')
            data_util_text += f"{priority_icon} {insight.title}\n"
            data_util_text += f"   {insight.description}\n"
            if insight.actionable:
                data_util_text += f"   💡 {insight.recommendation}\n"
            data_util_text += "\n"
        
        self.data_util_text.setText(data_util_text or "인사이트가 없습니다.")

class UltimateDashboard(QMainWindow):
    """최종 통합 대시보드"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("완전한 크롤러 통합 대시보드")
        self.resize(1800, 1000)
        
        # 시스템 초기화
        self.site_manager = SiteCrawlingManager()
        self.title_manager = ReportTitleManager()
        self.insights_system = AIInsightsSystem()
        self.integrated_manager = IntegratedCrawlerManager(
            use_fake_face=True,
            fake_face_profile='casual'
        )
        self.manager = CrawlerManager()
        
        # 기존 대시보드
        self.dashboard = CrawlerDashboardWidget()
        self.dashboard.set_system(self.manager)
        
        # UI 초기화
        self._init_ui()
        
        # 초기화
        self._initialize()
        
        # 타이머 설정
        self._setup_timers()
    
    def _init_ui(self):
        """UI 초기화"""
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 왼쪽: 제어 패널
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # 사이트 제어
        self.site_control = SiteControlWidget(self.site_manager, self)
        left_layout.addWidget(self.site_control)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(300)
        
        # 오른쪽: 메인 콘텐츠
        right_panel = QTabWidget()
        
        # 탭 1: 모니터링
        monitoring_tab = self.dashboard
        right_panel.addTab(monitoring_tab, "📊 모니터링")
        
        # 탭 2: 보고서 목록
        self.report_list = ReportListWidget(self.title_manager, self)
        right_panel.addTab(self.report_list, "📋 보고서 목록")
        
        # 탭 3: AI 인사이트
        self.insights_widget = InsightsWidget(self.insights_system, self)
        right_panel.addTab(self.insights_widget, "🤖 AI 인사이트")
        
        # 레이아웃
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def _initialize(self):
        """초기화"""
        
        # 사이트 등록
        site_state = self.site_manager.register_site(
            site_id="38com",
            site_name="38커뮤니케이션",
            site_url="http://www.38.co.kr",
            days=1,
            max_reports=50,
            fake_face_profile='casual'
        )
        
        # 스케줄 설정
        self.site_manager.update_schedule("38com", {
            'interval': 'daily',
            'time': '09:00'
        })
        
        # 사이트 제어 위젯 업데이트
        self.site_control.update_site_list()
        
        # 사이트 등록 (모니터링)
        if self.manager.health_monitor:
            self.dashboard.register_site('38com', self.manager.health_monitor)
        
        # 초기 로그
        self.log("시스템 초기화 완료", "SUCCESS")
        self.log("사이트 등록: 38커뮤니케이션", "INFO")
        self.log("AI 인사이트 시스템 활성화", "INFO")
        
        # 보고서 목록 새로고침
        self.report_list.refresh_list()
        
        # 인사이트 새로고침
        self.insights_widget.refresh_insights()
    
    def _setup_timers(self):
        """타이머 설정"""
        
        # 활동 시뮬레이션
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self._simulate_activity)
        self.activity_timer.start(5000)
        
        # 보고서 목록 자동 새로고침
        self.report_refresh_timer = QTimer()
        self.report_refresh_timer.timeout.connect(self.report_list.refresh_list)
        self.report_refresh_timer.start(30000)  # 30초마다
    
    def _simulate_activity(self):
        """활동 시뮬레이션"""
        
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
            
            # 보고서 제목 등록 (시뮬레이션)
            if random.random() < 0.3:  # 30% 확률
                report_id = f"RPT_{self.manager.stats['total_collected']:04d}"
                title = f"보고서 {self.manager.stats['total_collected']}"
                
                self.title_manager.register_report(
                    report_id=report_id,
                    original_title=title,
                    keywords=["테스트"]
                )
                
                # AI 제목 생성
                self.title_manager.generate_ai_title(
                    report_id,
                    metadata={'stock_name': '테스트종목'}
                )
            
            self.log(f"보고서 수집 완료: {self.manager.stats['total_collected']}개", "SUCCESS")
        else:
            self.log(f"요청 실패: HTTP {status_code}", "WARNING")
    
    def log(self, message: str, level: str = "INFO"):
        """로그 추가"""
        self.dashboard.log(message, level)

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("완전한 크롤러 통합 대시보드")
    print("="*60)
    print()
    print("위젯 창이 열립니다...")
    print()
    
    app = QApplication(sys.argv)
    
    dashboard = UltimateDashboard()
    dashboard.show()
    
    print("✅ 대시보드가 표시되었습니다!")
    print()
    print("기능:")
    print("  📊 모니터링: 실시간 크롤러 상태")
    print("  🎮 사이트 제어: 시작/일시정지/정지/이어가기/지우기/저장")
    print("  📋 보고서 목록: 수집된 보고서 및 AI 요약 제목")
    print("  🤖 AI 인사이트: 운영/데이터 관리/데이터 활용 조언")
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


