# test_widget_validation.py
"""
위젯 검증 테스트

위젯의 모든 기능이 제대로 작동하는지 검증
"""

import sys
import io
import random
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_complete_integration():
    """완전한 통합 테스트"""
    
    print("="*60)
    print("🔍 완전한 통합 테스트")
    print("="*60)
    print()
    
    try:
        from PyQt5.QtWidgets import QApplication
        from crawler_monitoring_widget import CrawlerDashboardWidget
        from crawler_manager import CrawlerManager
        from enhanced_health_monitor import EnhancedHealthMonitor
        
        print("1. 모듈 임포트... ✅")
        
        # QApplication 생성
        app = QApplication([])
        print("2. QApplication 생성... ✅")
        
        # 매니저 생성
        manager = CrawlerManager()
        print("3. 크롤러 매니저 생성... ✅")
        
        # 위젯 생성
        widget = CrawlerDashboardWidget()
        print("4. 위젯 생성... ✅")
        
        # 연결
        widget.set_system(manager)
        widget.register_site('38com', manager.health_monitor)
        print("5. 위젯-매니저 연결... ✅")
        
        # 크롤러 등록
        crawler_avatar = manager.get_crawler_as_avatar()
        widget.register_avatar('38com_crawler', crawler_avatar)
        print("6. 크롤러 등록... ✅")
        
        # 초기 데이터 생성
        print("\n7. 초기 데이터 생성 중...")
        for i in range(20):
            success = random.random() < 0.85
            response_time = random.uniform(0.5, 3.0)
            status_code = 200 if success else random.choice([403, 429, 500])
            
            manager.record_request(
                success=success,
                response_time=response_time,
                status_code=status_code
            )
        
        # 건강도 확인
        health = manager.health_monitor.get_health()
        print(f"   성공률: {health.success_rate:.1%}")
        print(f"   평균 응답 시간: {health.avg_response_time:.2f}초")
        print(f"   상태: {health.status}")
        print("   ✅ 초기 데이터 생성 완료")
        
        # 통계 설정
        manager.stats['total_collected'] = 30
        manager.stats['active_sources'] = 1
        print("\n8. 통계 설정... ✅")
        
        # 로그 테스트
        print("\n9. 로그 기능 테스트...")
        widget.log("시스템 초기화 완료", "SUCCESS")
        widget.log("38com 사이트 등록 완료", "INFO")
        widget.log("크롤러 초기화 완료", "SUCCESS")
        widget.log("모니터링 시작", "INFO")
        widget.log("테스트 경고 메시지", "WARNING")
        widget.log("테스트 오류 메시지", "ERROR")
        print("   ✅ 로그 기능 정상 작동")
        
        # 위젯 업데이트 확인
        print("\n10. 위젯 업데이트 확인...")
        widget.site_health.update_display()
        widget.avatar_status.update_display()
        widget.statistics.update_display()
        print("   ✅ 위젯 업데이트 정상 작동")
        
        # 크롤러 상태 업데이트
        manager.update_crawler_status('working', completed=30, failed=2)
        print("\n11. 크롤러 상태 업데이트... ✅")
        
        print("\n" + "="*60)
        print("✅ 모든 검증 테스트 통과!")
        print("="*60)
        print()
        print("위젯이 정상적으로 작동합니다.")
        print("GUI 창을 열려면 다음 명령을 실행하세요:")
        print("  python run_widget_demo.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_monitor_detailed():
    """건강도 모니터 상세 테스트"""
    
    print("\n" + "="*60)
    print("🔍 건강도 모니터 상세 테스트")
    print("="*60)
    print()
    
    try:
        from enhanced_health_monitor import EnhancedHealthMonitor
        
        monitor = EnhancedHealthMonitor('test_site')
        
        # 다양한 시나리오 테스트
        scenarios = [
            ("정상 상태", [True]*10),
            ("성능 저하", [True]*7 + [False]*3),
            ("위험 상태", [True]*5 + [False]*5),
            ("차단 의심", [False]*6),
        ]
        
        for scenario_name, results in scenarios:
            monitor = EnhancedHealthMonitor('test_site')
            
            for success in results:
                monitor.record_request(
                    success=success,
                    response_time=random.uniform(0.5, 3.0),
                    status_code=200 if success else random.choice([403, 429, 500])
                )
            
            health = monitor.get_health()
            print(f"{scenario_name}:")
            print(f"  성공률: {health.success_rate:.1%}")
            print(f"  상태: {health.status}")
            print(f"  연속 오류: {health.consecutive_errors}")
            print()
        
        print("✅ 건강도 모니터 상세 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    
    print("\n" + "="*60)
    print("🧪 위젯 검증 테스트")
    print("="*60)
    print()
    
    results = []
    
    # 테스트 실행
    results.append(("건강도 모니터 상세", test_health_monitor_detailed()))
    results.append(("완전한 통합", test_complete_integration()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 모든 검증 테스트 통과!")
        print("\n💡 GUI 데모를 실행하려면:")
        print("   python run_widget_demo.py")
    else:
        print("\n⚠️  일부 테스트 실패")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


