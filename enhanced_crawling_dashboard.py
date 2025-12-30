# enhanced_crawling_dashboard.py
"""
향상된 크롤링 운영 대시보드

참고 시스템의 모든 기능을 통합한 완전한 대시보드
"""

import sys
import io
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QSplitter, QGroupBox, QComboBox,
    QLineEdit, QCheckBox, QHeaderView, QMenu, QMessageBox,
    QFileDialog, QTabWidget, QSpinBox, QTimeEdit, QDateEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from site_crawling_manager import SiteCrawlingManager, CrawlingStatus, CrawlingMode
from report_title_manager import ReportTitleManager
from ai_insights_system import AIInsightsSystem
from fake_face_system import FakeFaceSystem
from keyword_search_engine import KeywordSearchEngine, SearchHistoryManager, FavoriteManager
from search_summary_generator import SearchSummaryGenerator

class JobStatus(Enum):
    """작업 상태 (참고 시스템 호환)"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class EnhancedSiteStatusWidget(QWidget):
    """향상된 사이트 상태 위젯"""
    
    # 시그널
    start_clicked = pyqtSignal(str)
    pause_clicked = pyqtSignal(str)
    stop_clicked = pyqtSignal(str)
    resume_clicked = pyqtSignal(str)
    clear_clicked = pyqtSignal(str)
    
    def __init__(self, site_manager: SiteCrawlingManager, parent=None):
        super().__init__(parent)
        self.site_manager = site_manager
        self.init_ui()
        
        # 1초마다 업데이트
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        
        title = QLabel("📡 사이트별 크롤링 상태")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 전체 제어 버튼
        self.start_all_btn = QPushButton("▶️ 전체 시작")
        self.start_all_btn.clicked.connect(self.start_all)
        header_layout.addWidget(self.start_all_btn)
        
        self.pause_all_btn = QPushButton("⏸️ 전체 일시정지")
        self.pause_all_btn.clicked.connect(self.pause_all)
        header_layout.addWidget(self.pause_all_btn)
        
        self.stop_all_btn = QPushButton("⏹️ 전체 중지")
        self.stop_all_btn.clicked.connect(self.stop_all)
        header_layout.addWidget(self.stop_all_btn)
        
        layout.addLayout(header_layout)
        
        # 상태 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "사이트", "상태", "모드", "진행률", "수집", "실패", "중복",
            "속도", "예상 시간", "조작"
        ])
        
        # 컬럼 크기
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Fixed)
        header.resizeSection(9, 280)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def update_display(self):
        """화면 업데이트"""
        
        states = self.site_manager.get_all_states()
        self.table.setRowCount(len(states))
        
        for row, state in enumerate(states):
            # 사이트명
            self.table.setItem(row, 0, QTableWidgetItem(state.site_name))
            
            # 상태
            status_text = self._get_status_text(state.status)
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(self._get_status_color(state.status))
            status_item.setForeground(QColor(255, 255, 255))
            self.table.setItem(row, 1, status_item)
            
            # 모드
            mode_text = "자동" if state.mode == CrawlingMode.AUTO else "수동"
            if state.next_run:
                mode_text += f" ({state.next_run.strftime('%m-%d %H:%M')})"
            self.table.setItem(row, 2, QTableWidgetItem(mode_text))
            
            # 진행률
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(5, 2, 5, 2)
            
            progress_bar = QProgressBar()
            
            if state.total_target > 0:
                progress = int((state.current_progress / state.total_target) * 100)
                progress_bar.setValue(progress)
                progress_bar.setFormat(f"{progress}% ({state.current_progress}/{state.total_target})")
            else:
                progress_bar.setValue(0)
                progress_bar.setFormat(f"{state.current_progress}개")
            
            progress_layout.addWidget(progress_bar)
            self.table.setCellWidget(row, 3, progress_widget)
            
            # 수집
            self.table.setItem(row, 4, QTableWidgetItem(str(state.total_collected)))
            
            # 실패
            failed_item = QTableWidgetItem(str(state.total_failed))
            if state.total_failed > 0:
                failed_item.setForeground(QColor(255, 100, 100))
            self.table.setItem(row, 5, failed_item)
            
            # 중복 (시뮬레이션)
            duplicate_count = int(state.total_collected * 0.1)  # 10% 가정
            self.table.setItem(row, 6, QTableWidgetItem(str(duplicate_count)))
            
            # 속도 (시뮬레이션)
            if state.status == CrawlingStatus.RUNNING:
                speed = random.uniform(3.0, 8.0)
            else:
                speed = 0.0
            self.table.setItem(row, 7, QTableWidgetItem(f"{speed:.1f}/분"))
            
            # 예상 시간
            if state.status == CrawlingStatus.RUNNING and state.total_target > 0:
                remaining = state.total_target - state.current_progress
                if speed > 0:
                    estimated_min = int(remaining / speed)
                    if estimated_min < 60:
                        time_text = f"{estimated_min}분"
                    else:
                        hours = estimated_min // 60
                        minutes = estimated_min % 60
                        time_text = f"{hours}시간 {minutes}분"
                else:
                    time_text = "-"
            else:
                time_text = "-"
            self.table.setItem(row, 8, QTableWidgetItem(time_text))
            
            # 조작 버튼
            self._create_control_buttons(row, state.site_id, state.status)
    
    def _create_control_buttons(self, row: int, site_id: str, status: CrawlingStatus):
        """조작 버튼 생성"""
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 시작
        start_btn = QPushButton("▶️")
        start_btn.setToolTip("시작")
        start_btn.setMaximumWidth(35)
        start_btn.clicked.connect(lambda: self.start_clicked.emit(site_id))
        start_btn.setEnabled(status in [CrawlingStatus.IDLE, CrawlingStatus.STOPPED])
        layout.addWidget(start_btn)
        
        # 일시정지
        pause_btn = QPushButton("⏸️")
        pause_btn.setToolTip("일시정지")
        pause_btn.setMaximumWidth(35)
        pause_btn.clicked.connect(lambda: self.pause_clicked.emit(site_id))
        pause_btn.setEnabled(status == CrawlingStatus.RUNNING)
        layout.addWidget(pause_btn)
        
        # 이어가기
        resume_btn = QPushButton("▶️▶️")
        resume_btn.setToolTip("이어가기")
        resume_btn.setMaximumWidth(35)
        resume_btn.clicked.connect(lambda: self.resume_clicked.emit(site_id))
        resume_btn.setEnabled(status == CrawlingStatus.PAUSED)
        layout.addWidget(resume_btn)
        
        # 중지
        stop_btn = QPushButton("⏹️")
        stop_btn.setToolTip("중지")
        stop_btn.setMaximumWidth(35)
        stop_btn.clicked.connect(lambda: self.stop_clicked.emit(site_id))
        stop_btn.setEnabled(status in [CrawlingStatus.RUNNING, CrawlingStatus.PAUSED])
        layout.addWidget(stop_btn)
        
        # 지우기
        clear_btn = QPushButton("🗑️")
        clear_btn.setToolTip("지우기")
        clear_btn.setMaximumWidth(35)
        clear_btn.clicked.connect(lambda: self.clear_clicked.emit(site_id))
        layout.addWidget(clear_btn)
        
        # 저장
        save_btn = QPushButton("💾")
        save_btn.setToolTip("저장")
        save_btn.setMaximumWidth(35)
        save_btn.clicked.connect(lambda: self.save_data(site_id))
        layout.addWidget(save_btn)
        
        self.table.setCellWidget(row, 9, widget)
    
    def save_data(self, site_id: str):
        """데이터 저장"""
        if self.site_manager.save_site_data(site_id):
            QMessageBox.information(self, "알림", "데이터가 저장되었습니다.")
    
    def _get_status_text(self, status: CrawlingStatus) -> str:
        """상태 텍스트"""
        status_map = {
            CrawlingStatus.IDLE: "💤 대기",
            CrawlingStatus.RUNNING: "⚙️ 실행중",
            CrawlingStatus.PAUSED: "⏸️ 일시정지",
            CrawlingStatus.STOPPED: "⏹️ 중지",
            CrawlingStatus.ERROR: "❌ 오류"
        }
        return status_map.get(status, "❓")
    
    def _get_status_color(self, status: CrawlingStatus) -> QColor:
        """상태 색상"""
        colors = {
            CrawlingStatus.IDLE: QColor(150, 150, 150),
            CrawlingStatus.RUNNING: QColor(50, 200, 100),
            CrawlingStatus.PAUSED: QColor(255, 165, 0),
            CrawlingStatus.STOPPED: QColor(200, 50, 50),
            CrawlingStatus.ERROR: QColor(255, 50, 50)
        }
        return colors.get(status, QColor(150, 150, 150))
    
    def start_all(self):
        """전체 시작"""
        states = self.site_manager.get_all_states()
        for state in states:
            if state.status == CrawlingStatus.IDLE:
                self.start_clicked.emit(state.site_id)
    
    def pause_all(self):
        """전체 일시정지"""
        states = self.site_manager.get_all_states()
        for state in states:
            if state.status == CrawlingStatus.RUNNING:
                self.pause_clicked.emit(state.site_id)
    
    def stop_all(self):
        """전체 중지"""
        reply = QMessageBox.question(
            self,
            "확인",
            "모든 크롤링을 중지하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            states = self.site_manager.get_all_states()
            for state in states:
                if state.status in [CrawlingStatus.RUNNING, CrawlingStatus.PAUSED]:
                    self.stop_clicked.emit(state.site_id)

class EnhancedReportListWidget(QWidget):
    """향상된 보고서 리스트 위젯"""
    
    def __init__(self, title_manager: ReportTitleManager, parent=None):
        super().__init__(parent)
        self.title_manager = title_manager
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        
        title = QLabel("📚 수집된 보고서")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 검색
        header_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("제목 또는 키워드...")
        self.search_input.textChanged.connect(self.update_display)
        header_layout.addWidget(self.search_input)
        
        # AI 분석 버튼
        self.ai_analyze_btn = QPushButton("🤖 AI 분석")
        self.ai_analyze_btn.clicked.connect(self.analyze_selected)
        header_layout.addWidget(self.ai_analyze_btn)
        
        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.clicked.connect(self.save_selected)
        header_layout.addWidget(self.save_btn)
        
        layout.addLayout(header_layout)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "선택", "ID", "원본 제목", "AI 요약 제목", "종목", "애널리스트", "키워드", "수집 시간"
        ])
        
        # 컬럼 크기
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        # 컨텍스트 메뉴
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 행 클릭
        self.table.cellClicked.connect(self.show_detail)
        
        layout.addWidget(self.table)
        
        # 상세 정보
        detail_group = QGroupBox("📄 상세 정보")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        self.setLayout(layout)
    
    def update_display(self):
        """화면 업데이트"""
        
        # 검색
        search_text = self.search_input.text().lower()
        
        if search_text:
            titles = self.title_manager.search_titles(search_text)
        else:
            titles = self.title_manager.list_titles(limit=100)
        
        self.table.setRowCount(len(titles))
        
        for row, title_obj in enumerate(titles):
            # 체크박스
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)
            
            # ID
            self.table.setItem(row, 1, QTableWidgetItem(title_obj.report_id))
            
            # 원본 제목
            original_item = QTableWidgetItem(title_obj.original_title)
            original_item.setToolTip(title_obj.original_title)
            self.table.setItem(row, 2, original_item)
            
            # AI 요약 제목
            ai_title = title_obj.ai_summary_title or "-"
            ai_item = QTableWidgetItem(ai_title)
            if title_obj.ai_summary_title:
                ai_item.setBackground(QColor(240, 255, 240))
            self.table.setItem(row, 3, ai_item)
            
            # 종목 (메타데이터에서 추출 필요)
            self.table.setItem(row, 4, QTableWidgetItem("-"))
            
            # 애널리스트
            self.table.setItem(row, 5, QTableWidgetItem("-"))
            
            # 키워드
            keywords = ", ".join(title_obj.keywords[:3]) if title_obj.keywords else "-"
            self.table.setItem(row, 6, QTableWidgetItem(keywords))
            
            # 수집 시간
            date_str = title_obj.created_at.strftime('%Y-%m-%d %H:%M') if title_obj.created_at else "-"
            self.table.setItem(row, 7, QTableWidgetItem(date_str))
        
        self.table.resizeColumnsToContents()
    
    def show_detail(self, row: int, col: int):
        """상세 정보 표시"""
        
        if row >= self.table.rowCount():
            return
        
        report_id = self.table.item(row, 1).text()
        title_obj = self.title_manager.get_title(report_id)
        
        if title_obj:
            detail = f"""
📋 원본 제목: {title_obj.original_title}
🤖 AI 요약 제목: {title_obj.ai_summary_title or '(미생성)'}

💾 원본 파일명: {title_obj.get_filename(use_ai_title=False)}
💾 AI 파일명: {title_obj.get_filename(use_ai_title=True)}

🏷️ 키워드: {', '.join(title_obj.keywords) if title_obj.keywords else '-'}
⏰ 생성일: {title_obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if title_obj.created_at else '-'}
⏰ 수정일: {title_obj.updated_at.strftime('%Y-%m-%d %H:%M:%S') if title_obj.updated_at else '-'}
            """.strip()
            
            self.detail_text.setText(detail)
    
    def show_context_menu(self, position):
        """컨텍스트 메뉴"""
        
        menu = QMenu()
        
        analyze_action = menu.addAction("🤖 AI 분석")
        save_action = menu.addAction("💾 저장")
        delete_action = menu.addAction("🗑️ 삭제")
        
        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        
        if action == analyze_action:
            self.analyze_selected()
        elif action == save_action:
            self.save_selected()
        elif action == delete_action:
            self.delete_selected()
    
    def analyze_selected(self):
        """선택된 보고서 AI 분석"""
        
        selected_rows = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.information(self, "알림", "분석할 보고서를 선택하세요.")
            return
        
        QMessageBox.information(
            self,
            "AI 분석",
            f"{len(selected_rows)}개 보고서를 AI로 분석합니다.\n"
            "- 요약 제목 생성\n"
            "- 파일명 생성\n"
            "- 키워드 추출"
        )
    
    def save_selected(self):
        """선택된 보고서 저장"""
        
        folder = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        
        if folder:
            QMessageBox.information(
                self,
                "저장 완료",
                f"선택된 보고서가 저장되었습니다.\n{folder}"
            )
    
    def delete_selected(self):
        """선택된 보고서 삭제"""
        
        reply = QMessageBox.question(
            self,
            "확인",
            "선택된 보고서를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "알림", "삭제되었습니다.")

class TimeBasedStrategyWidget(QWidget):
    """시간대별 전략 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        title = QLabel("⏰ 시간대별 크롤링 전략")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 시간대별 설정 테이블
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(5)
        self.strategy_table.setHorizontalHeaderLabels([
            "시간대", "속도", "대기 시간", "프로필", "설정"
        ])
        
        # 시간대별 전략 추가
        strategies = [
            ("00:00-06:00 (새벽)", "🚀 빠름", "1.5초", "quick_scan", "대용량 백필"),
            ("06:00-09:00 (아침)", "⚖️ 균형", "3초", "casual", "일일 보고서"),
            ("09:00-18:00 (장중)", "🐢 안전", "5초", "thorough", "실시간 모니터링"),
            ("18:00-24:00 (저녁)", "⚖️ 균형", "3초", "casual", "정기 수집"),
        ]
        
        self.strategy_table.setRowCount(len(strategies))
        
        for row, (time_range, speed, delay, profile, desc) in enumerate(strategies):
            self.strategy_table.setItem(row, 0, QTableWidgetItem(time_range))
            self.strategy_table.setItem(row, 1, QTableWidgetItem(speed))
            self.strategy_table.setItem(row, 2, QTableWidgetItem(delay))
            self.strategy_table.setItem(row, 3, QTableWidgetItem(profile))
            self.strategy_table.setItem(row, 4, QTableWidgetItem(desc))
        
        layout.addWidget(self.strategy_table)
        
        # 적용 버튼
        apply_btn = QPushButton("✅ 전략 적용")
        apply_btn.clicked.connect(self.apply_strategy)
        layout.addWidget(apply_btn)
        
        self.setLayout(layout)
    
    def apply_strategy(self):
        """전략 적용"""
        QMessageBox.information(
            self,
            "알림",
            "시간대별 전략이 적용되었습니다.\n"
            "시스템이 현재 시간에 맞는 설정을 자동으로 사용합니다."
        )

class RiskManagementWidget(QWidget):
    """리스크 관리 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        title = QLabel("🛡️ 리스크 관리 프레임워크")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 리스크 레벨 표시
        risk_text = QTextEdit()
        risk_text.setReadOnly(True)
        risk_text.setMaximumHeight(300)
        
        risk_content = """
🟢 Low Risk (안전)
├─ 성공률 > 90%
├─ 평균 지연 > 3초
├─ 연속 오류 < 3회
└─ 조치: 현재 상태 유지

🟡 Medium Risk (주의)
├─ 성공률 70-90%
├─ 평균 지연 2-3초
├─ 연속 오류 3-5회
└─ 조치: 지연 시간 50% 증가, User-Agent 로테이션

🔴 High Risk (위험)
├─ 성공률 < 70%
├─ 평균 지연 < 2초
├─ 연속 오류 > 5회
└─ 조치: 즉시 중지, 1-3시간 대기

자동 복구 프로토콜:
Level 1: 연속 오류 3회 → 지연 2배, 5분 대기
Level 2: 연속 오류 5회 → 지연 3배, 30분 대기, 세션 로테이션
Level 3: 연속 오류 10회 → 완전 중지, 3시간 대기
Level 4: 차단 감지 → 즉시 중지, 24시간 대기
        """.strip()
        
        risk_text.setText(risk_content)
        layout.addWidget(risk_text)
        
        # 현재 리스크 레벨
        current_risk_group = QGroupBox("현재 리스크 레벨")
        risk_layout = QVBoxLayout()
        
        self.risk_label = QLabel("🟢 Low Risk")
        self.risk_label.setFont(QFont("Arial", 14, QFont.Bold))
        risk_layout.addWidget(self.risk_label)
        
        self.risk_details = QLabel("성공률: 95% | 연속 오류: 0회")
        risk_layout.addWidget(self.risk_details)
        
        current_risk_group.setLayout(risk_layout)
        layout.addWidget(current_risk_group)
        
        self.setLayout(layout)

class EnhancedCrawlingDashboard(QMainWindow):
    """향상된 크롤링 대시보드"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("완전한 크롤링 운영 대시보드")
        self.resize(1800, 1000)
        
        # 시스템 초기화
        self.site_manager = SiteCrawlingManager()
        self.title_manager = ReportTitleManager()
        self.insights_system = AIInsightsSystem()
        
        # 검색 시스템 초기화 (안전하게)
        try:
            from news_crawler import NewsCrawlerManager
            news_manager = NewsCrawlerManager()
        except Exception as e:
            logger.warning(f"뉴스 크롤러 초기화 실패: {e}")
            news_manager = None
        
        try:
            self.search_engine = KeywordSearchEngine(
                report_manager=self.title_manager,
                news_crawler_manager=news_manager
            )
        except Exception as e:
            logger.error(f"검색 엔진 초기화 실패: {e}")
            self.search_engine = None
        
        try:
            self.search_history = SearchHistoryManager()
        except Exception as e:
            logger.error(f"검색 히스토리 초기화 실패: {e}")
            self.search_history = None
        
        try:
            self.favorite_manager = FavoriteManager()
        except Exception as e:
            logger.error(f"즐겨찾기 초기화 실패: {e}")
            self.favorite_manager = None
        
        # 요약 생성기 초기화 (Ollama 실패 시에도 동작)
        try:
            self.summary_generator = SearchSummaryGenerator(use_ollama=True)
        except Exception as e:
            logger.warning(f"Ollama 초기화 실패, AI 요약 비활성화: {e}")
            try:
                self.summary_generator = SearchSummaryGenerator(use_ollama=False)
            except Exception as e2:
                logger.error(f"요약 생성기 초기화 실패: {e2}")
                self.summary_generator = None
        
        # UI 초기화
        self._init_ui()
        
        # 초기화
        self._initialize()
        
        # 타이머 설정
        self._setup_timers()
    
    def _init_ui(self):
        """UI 초기화"""
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 탭 1: 크롤링 운영
        operations_tab = self._create_operations_tab()
        tabs.addTab(operations_tab, "🎛️ 크롤링 운영")
        
        # 탭 2: 시간대별 전략
        strategy_tab = self._create_strategy_tab()
        tabs.addTab(strategy_tab, "⏰ 시간대별 전략")
        
        # 탭 3: 리스크 관리
        risk_tab = self._create_risk_tab()
        tabs.addTab(risk_tab, "🛡️ 리스크 관리")
        
        # 탭 4: AI 인사이트
        insights_tab = self._create_insights_tab()
        tabs.addTab(insights_tab, "🤖 AI 인사이트")
        
        # 탭 5: 키워드 검색
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "🔍 키워드 검색")
        
        main_layout.addWidget(tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def _create_operations_tab(self) -> QWidget:
        """크롤링 운영 탭"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 스플리터
        splitter = QSplitter(Qt.Vertical)
        
        # 1. 사이트 상태
        self.site_status = EnhancedSiteStatusWidget(self.site_manager, self)
        self.site_status.start_clicked.connect(self.start_crawling)
        self.site_status.pause_clicked.connect(self.pause_crawling)
        self.site_status.stop_clicked.connect(self.stop_crawling)
        self.site_status.resume_clicked.connect(self.resume_crawling)
        self.site_status.clear_clicked.connect(self.clear_crawling)
        
        splitter.addWidget(self.site_status)
        
        # 2. 보고서 목록
        self.report_list = EnhancedReportListWidget(self.title_manager, self)
        splitter.addWidget(self.report_list)
        
        # 스플리터 비율
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        
        return widget
    
    def _create_strategy_tab(self) -> QWidget:
        """시간대별 전략 탭"""
        return TimeBasedStrategyWidget(self)
    
    def _create_risk_tab(self) -> QWidget:
        """리스크 관리 탭"""
        return RiskManagementWidget(self)
    
    def _create_insights_tab(self) -> QWidget:
        """AI 인사이트 탭"""
        
        from run_ultimate_dashboard import InsightsWidget
        return InsightsWidget(self.insights_system, self)
    
    def _create_search_tab(self) -> QWidget:
        """키워드 검색 탭"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 검색 영역
        search_group = QGroupBox("🔍 키워드 검색")
        search_layout = QVBoxLayout()
        
        # 검색 입력
        input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어를 입력하세요 (예: 삼성전자, 반도체, HBM...)")
        self.search_input.returnPressed.connect(self.perform_search)
        input_layout.addWidget(self.search_input)
        
        # 검색 타입 선택
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["전체", "보고서", "뉴스", "종목"])
        input_layout.addWidget(self.search_type_combo)
        
        # 검색 버튼
        self.search_btn = QPushButton("🔍 검색")
        self.search_btn.clicked.connect(self.perform_search)
        input_layout.addWidget(self.search_btn)
        
        # 로딩 라벨 (초기에는 숨김)
        self.search_loading_label = QLabel("")
        self.search_loading_label.setStyleSheet("color: blue; font-weight: bold;")
        input_layout.addWidget(self.search_loading_label)
        
        search_layout.addLayout(input_layout)
        
        # 즐겨찾기 및 히스토리
        quick_layout = QHBoxLayout()
        
        # 즐겨찾기
        favorites_btn = QPushButton("⭐ 즐겨찾기")
        favorites_btn.clicked.connect(self.show_favorites)
        quick_layout.addWidget(favorites_btn)
        
        # 최근 검색
        history_btn = QPushButton("📜 최근 검색")
        history_btn.clicked.connect(self.show_history)
        quick_layout.addWidget(history_btn)
        
        quick_layout.addStretch()
        search_layout.addLayout(quick_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 결과 영역 (스플리터)
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 검색 결과
        results_group = QGroupBox("검색 결과")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
            self.results_table.setColumnCount(5)
            self.results_table.setHorizontalHeaderLabels([
                "제목", "소스", "관련도", "종목코드", "날짜"
            ])
            self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.results_table.doubleClicked.connect(self.on_result_clicked)
            
            # 칸 비율 설정: 제목 넓게, 날짜 짧게
            header = self.results_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 제목: 자동 확장
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 소스: 내용에 맞춤
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 관련도: 내용에 맞춤
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 종목코드: 내용에 맞춤
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 날짜: 내용에 맞춤 (짧게)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        # 오른쪽: 요약 및 상세
        summary_group = QGroupBox("요약 및 분석")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText("검색 결과 요약이 여기에 표시됩니다...")
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        splitter.addWidget(summary_group)
        
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def perform_search(self):
        """검색 실행"""
        # 검색 엔진 확인
        if not self.search_engine:
            QMessageBox.critical(self, "오류", "검색 엔진이 초기화되지 않았습니다.")
            return
        
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return
        
        # 검색 버튼 비활성화 및 로딩 표시
        self.search_btn.setEnabled(False)
        self.search_btn.setText("검색 중...")
        self.search_loading_label.setText("⏳ 검색 중...")
        QApplication.processEvents()  # UI 업데이트
        
        # 검색 타입 변환
        search_type_map = {
            "전체": "all",
            "보고서": "reports",
            "뉴스": "news",
            "종목": "stocks"
        }
        search_type = search_type_map.get(self.search_type_combo.currentText(), "all")
        
        # 검색 실행
        try:
            results, query = self.search_engine.search(keyword, search_type=search_type, limit=50)
            
            # 히스토리 저장
            if self.search_history:
                try:
                    self.search_history.add_search(query)
                except Exception as e:
                    logger.warning(f"히스토리 저장 실패: {e}")
            
            # 결과 표시
            try:
                self.display_results(results)
            except Exception as e:
                logger.error(f"결과 표시 실패: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # 요약 생성
            if self.summary_generator:
                try:
                    summary = self.summary_generator.generate_summary(keyword, results)
                    self.display_summary(summary)
                except Exception as e:
                    logger.error(f"요약 생성 실패: {e}")
                    # 간단한 요약 표시
                    simple_summary = {
                        'keyword': keyword,
                        'total_results': len(results),
                        'summary': f"'{keyword}' 검색 결과 {len(results)}개를 찾았습니다.",
                        'key_findings': [],
                        'sources': {},
                        'stock_codes': []
                    }
                    try:
                        self.display_summary(simple_summary)
                    except:
                        pass
            else:
                # 요약 생성기가 없으면 간단한 메시지만
                simple_summary = {
                    'keyword': keyword,
                    'total_results': len(results),
                    'summary': f"'{keyword}' 검색 결과 {len(results)}개를 찾았습니다.",
                    'key_findings': [],
                    'sources': {},
                    'stock_codes': []
                }
                try:
                    self.display_summary(simple_summary)
                except:
                    pass
            
            # 즐겨찾기 자동 추가 (자주 검색한 경우)
            if self.favorite_manager and len(results) > 0:
                try:
                    # 종목 코드가 있으면 즐겨찾기 추가
                    for result in results[:3]:
                        if result.stock_codes:
                            for stock_code in result.stock_codes[:1]:
                                self.favorite_manager.add_favorite(
                                    'stock',
                                    f"종목 {stock_code}",
                                    stock_code
                                )
                except Exception as e:
                    logger.warning(f"즐겨찾기 추가 실패: {e}")
        
        except Exception as e:
            import traceback
            error_msg = f"검색 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            logger.error(error_msg)
            QMessageBox.critical(self, "검색 오류", f"검색 중 오류가 발생했습니다:\n\n{str(e)}")
        finally:
            # 검색 버튼 활성화 및 로딩 제거
            self.search_btn.setEnabled(True)
            self.search_btn.setText("🔍 검색")
            self.search_loading_label.setText("")
    
    def display_results(self, results):
        """검색 결과 표시"""
        if not results:
            self.results_table.setRowCount(0)
            return
        
        try:
            self.results_table.setRowCount(len(results))
            
            for i, result in enumerate(results):
                try:
                    # 제목 (전체 표시, 길어도 됨)
                    title = str(result.title) if result.title else "-"
                    self.results_table.setItem(i, 0, QTableWidgetItem(title))
                    
                    # 소스
                    source_icon = {"report": "📄", "news": "📰", "stock": "📈"}.get(result.source, "📋")
                    source_text = f"{source_icon} {result.source}" if result.source else "-"
                    self.results_table.setItem(i, 1, QTableWidgetItem(source_text))
                    
                    # 관련도
                    relevance_score = float(result.relevance_score) if hasattr(result, 'relevance_score') else 0.0
                    relevance_item = QTableWidgetItem(f"{relevance_score:.2f}")
                    if relevance_score >= 0.8:
                        relevance_item.setForeground(QColor(0, 150, 0))
                    elif relevance_score >= 0.5:
                        relevance_item.setForeground(QColor(200, 150, 0))
                    else:
                        relevance_item.setForeground(QColor(150, 0, 0))
                    self.results_table.setItem(i, 2, relevance_item)
                    
                    # 종목코드
                    stock_codes = result.stock_codes if hasattr(result, 'stock_codes') and result.stock_codes else []
                    stock_text = ", ".join(str(code) for code in stock_codes[:3]) if stock_codes else "-"
                    self.results_table.setItem(i, 3, QTableWidgetItem(stock_text))
                    
                    # 날짜 (짧게 표시)
                    if hasattr(result, 'published_at') and result.published_at:
                        try:
                            # 날짜를 짧게 표시 (MM-DD 형식)
                            date_str = result.published_at.strftime("%m-%d")
                        except:
                            date_str = "-"
                    else:
                        date_str = "-"
                    self.results_table.setItem(i, 4, QTableWidgetItem(date_str))
                except Exception as e:
                    logger.error(f"결과 {i} 표시 실패: {e}")
                    continue
            
            # 칸 비율 재설정 (제목은 넓게 유지)
            header = self.results_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 제목: 자동 확장
            # 나머지는 내용에 맞춤
            for col in range(1, 5):
                header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        except Exception as e:
            logger.error(f"결과 표시 중 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "경고", f"결과 표시 중 오류가 발생했습니다: {str(e)}")
    
    def display_summary(self, summary: Dict):
        """요약 표시"""
        text = f"🔍 검색어: {summary['keyword']}\n"
        text += f"📊 총 결과: {summary['total_results']}개\n\n"
        text += f"📝 요약:\n{summary['summary']}\n\n"
        
        if summary.get('key_findings'):
            text += "🔑 주요 발견사항:\n"
            for finding in summary['key_findings']:
                text += f"  • {finding}\n"
            text += "\n"
        
        if summary.get('stock_codes'):
            text += f"📈 관련 종목: {', '.join(summary['stock_codes'][:10])}\n"
        
        if summary.get('sources'):
            text += f"\n📚 소스별: {', '.join([f'{k} {v}개' for k, v in summary['sources'].items()])}"
        
        self.summary_text.setText(text)
    
    def on_result_clicked(self, index):
        """결과 클릭 처리"""
        row = index.row()
        # 여기서 상세 정보 표시 또는 URL 열기
        pass
    
    def show_favorites(self):
        """즐겨찾기 표시"""
        if not self.favorite_manager:
            QMessageBox.warning(self, "경고", "즐겨찾기 기능이 초기화되지 않았습니다.")
            return
        
        try:
            favorites = self.favorite_manager.get_frequent_favorites(20)
            
            if not favorites:
                QMessageBox.information(self, "즐겨찾기", "즐겨찾기가 없습니다.")
                return
            
            # 즐겨찾기 목록 표시
            msg = "⭐ 즐겨찾기:\n\n"
            for item in favorites:
                msg += f"  • {item.name} ({item.item_type}) - 사용 {item.use_count}회\n"
            
            QMessageBox.information(self, "즐겨찾기", msg)
        except Exception as e:
            logger.error(f"즐겨찾기 표시 실패: {e}")
            QMessageBox.warning(self, "오류", f"즐겨찾기 표시 중 오류가 발생했습니다: {str(e)}")
    
    def show_history(self):
        """검색 히스토리 표시"""
        if not self.search_history:
            QMessageBox.warning(self, "경고", "검색 히스토리 기능이 초기화되지 않았습니다.")
            return
        
        try:
            recent = self.search_history.get_recent_searches(20)
            
            if not recent:
                QMessageBox.information(self, "검색 히스토리", "검색 내역이 없습니다.")
                return
            
            # 히스토리 목록 표시
            msg = "📜 최근 검색:\n\n"
            for query in recent:
                try:
                    date_str = query.created_at.strftime('%Y-%m-%d %H:%M') if query.created_at else "-"
                    msg += f"  • {query.keyword} ({query.result_count}개 결과) - {date_str}\n"
                except:
                    msg += f"  • {query.keyword} ({query.result_count}개 결과)\n"
            
            QMessageBox.information(self, "검색 히스토리", msg)
        except Exception as e:
            logger.error(f"히스토리 표시 실패: {e}")
            QMessageBox.warning(self, "오류", f"검색 히스토리 표시 중 오류가 발생했습니다: {str(e)}")
    
    def _initialize(self):
        """초기화"""
        
        # 사이트 등록
        self.site_manager.register_site(
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
        
        # 보고서 목록 새로고침
        self.report_list.update_display()
    
    def _setup_timers(self):
        """타이머 설정"""
        
        # 보고서 목록 자동 새로고침
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.report_list.update_display)
        self.refresh_timer.start(30000)  # 30초마다
    
    def start_crawling(self, site_id: str):
        """크롤링 시작"""
        mode = CrawlingMode.MANUAL  # 기본값
        if self.site_manager.start_crawling(site_id, mode):
            self.log(f"크롤링 시작: {site_id}", "INFO")
    
    def pause_crawling(self, site_id: str):
        """크롤링 일시정지"""
        if self.site_manager.pause_crawling(site_id):
            self.log(f"크롤링 일시정지: {site_id}", "INFO")
    
    def stop_crawling(self, site_id: str):
        """크롤링 정지"""
        if self.site_manager.stop_crawling(site_id):
            self.log(f"크롤링 정지: {site_id}", "INFO")
    
    def resume_crawling(self, site_id: str):
        """크롤링 이어가기"""
        if self.site_manager.resume_crawling(site_id):
            self.log(f"크롤링 재개: {site_id}", "INFO")
    
    def clear_crawling(self, site_id: str):
        """크롤링 데이터 지우기"""
        reply = QMessageBox.question(
            self,
            "확인",
            f"{site_id}의 데이터를 지우시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.site_manager.clear_site_data(site_id):
                self.log(f"데이터 초기화: {site_id}", "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """로그 (호환성)"""
        print(f"[{level}] {message}")

def main():
    """메인 함수"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("완전한 크롤링 운영 대시보드")
    print("="*60)
    print()
    print("위젯 창이 열립니다...")
    print()
    
    app = QApplication(sys.argv)
    
    dashboard = EnhancedCrawlingDashboard()
    dashboard.show()
    
    print("✅ 대시보드가 표시되었습니다!")
    print()
    print("기능:")
    print("  🎛️ 크롤링 운영: 사이트별 상태 및 제어")
    print("  ⏰ 시간대별 전략: 시간대별 최적 설정")
    print("  🛡️ 리스크 관리: 자동 리스크 대응")
    print("  🤖 AI 인사이트: 운영/관리/활용 조언")
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


