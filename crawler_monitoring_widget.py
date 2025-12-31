# crawler_monitoring_widget.py
"""
적응형 크롤러 모니터링 위젯

실시간으로 크롤러 상태를 시각화
메인 프로젝트에 바로 통합 가능
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QTableWidget, QTableWidgetItem,
    QGroupBox, QPushButton, QScrollArea, QTextEdit,
    QSplitter, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QPalette
from datetime import datetime
from typing import Dict, List, Optional
import logging

# 현재 프로젝트의 EnhancedHealthMonitor 사용
try:
    from enhanced_health_monitor import EnhancedHealthMonitor, HealthMetrics
except ImportError:
    # 호환성을 위한 fallback
    EnhancedHealthMonitor = None
    HealthMetrics = None

# ============================================================
# Component 1: Site Health Display
# ============================================================

class SiteHealthWidget(QWidget):
    """
    사이트 건강도 위젯
    
    각 사이트의 상태를 실시간 표시
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.site_monitors = {}  # site_id → health_monitor
        self.init_ui()
        
        # 1초마다 업데이트
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🌐 사이트 건강도")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "사이트", "상태", "성공률", "평균 응답", "1시간 오류", "연속 오류"
        ])
        
        # 컬럼 크기 조정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.table.setMaximumHeight(200)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def register_site(self, site_id: str, health_monitor):
        """사이트 등록"""
        self.site_monitors[site_id] = health_monitor
        
        # 테이블에 행 추가
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 사이트 이름
        self.table.setItem(row, 0, QTableWidgetItem(site_id))
    
    def update_display(self):
        """디스플레이 업데이트"""
        
        for row, (site_id, monitor) in enumerate(self.site_monitors.items()):
            # 건강도 가져오기
            health = monitor.get_health()
            
            # 상태
            status_icon = self._get_status_icon(health.status)
            status_item = QTableWidgetItem(status_icon)
            status_item.setTextAlignment(Qt.AlignCenter)
            self._set_status_color(status_item, health.status)
            self.table.setItem(row, 1, status_item)
            
            # 성공률
            success_item = QTableWidgetItem(f"{health.success_rate:.1%}")
            success_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, success_item)
            
            # 평균 응답 시간
            response_item = QTableWidgetItem(f"{health.avg_response_time:.2f}초")
            response_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, response_item)
            
            # 1시간 오류
            error_item = QTableWidgetItem(str(health.error_count_1h))
            error_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, error_item)
            
            # 연속 오류
            consecutive_item = QTableWidgetItem(str(health.consecutive_errors))
            consecutive_item.setTextAlignment(Qt.AlignCenter)
            if health.consecutive_errors >= 3:
                consecutive_item.setForeground(QColor(255, 0, 0))
            self.table.setItem(row, 5, consecutive_item)
    
    def _get_status_icon(self, status: str) -> str:
        """상태 아이콘"""
        icons = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '🔴',
            'blocked': '🚫',
            'unknown': '❓'
        }
        return icons.get(status, '❓')
    
    def _set_status_color(self, item: QTableWidgetItem, status: str):
        """상태 색상"""
        colors = {
            'healthy': QColor(0, 200, 0),
            'degraded': QColor(255, 165, 0),
            'critical': QColor(255, 0, 0),
            'blocked': QColor(128, 0, 128)
        }
        
        if status in colors:
            item.setBackground(colors[status])
            item.setForeground(QColor(255, 255, 255))

# ============================================================
# Component 2: Avatar Status Display (단순화 버전)
# ============================================================

class AvatarStatusWidget(QWidget):
    """
    아바타 상태 위젯 (단순화 버전)
    
    현재는 단일 크롤러만 지원
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.avatars = {}  # avatar_id → avatar
        self.init_ui()
        
        # 1초마다 업데이트
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🤖 크롤러 상태")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "크롤러", "상태", "총 작업", "완료", "실패", "대기"
        ])
        
        # 컬럼 크기 조정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.table.setMaximumHeight(200)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def register_avatar(self, avatar_id: str, avatar):
        """아바타 등록"""
        self.avatars[avatar_id] = avatar
        
        # 테이블에 행 추가
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 아바타 이름
        self.table.setItem(row, 0, QTableWidgetItem(avatar_id))
    
    def update_display(self):
        """디스플레이 업데이트"""
        
        for row, (avatar_id, avatar) in enumerate(self.avatars.items()):
            # 통계 가져오기
            if hasattr(avatar, 'get_stats'):
                stats = avatar.get_stats()
            else:
                # 기본 통계
                stats = {
                    'status': 'idle',
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'queue_size': 0
                }
            
            # 상태
            status_icon = self._get_status_icon(stats['status'])
            status_item = QTableWidgetItem(status_icon)
            status_item.setTextAlignment(Qt.AlignCenter)
            self._set_status_color(status_item, stats['status'])
            self.table.setItem(row, 1, status_item)
            
            # 총 작업
            total_item = QTableWidgetItem(str(stats['total']))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, total_item)
            
            # 완료
            completed_item = QTableWidgetItem(str(stats['completed']))
            completed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, completed_item)
            
            # 실패
            failed_item = QTableWidgetItem(str(stats['failed']))
            failed_item.setTextAlignment(Qt.AlignCenter)
            if stats['failed'] > 0:
                failed_item.setForeground(QColor(255, 0, 0))
            self.table.setItem(row, 4, failed_item)
            
            # 대기
            queue_item = QTableWidgetItem(str(stats['queue_size']))
            queue_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, queue_item)
    
    def _get_status_icon(self, status: str) -> str:
        """상태 아이콘"""
        icons = {
            'idle': '💤',
            'working': '⚙️',
            'paused': '⏸️',
            'error': '❌',
            'blocked': '🚫'
        }
        return icons.get(status, '❓')
    
    def _set_status_color(self, item: QTableWidgetItem, status: str):
        """상태 색상"""
        colors = {
            'idle': QColor(200, 200, 200),
            'working': QColor(0, 200, 0),
            'paused': QColor(255, 165, 0),
            'error': QColor(255, 0, 0),
            'blocked': QColor(128, 0, 128)
        }
        
        if status in colors:
            item.setBackground(colors[status])
            item.setForeground(QColor(255, 255, 255))

# ============================================================
# Component 3: Statistics Display
# ============================================================

class StatisticsWidget(QWidget):
    """
    통계 위젯
    
    전체 시스템 통계 표시
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system = None
        self.init_ui()
        
        # 1초마다 업데이트
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("📊 전체 통계")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 통계 그리드
        grid_layout = QVBoxLayout()
        
        # 수집 통계
        self.total_collected_label = self._create_stat_label("총 수집", "0")
        grid_layout.addWidget(self.total_collected_label)
        
        self.total_validated_label = self._create_stat_label("총 검증", "0")
        grid_layout.addWidget(self.total_validated_label)
        
        self.consensus_label = self._create_stat_label("컨센서스", "0")
        grid_layout.addWidget(self.consensus_label)
        
        self.active_sources_label = self._create_stat_label("활성 소스", "0")
        grid_layout.addWidget(self.active_sources_label)
        
        layout.addLayout(grid_layout)
        
        self.setLayout(layout)
        self.setMaximumHeight(200)
    
    def _create_stat_label(self, title: str, value: str) -> QLabel:
        """통계 라벨 생성"""
        label = QLabel(f"{title}: {value}")
        label.setFont(QFont("Arial", 10))
        return label
    
    def set_system(self, system):
        """시스템 설정"""
        self.system = system
    
    def update_display(self):
        """디스플레이 업데이트"""
        
        if not self.system:
            return
        
        # 시스템에서 통계 가져오기
        if hasattr(self.system, 'get_global_stats'):
            stats = self.system.get_global_stats()
        else:
            stats = {
                'total_collected': 0,
                'total_validated': 0,
                'consensus_count': 0,
                'active_sources': 0
            }
        
        self.total_collected_label.setText(
            f"총 수집: {stats.get('total_collected', 0)}"
        )
        
        self.total_validated_label.setText(
            f"총 검증: {stats.get('total_validated', 0)}"
        )
        
        self.consensus_label.setText(
            f"컨센서스: {stats.get('consensus_count', 0)}"
        )
        
        self.active_sources_label.setText(
            f"활성 소스: {stats.get('active_sources', 0)}"
        )

# ============================================================
# Component 4: Activity Log
# ============================================================

class ActivityLogWidget(QWidget):
    """
    활동 로그 위젯
    
    실시간 활동 로그 표시
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_logs = 100
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title_layout = QHBoxLayout()
        
        title = QLabel("📝 활동 로그")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title_layout.addWidget(title)
        
        # 클리어 버튼
        clear_btn = QPushButton("지우기")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setMaximumWidth(80)
        title_layout.addWidget(clear_btn)
        
        layout.addLayout(title_layout)
        
        # 로그 표시
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        # 폰트 설정
        font = QFont("Courier New", 9)
        self.log_text.setFont(font)
        
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
    
    def add_log(self, message: str, level: str = "INFO"):
        """로그 추가"""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 색상 지정
        colors = {
            'INFO': 'black',
            'SUCCESS': 'green',
            'WARNING': 'orange',
            'ERROR': 'red'
        }
        
        color = colors.get(level, 'black')
        
        # HTML 형식
        html = f'<span style="color: gray">[{timestamp}]</span> '
        html += f'<span style="color: {color}">[{level}]</span> '
        html += f'{message}'
        
        self.log_text.append(html)
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """로그 지우기"""
        self.log_text.clear()

# ============================================================
# Component 5: Main Dashboard Widget
# ============================================================

class CrawlerDashboardWidget(QWidget):
    """
    메인 대시보드 위젯
    
    모든 모니터링 컴포넌트를 통합
    """
    
    # 시그널
    log_signal = pyqtSignal(str, str)  # message, level
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # 로그 시그널 연결
        self.log_signal.connect(self.activity_log.add_log)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🎭 적응형 크롤러 모니터링 대시보드")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 시간
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # 타이머 (시간 업데이트)
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        # 스플리터 (상하 분할)
        splitter = QSplitter(Qt.Vertical)
        
        # 상단: 사이트 건강도 + 아바타 상태
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        
        self.site_health = SiteHealthWidget()
        top_layout.addWidget(self.site_health)
        
        self.avatar_status = AvatarStatusWidget()
        top_layout.addWidget(self.avatar_status)
        
        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)
        
        # 중단: 통계
        self.statistics = StatisticsWidget()
        splitter.addWidget(self.statistics)
        
        # 하단: 활동 로그
        self.activity_log = ActivityLogWidget()
        splitter.addWidget(self.activity_log)
        
        # 비율 설정
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def update_time(self):
        """시간 업데이트"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
    
    def register_site(self, site_id: str, health_monitor):
        """사이트 등록"""
        self.site_health.register_site(site_id, health_monitor)
        self.log(f"사이트 등록: {site_id}", "INFO")
    
    def register_avatar(self, avatar_id: str, avatar):
        """아바타 등록"""
        self.avatar_status.register_avatar(avatar_id, avatar)
        self.log(f"크롤러 등록: {avatar_id}", "INFO")
    
    def set_system(self, system):
        """시스템 설정"""
        self.statistics.set_system(system)
    
    def log(self, message: str, level: str = "INFO"):
        """로그 추가 (thread-safe)"""
        self.log_signal.emit(message, level)

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 대시보드 생성
    dashboard = CrawlerDashboardWidget()
    dashboard.setWindowTitle("크롤러 모니터링 대시보드")
    dashboard.resize(1200, 800)
    dashboard.show()
    
    # 테스트 로그
    dashboard.log("시스템 시작", "SUCCESS")
    dashboard.log("38com 연결 중...", "INFO")
    dashboard.log("크롤러 초기화 완료", "SUCCESS")
    
    sys.exit(app.exec_())



