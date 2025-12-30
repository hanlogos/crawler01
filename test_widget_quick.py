# test_widget_quick.py
"""
위젯 빠른 테스트 (GUI 없이)

위젯이 제대로 임포트되고 초기화되는지 확인
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_imports():
    """임포트 테스트"""
    print("="*60)
    print("Test: 모듈 임포트")
    print("="*60)
    
    try:
        from crawler_monitoring_widget import (
            CrawlerDashboardWidget,
            SiteHealthWidget,
            AvatarStatusWidget,
            StatisticsWidget,
            ActivityLogWidget
        )
        print("✅ 위젯 모듈 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ 위젯 모듈 임포트 실패: {e}")
        return False

def test_manager():
    """크롤러 매니저 테스트"""
    print("\n" + "="*60)
    print("Test: 크롤러 매니저")
    print("="*60)
    
    try:
        from crawler_manager import CrawlerManager
        
        manager = CrawlerManager()
        print("✅ 크롤러 매니저 생성 성공")
        
        # 통계 확인
        stats = manager.get_global_stats()
        print(f"   통계: {stats}")
        
        # 건강도 모니터 확인
        health = manager.health_monitor.get_health()
        print(f"   건강도 상태: {health.status}")
        
        return True
    except Exception as e:
        print(f"❌ 크롤러 매니저 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_monitor():
    """건강도 모니터 테스트"""
    print("\n" + "="*60)
    print("Test: 건강도 모니터")
    print("="*60)
    
    try:
        from enhanced_health_monitor import EnhancedHealthMonitor
        
        monitor = EnhancedHealthMonitor('test_site')
        print("✅ 건강도 모니터 생성 성공")
        
        # 초기 상태
        health = monitor.get_health()
        print(f"   초기 상태: {health.status}")
        
        # 요청 기록
        monitor.record_request(True, 1.5, 200)
        monitor.record_request(True, 2.0, 200)
        monitor.record_request(False, 0.5, 429)
        
        health = monitor.get_health()
        print(f"   성공률: {health.success_rate:.1%}")
        print(f"   평균 응답 시간: {health.avg_response_time:.2f}초")
        print(f"   상태: {health.status}")
        
        return True
    except Exception as e:
        print(f"❌ 건강도 모니터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_creation():
    """위젯 생성 테스트 (GUI 없이)"""
    print("\n" + "="*60)
    print("Test: 위젯 생성 (GUI 없이)")
    print("="*60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from crawler_monitoring_widget import CrawlerDashboardWidget
        from crawler_manager import CrawlerManager
        
        # QApplication 생성 (GUI 없이)
        app = QApplication([])
        
        # 위젯 생성
        widget = CrawlerDashboardWidget()
        print("✅ 위젯 생성 성공")
        
        # 매니저 생성
        manager = CrawlerManager()
        print("✅ 매니저 생성 성공")
        
        # 연결
        widget.set_system(manager)
        widget.register_site('38com', manager.health_monitor)
        print("✅ 위젯-매니저 연결 성공")
        
        # 크롤러 등록
        crawler_avatar = manager.get_crawler_as_avatar()
        widget.register_avatar('38com_crawler', crawler_avatar)
        print("✅ 크롤러 등록 성공")
        
        # 로그 테스트
        widget.log("테스트 로그", "INFO")
        widget.log("성공 로그", "SUCCESS")
        widget.log("경고 로그", "WARNING")
        print("✅ 로그 기능 테스트 성공")
        
        print("\n✅ 모든 테스트 통과!")
        print("\n💡 GUI 테스트를 실행하려면:")
        print("   python test_widget_integration.py")
        
        return True
    except Exception as e:
        print(f"❌ 위젯 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("🧪 위젯 빠른 테스트 (GUI 없이)")
    print("="*60)
    
    results = []
    
    # 테스트 실행
    results.append(("임포트", test_imports()))
    results.append(("건강도 모니터", test_health_monitor()))
    results.append(("크롤러 매니저", test_manager()))
    results.append(("위젯 생성", test_widget_creation()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n⚠️  일부 테스트 실패")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

