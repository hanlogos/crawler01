# run_complete_dashboard.py
"""
완전한 통합 대시보드

페이크 페이스, 데이터 구조, 시나리오를 모두 통합한 대시보드
"""

import sys
import io
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QComboBox,
                             QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
                             QTableWidget, QTableWidgetItem, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
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
from integrated_crawler_manager import IntegratedCrawlerManager
import logging

class CompleteDashboard(QMainWindow):
    """완전한 통합 대시보드"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("완전한 크롤러 통합 대시보드")
        self.resize(1600, 1000)
        
        # 통합 매니저
        self.integrated_manager = IntegratedCrawlerManager(
            use_fake_face=True,
            fake_face_profile='casual',
            use_adaptive_parsing=True
        )
        
        # 기존 매니저 (호환성)
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
        main_layout = QVBoxLayout()
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 탭 1: 모니터링
        monitoring_tab = self._create_monitoring_tab()
        tabs.addTab(monitoring_tab, "📊 모니터링")
        
        # 탭 2: 시나리오
        scenario_tab = self._create_scenario_tab()
        tabs.addTab(scenario_tab, "🎯 시나리오")
        
        # 탭 3: 데이터 구조
        data_tab = self._create_data_structure_tab()
        tabs.addTab(data_tab, "📋 데이터 구조")
        
        # 탭 4: 페이크 페이스
        fake_face_tab = self._create_fake_face_tab()
        tabs.addTab(fake_face_tab, "🎭 페이크 페이스")
        
        main_layout.addWidget(tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def _create_monitoring_tab(self) -> QWidget:
        """모니터링 탭 생성"""
        return self.dashboard
    
    def _create_scenario_tab(self) -> QWidget:
        """시나리오 탭 생성"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("크롤링 시나리오 관리")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # 시나리오 목록
        list_label = QLabel("사용 가능한 시나리오:")
        layout.addWidget(list_label)
        
        self.scenario_list = QListWidget()
        scenarios = self.integrated_manager.list_available_scenarios()
        for scenario in scenarios:
            item_text = f"[{scenario['type']}] {scenario['name']}\n{scenario['description']}"
            self.scenario_list.addItem(item_text)
        layout.addWidget(self.scenario_list)
        
        # 실행 버튼
        run_btn = QPushButton("선택한 시나리오 실행")
        run_btn.clicked.connect(self._run_selected_scenario)
        layout.addWidget(run_btn)
        
        # 커스텀 시나리오
        custom_label = QLabel("커스텀 시나리오 생성:")
        layout.addWidget(custom_label)
        
        custom_layout = QHBoxLayout()
        self.custom_name = QLineEdit()
        self.custom_name.setPlaceholderText("시나리오 이름")
        custom_layout.addWidget(self.custom_name)
        
        self.custom_keywords = QLineEdit()
        self.custom_keywords.setPlaceholderText("키워드 (쉼표로 구분)")
        custom_layout.addWidget(self.custom_keywords)
        
        create_btn = QPushButton("생성 및 실행")
        create_btn.clicked.connect(self._create_custom_scenario)
        custom_layout.addWidget(create_btn)
        
        layout.addLayout(custom_layout)
        
        # 결과
        result_label = QLabel("실행 결과:")
        layout.addWidget(result_label)
        
        self.scenario_result = QTextEdit()
        self.scenario_result.setReadOnly(True)
        layout.addWidget(self.scenario_result)
        
        widget.setLayout(layout)
        return widget
    
    def _create_data_structure_tab(self) -> QWidget:
        """데이터 구조 탭 생성"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("데이터 구조 관리")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # 템플릿 선택
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("템플릿:"))
        
        self.template_combo = QComboBox()
        templates = self.integrated_manager.list_available_templates()
        for template in templates:
            self.template_combo.addItem(template['name'], template['name'])
        template_layout.addWidget(self.template_combo)
        
        view_btn = QPushButton("템플릿 보기")
        view_btn.clicked.connect(self._view_template)
        template_layout.addWidget(view_btn)
        
        layout.addLayout(template_layout)
        
        # 템플릿 정보
        self.template_info = QTextEdit()
        self.template_info.setReadOnly(True)
        layout.addWidget(self.template_info)
        
        # 필드 제안
        suggest_label = QLabel("필드 제안 (JSON 데이터 입력):")
        layout.addWidget(suggest_label)
        
        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText('{"report_id": "RPT_001", "title": "..."}')
        layout.addWidget(self.data_input)
        
        suggest_btn = QPushButton("필드 제안 받기")
        suggest_btn.clicked.connect(self._suggest_fields)
        layout.addWidget(suggest_btn)
        
        # 제안 결과
        self.suggestion_result = QTextEdit()
        self.suggestion_result.setReadOnly(True)
        layout.addWidget(self.suggestion_result)
        
        widget.setLayout(layout)
        return widget
    
    def _create_fake_face_tab(self) -> QWidget:
        """페이크 페이스 탭 생성"""
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("페이크 페이스 설정")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # 프로필 선택
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("프로필:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(['casual', 'researcher', 'quick_scan', 'thorough'])
        self.profile_combo.setCurrentText('casual')
        profile_layout.addWidget(self.profile_combo)
        
        apply_btn = QPushButton("프로필 적용")
        apply_btn.clicked.connect(self._apply_fake_face_profile)
        profile_layout.addWidget(apply_btn)
        
        layout.addLayout(profile_layout)
        
        # 통계
        stats_label = QLabel("세션 통계:")
        layout.addWidget(stats_label)
        
        self.fake_face_stats = QTextEdit()
        self.fake_face_stats.setReadOnly(True)
        layout.addWidget(self.fake_face_stats)
        
        # 업데이트 버튼
        update_btn = QPushButton("통계 업데이트")
        update_btn.clicked.connect(self._update_fake_face_stats)
        layout.addWidget(update_btn)
        
        widget.setLayout(layout)
        return widget
    
    def _initialize(self):
        """초기화"""
        
        # 사이트 등록
        if self.manager.health_monitor:
            self.dashboard.register_site('38com', self.manager.health_monitor)
        
        # 초기 로그
        self.dashboard.log("시스템 초기화 완료", "SUCCESS")
        self.dashboard.log("통합 크롤러 매니저 활성화", "INFO")
        self.dashboard.log("페이크 페이스 시스템 활성화", "INFO")
        
        # 초기 통계
        self._update_fake_face_stats()
    
    def _setup_timers(self):
        """타이머 설정"""
        
        # 활동 시뮬레이션
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self._simulate_activity)
        self.activity_timer.start(5000)
        
        # 통계 업데이트
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_fake_face_stats)
        self.stats_timer.start(10000)  # 10초마다
    
    def _run_selected_scenario(self):
        """선택한 시나리오 실행"""
        
        current_item = self.scenario_list.currentItem()
        if not current_item:
            self.scenario_result.setText("시나리오를 선택하세요.")
            return
        
        # 시나리오 이름 추출
        text = current_item.text()
        scenario_name = text.split(']')[1].split('\n')[0].strip()
        
        self.dashboard.log(f"시나리오 실행 시작: {scenario_name}", "INFO")
        self.scenario_result.setText("실행 중...")
        
        try:
            result = self.integrated_manager.run_scenario(scenario_name)
            
            if result.get('success'):
                count = result.get('reports_count', 0)
                self.scenario_result.setText(
                    f"✅ 실행 완료!\n\n"
                    f"수집된 보고서: {count}개\n"
                    f"시나리오: {result.get('scenario')}"
                )
                self.dashboard.log(f"시나리오 실행 완료: {count}개 수집", "SUCCESS")
            else:
                error = result.get('error', '알 수 없는 오류')
                self.scenario_result.setText(f"❌ 실행 실패:\n{error}")
                self.dashboard.log(f"시나리오 실행 실패: {error}", "ERROR")
        
        except Exception as e:
            self.scenario_result.setText(f"❌ 오류 발생:\n{str(e)}")
            self.dashboard.log(f"시나리오 실행 오류: {e}", "ERROR")
    
    def _create_custom_scenario(self):
        """커스텀 시나리오 생성 및 실행"""
        
        name = self.custom_name.text()
        keywords_str = self.custom_keywords.text()
        
        if not name:
            self.scenario_result.setText("시나리오 이름을 입력하세요.")
            return
        
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []
        
        requirements = {
            'description': f'커스텀 시나리오: {name}',
            'days': 7,
            'max_reports': 50,
            'keywords': keywords,
            'use_analysis': True,
            'fake_face_profile': 'casual'
        }
        
        self.dashboard.log(f"커스텀 시나리오 생성: {name}", "INFO")
        
        try:
            result = self.integrated_manager.create_and_run(name, requirements)
            
            if result.get('success'):
                count = result.get('reports_count', 0)
                self.scenario_result.setText(
                    f"✅ 생성 및 실행 완료!\n\n"
                    f"시나리오: {name}\n"
                    f"수집된 보고서: {count}개"
                )
                self.dashboard.log(f"커스텀 시나리오 완료: {count}개 수집", "SUCCESS")
            else:
                error = result.get('error', '알 수 없는 오류')
                self.scenario_result.setText(f"❌ 실패:\n{error}")
        
        except Exception as e:
            self.scenario_result.setText(f"❌ 오류:\n{str(e)}")
    
    def _view_template(self):
        """템플릿 보기"""
        
        template_name = self.template_combo.currentData()
        if not template_name:
            return
        
        template_dict = self.integrated_manager.get_data_structure(template_name)
        if template_dict:
            info = f"템플릿: {template_dict['name']}\n"
            info += f"설명: {template_dict['description']}\n"
            info += f"버전: {template_dict['version']}\n\n"
            info += "필드 목록:\n"
            
            for field in template_dict['fields']:
                req = "필수" if field['required'] else "선택"
                info += f"  - {field['name']} ({field['type']}, {req})\n"
                if field['description']:
                    info += f"    {field['description']}\n"
            
            self.template_info.setText(info)
    
    def _suggest_fields(self):
        """필드 제안"""
        
        import json
        
        data_text = self.data_input.toPlainText()
        if not data_text:
            self.suggestion_result.setText("데이터를 입력하세요.")
            return
        
        try:
            data = json.loads(data_text)
            template_name = self.template_combo.currentData()
            
            suggestions = self.integrated_manager.suggest_fields(data, template_name)
            
            if suggestions:
                result = f"제안된 필드: {len(suggestions)}개\n\n"
                for sug in suggestions[:10]:
                    req = "필수" if sug['required'] else "선택"
                    result += f"- {sug['field']} ({sug['type']}, {req})\n"
                    result += f"  설명: {sug['description']}\n"
                    result += f"  이유: {sug['reason']}\n\n"
                
                self.suggestion_result.setText(result)
            else:
                self.suggestion_result.setText("제안할 필드가 없습니다.")
        
        except json.JSONDecodeError:
            self.suggestion_result.setText("올바른 JSON 형식이 아닙니다.")
        except Exception as e:
            self.suggestion_result.setText(f"오류: {str(e)}")
    
    def _apply_fake_face_profile(self):
        """페이크 페이스 프로필 적용"""
        
        profile_name = self.profile_combo.currentText()
        
        if self.integrated_manager.fake_face:
            self.integrated_manager.fake_face.profile = \
                self.integrated_manager.fake_face.PROFILES.get(
                    profile_name,
                    self.integrated_manager.fake_face.PROFILES['casual']
                )
            
            self.dashboard.log(f"페이크 페이스 프로필 변경: {profile_name}", "INFO")
            self._update_fake_face_stats()
    
    def _update_fake_face_stats(self):
        """페이크 페이스 통계 업데이트"""
        
        if self.integrated_manager.fake_face:
            stats = self.integrated_manager.fake_face.get_session_stats()
            
            info = f"프로필: {stats['profile']}\n"
            info += f"요청 수: {stats['request_count']}개\n"
            info += f"세션 시간: {stats['session_elapsed']:.0f}초\n"
            info += f"세션 지속 시간: {stats['session_duration']:.0f}초\n"
            
            if stats['is_break']:
                info += f"\n현재 휴식 중 (종료 예정: {stats['break_until']})"
            
            self.fake_face_stats.setText(info)
    
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
            self.dashboard.log(f"보고서 수집 완료: {self.manager.stats['total_collected']}개", "SUCCESS")

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
    
    dashboard = CompleteDashboard()
    dashboard.show()
    
    print("✅ 대시보드가 표시되었습니다!")
    print()
    print("기능:")
    print("  📊 모니터링: 실시간 크롤러 상태")
    print("  🎯 시나리오: 다양한 수집 전략 실행")
    print("  📋 데이터 구조: 템플릿 및 필드 제안")
    print("  🎭 페이크 페이스: 차단 방지 설정")
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



