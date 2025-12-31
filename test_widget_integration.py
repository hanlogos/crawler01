# test_widget_integration.py
"""
모니터링 위젯 통합 테스트

크롤러와 위젯이 제대로 연결되는지 확인
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import random

from crawler_monitoring_widget import CrawlerDashboardWidget
from crawler_manager import CrawlerManager
from enhanced_health_monitor import EnhancedHealthMonitor

def test_basic_widget():
    """Test 1: 기본 위젯 표시"""
    
    print("="*60)
    print("Test 1: 기본 위젯 표시")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    widget = CrawlerDashboardWidget()
    widget.setWindowTitle("Test 1: 기본 위젯")
    widget.resize(1200, 800)
    widget.show()
    
    # 테스트 로그
    widget.log("테스트 시작", "INFO")
    widget.log("기본 위젯 로딩 완료", "SUCCESS")
    
    print("✅ 위젯이 표시되었습니다.")
    print("   창이 보이는지 확인하세요.")
    
    sys.exit(app.exec_())

def test_with_manager():
    """Test 2: 크롤러 매니저와 통합"""
    
    print("\n" + "="*60)
    print("Test 2: 크롤러 매니저 통합")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    # 매니저 생성
    manager = CrawlerManager()
    
    # 위젯 생성
    widget = CrawlerDashboardWidget()
    widget.setWindowTitle("Test 2: 크롤러 매니저 통합")
    widget.resize(1200, 800)
    
    # 연결
    widget.set_system(manager)
    widget.register_site('38com', manager.health_monitor)
    
    # 크롤러를 아바타로 등록
    crawler_avatar = manager.get_crawler_as_avatar()
    widget.register_avatar('38com_crawler', crawler_avatar)
    
    # 초기 로그
    widget.log("시스템 초기화 완료", "SUCCESS")
    widget.log("크롤러 매니저 연결 완료", "INFO")
    
    # 시뮬레이션: 요청 기록
    def simulate_requests():
        success = random.random() < 0.85
        response_time = random.uniform(0.5, 3.0)
        status_code = 200 if success else random.choice([403, 429, 500])
        
        manager.record_request(
            success=success,
            response_time=response_time,
            status_code=status_code
        )
        
        if success:
            widget.log(f"요청 성공: {response_time:.2f}초", "SUCCESS")
        else:
            widget.log(f"요청 실패: {status_code}", "WARNING")
    
    # 타이머로 시뮬레이션
    timer = QTimer()
    timer.timeout.connect(simulate_requests)
    timer.start(3000)  # 3초마다
    
    widget.show()
    
    print("✅ 크롤러 매니저가 연결되었습니다.")
    print("   3초마다 요청이 시뮬레이션됩니다.")
    print("   사이트 건강도가 실시간으로 업데이트됩니다.")
    
    sys.exit(app.exec_())

def test_full_integration():
    """Test 3: 전체 통합 테스트"""
    
    print("\n" + "="*60)
    print("Test 3: 전체 통합 테스트")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    # 매니저 생성
    manager = CrawlerManager()
    
    # 위젯 생성
    widget = CrawlerDashboardWidget()
    widget.setWindowTitle("Test 3: 전체 통합 테스트")
    widget.resize(1200, 800)
    
    # 연결
    widget.set_system(manager)
    widget.register_site('38com', manager.health_monitor)
    
    # 크롤러를 아바타로 등록
    crawler_avatar = manager.get_crawler_as_avatar()
    widget.register_avatar('38com_crawler', crawler_avatar)
    
    # 초기 데이터 생성
    for _ in range(10):
        success = random.random() < 0.85
        manager.record_request(
            success=success,
            response_time=random.uniform(0.5, 3.0),
            status_code=200 if success else random.choice([403, 429, 500])
        )
    
    # 통계 업데이트
    manager.stats['total_collected'] = 25
    manager.stats['active_sources'] = 1
    
    # 초기 로그
    widget.log("시스템 초기화 완료", "SUCCESS")
    widget.log("38com 사이트 등록 완료", "INFO")
    widget.log("크롤러 초기화 완료", "SUCCESS")
    
    # 시뮬레이션
    def simulate():
        success = random.random() < 0.8
        response_time = random.uniform(0.5, 3.0)
        status_code = 200 if success else random.choice([403, 429, 500])
        
        manager.record_request(
            success=success,
            response_time=response_time,
            status_code=status_code
        )
        
        if success:
            manager.stats['total_collected'] += 1
            widget.log(f"보고서 수집 완료: {manager.stats['total_collected']}개", "SUCCESS")
        else:
            widget.log(f"요청 실패: {status_code}", "WARNING")
    
    # 타이머
    timer = QTimer()
    timer.timeout.connect(simulate)
    timer.start(5000)  # 5초마다
    
    widget.show()
    
    print("✅ 전체 통합 테스트가 시작되었습니다.")
    print("   5초마다 요청이 시뮬레이션됩니다.")
    print("   모든 위젯이 실시간으로 업데이트됩니다.")
    
    sys.exit(app.exec_())

def main():
    """메인 함수"""
    
    print("\n" + "="*60)
    print("🧪 모니터링 위젯 통합 테스트")
    print("="*60)
    
    print("\n선택하세요:")
    print("1. 기본 위젯 표시")
    print("2. 크롤러 매니저 통합")
    print("3. 전체 통합 테스트")
    print("0. 종료")
    
    choice = input("\n선택 (0-3): ").strip()
    
    if choice == '1':
        test_basic_widget()
    elif choice == '2':
        test_with_manager()
    elif choice == '3':
        test_full_integration()
    elif choice == '0':
        print("종료합니다.")
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 명령줄 인수
        test_num = sys.argv[1]
        
        if test_num == '1':
            test_basic_widget()
        elif test_num == '2':
            test_with_manager()
        elif test_num == '3':
            test_full_integration()
        else:
            print(f"사용법: python {sys.argv[0]} [1-3]")
    else:
        # 메뉴
        main()



