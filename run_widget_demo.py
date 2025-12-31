# run_widget_demo.py
"""
위젯 데모 실행

모니터링 위젯을 실행하고 시뮬레이션 데이터를 표시
"""

import sys
import io
import random
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from crawler_monitoring_widget import CrawlerDashboardWidget
from crawler_manager import CrawlerManager

def main():
    """메인 함수"""
    
    print("="*60)
    print("🎭 크롤러 모니터링 위젯 데모")
    print("="*60)
    print()
    print("위젯 창이 열립니다...")
    print("창을 닫으면 프로그램이 종료됩니다.")
    print()
    
    # 애플리케이션 생성
    app = QApplication(sys.argv)
    
    # 매니저 생성
    manager = CrawlerManager()
    
    # 위젯 생성
    widget = CrawlerDashboardWidget()
    widget.setWindowTitle("크롤러 모니터링 대시보드 - 데모")
    widget.resize(1200, 800)
    
    # 연결
    widget.set_system(manager)
    widget.register_site('38com', manager.health_monitor)
    
    # 크롤러를 아바타로 등록
    crawler_avatar = manager.get_crawler_as_avatar()
    widget.register_avatar('38com_crawler', crawler_avatar)
    
    # 초기 데이터 생성
    print("초기 데이터 생성 중...")
    for i in range(15):
        success = random.random() < 0.85
        response_time = random.uniform(0.5, 3.0)
        status_code = 200 if success else random.choice([403, 429, 500])
        
        manager.record_request(
            success=success,
            response_time=response_time,
            status_code=status_code
        )
    
    # 통계 업데이트
    manager.stats['total_collected'] = 25
    manager.stats['active_sources'] = 1
    
    # 초기 로그
    widget.log("시스템 초기화 완료", "SUCCESS")
    widget.log("38com 사이트 등록 완료", "INFO")
    widget.log("크롤러 초기화 완료", "SUCCESS")
    widget.log("모니터링 시작", "INFO")
    
    # 시뮬레이션 함수
    request_count = 0
    
    def simulate_activity():
        nonlocal request_count
        request_count += 1
        
        # 요청 시뮬레이션
        success = random.random() < 0.8
        response_time = random.uniform(0.5, 3.0)
        status_code = 200 if success else random.choice([403, 429, 500])
        
        manager.record_request(
            success=success,
            response_time=response_time,
            status_code=status_code
        )
        
        # 통계 업데이트
        if success:
            manager.stats['total_collected'] += 1
            widget.log(f"보고서 수집 완료: {manager.stats['total_collected']}개", "SUCCESS")
        else:
            widget.log(f"요청 실패: HTTP {status_code}", "WARNING")
        
        # 크롤러 상태 업데이트
        if request_count % 5 == 0:
            manager.update_crawler_status('working', completed=manager.stats['total_collected'])
        else:
            manager.update_crawler_status('idle', completed=manager.stats['total_collected'])
    
    # 타이머 설정 (5초마다 시뮬레이션)
    timer = QTimer()
    timer.timeout.connect(simulate_activity)
    timer.start(5000)  # 5초마다
    
    # 위젯 표시
    widget.show()
    
    print("✅ 위젯이 표시되었습니다!")
    print()
    print("기능:")
    print("  - 사이트 건강도: 실시간 상태 모니터링")
    print("  - 크롤러 상태: 작업 진행 상황")
    print("  - 전체 통계: 수집/검증 통계")
    print("  - 활동 로그: 실시간 로그 표시")
    print()
    print("5초마다 새로운 요청이 시뮬레이션됩니다.")
    print()
    
    # 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()




