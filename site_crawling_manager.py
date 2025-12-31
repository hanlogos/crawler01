# site_crawling_manager.py
"""
사이트별 크롤링 관리 시스템

각 사이트별로 크롤링 상태를 관리하고 제어
"""

import sys
import io
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import threading
import time

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class CrawlingStatus(Enum):
    """크롤링 상태"""
    IDLE = "idle"  # 대기
    RUNNING = "running"  # 실행 중
    PAUSED = "paused"  # 일시정지
    STOPPED = "stopped"  # 정지
    ERROR = "error"  # 오류

class CrawlingMode(Enum):
    """크롤링 모드"""
    MANUAL = "manual"  # 수동
    AUTO = "auto"  # 자동

@dataclass
class SiteCrawlingState:
    """사이트 크롤링 상태"""
    site_id: str
    site_name: str
    site_url: str
    
    # 상태
    status: CrawlingStatus = CrawlingStatus.IDLE
    mode: CrawlingMode = CrawlingMode.MANUAL
    
    # 통계
    total_collected: int = 0
    total_failed: int = 0
    last_collected: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # 진행 상황
    current_progress: int = 0
    total_target: int = 0
    
    # 스케줄
    schedule: Dict = None  # {'interval': 'daily', 'time': '09:00'}
    next_run: Optional[datetime] = None
    
    # 설정
    days: int = 1
    max_reports: int = 100
    fake_face_profile: str = 'casual'
    
    # 메타데이터
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.schedule is None:
            self.schedule = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['mode'] = self.mode.value
        if self.last_collected:
            data['last_collected'] = self.last_collected.isoformat()
        if self.next_run:
            data['next_run'] = self.next_run.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

class SiteCrawlingManager:
    """사이트별 크롤링 관리자"""
    
    def __init__(self):
        self.sites: Dict[str, SiteCrawlingState] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._running_tasks: Dict[str, threading.Thread] = {}
        
        # 상태 파일
        self.state_file = "crawling_states.json"
        self._load_states()
    
    def register_site(
        self,
        site_id: str,
        site_name: str,
        site_url: str,
        **kwargs
    ) -> SiteCrawlingState:
        """사이트 등록"""
        
        if site_id in self.sites:
            self.logger.warning(f"사이트 이미 등록됨: {site_id}")
            return self.sites[site_id]
        
        state = SiteCrawlingState(
            site_id=site_id,
            site_name=site_name,
            site_url=site_url,
            **kwargs
        )
        
        self.sites[site_id] = state
        self._save_states()
        
        self.logger.info(f"사이트 등록: {site_id} ({site_name})")
        return state
    
    def get_site_state(self, site_id: str) -> Optional[SiteCrawlingState]:
        """사이트 상태 가져오기"""
        return self.sites.get(site_id)
    
    def start_crawling(
        self,
        site_id: str,
        mode: CrawlingMode = CrawlingMode.MANUAL
    ) -> bool:
        """크롤링 시작"""
        
        with self._lock:
            state = self.sites.get(site_id)
            if not state:
                self.logger.error(f"사이트를 찾을 수 없습니다: {site_id}")
                return False
            
            if state.status == CrawlingStatus.RUNNING:
                self.logger.warning(f"이미 실행 중입니다: {site_id}")
                return False
            
            state.status = CrawlingStatus.RUNNING
            state.mode = mode
            state.updated_at = datetime.now()
            
            # 스레드 시작
            thread = threading.Thread(
                target=self._crawling_worker,
                args=(site_id,),
                daemon=True
            )
            self._running_tasks[site_id] = thread
            thread.start()
            
            self._save_states()
            self.logger.info(f"크롤링 시작: {site_id} ({mode.value} 모드)")
            return True
    
    def pause_crawling(self, site_id: str) -> bool:
        """크롤링 일시정지"""
        
        with self._lock:
            state = self.sites.get(site_id)
            if not state:
                return False
            
            if state.status == CrawlingStatus.RUNNING:
                state.status = CrawlingStatus.PAUSED
                state.updated_at = datetime.now()
                self._save_states()
                self.logger.info(f"크롤링 일시정지: {site_id}")
                return True
            
            return False
    
    def resume_crawling(self, site_id: str) -> bool:
        """크롤링 이어가기"""
        
        with self._lock:
            state = self.sites.get(site_id)
            if not state:
                return False
            
            if state.status == CrawlingStatus.PAUSED:
                state.status = CrawlingStatus.RUNNING
                state.updated_at = datetime.now()
                self._save_states()
                self.logger.info(f"크롤링 재개: {site_id}")
                return True
            
            return False
    
    def stop_crawling(self, site_id: str) -> bool:
        """크롤링 정지"""
        
        with self._lock:
            state = self.sites.get(site_id)
            if not state:
                return False
            
            if state.status in [CrawlingStatus.RUNNING, CrawlingStatus.PAUSED]:
                state.status = CrawlingStatus.STOPPED
                state.updated_at = datetime.now()
                self._save_states()
                self.logger.info(f"크롤링 정지: {site_id}")
                return True
            
            return False
    
    def clear_site_data(self, site_id: str) -> bool:
        """사이트 데이터 지우기"""
        
        with self._lock:
            state = self.sites.get(site_id)
            if not state:
                return False
            
            state.total_collected = 0
            state.total_failed = 0
            state.current_progress = 0
            state.last_collected = None
            state.last_error = None
            state.updated_at = datetime.now()
            
            self._save_states()
            self.logger.info(f"사이트 데이터 초기화: {site_id}")
            return True
    
    def save_site_data(self, site_id: str, filename: str = None) -> bool:
        """사이트 데이터 저장"""
        
        state = self.sites.get(site_id)
        if not state:
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crawling_data_{site_id}_{timestamp}.json"
        
        data = {
            'site_id': site_id,
            'state': state.to_dict(),
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"데이터 저장 완료: {filename}")
            return True
        
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {e}")
            return False
    
    def _crawling_worker(self, site_id: str):
        """크롤링 워커 (스레드)"""
        
        state = self.sites.get(site_id)
        if not state:
            return
        
        try:
            # 실제 크롤링 로직
            from integrated_crawler_manager import IntegratedCrawlerManager
            
            manager = IntegratedCrawlerManager(
                use_fake_face=True,
                fake_face_profile=state.fake_face_profile
            )
            
            # total_target이 설정되지 않았으면 기본값 설정
            if state.total_target == 0:
                state.total_target = state.max_reports
            
            self.logger.info(f"크롤링 시작: {site_id} (목표: {state.total_target}개)")
            
            # 크롤링 실행
            while state.status == CrawlingStatus.RUNNING:
                # 일시정지 확인
                if state.status == CrawlingStatus.PAUSED:
                    time.sleep(1)
                    continue
                
                # 정지 확인
                if state.status == CrawlingStatus.STOPPED:
                    break
                
                try:
                    # 실제 크롤링 실행
                    # 38com 사이트인 경우 실제 크롤러 사용
                    if site_id == "38com":
                        from crawler_38com import ThirtyEightComCrawler
                        crawler = ThirtyEightComCrawler(
                            delay=3.0,
                            max_retries=3,
                            use_adaptive=True
                        )
                        
                        # 최근 보고서 크롤링
                        self.logger.info(f"크롤링 실행 중: {site_id} (days={state.days}, max={state.max_reports})")
                        reports = crawler.crawl_recent_reports(
                            days=state.days,
                            max_reports=state.max_reports
                        )
                        
                        if reports:
                            state.current_progress = len(reports)
                            state.total_collected += len(reports)
                            state.last_collected = datetime.now()
                            state.updated_at = datetime.now()
                            self.logger.info(f"✅ 크롤링 완료: {site_id} - {len(reports)}개 보고서 수집")
                        else:
                            self.logger.warning(f"⚠️  크롤링 결과 없음: {site_id}")
                        
                        # 크롤링 완료 후 종료
                        state.status = CrawlingStatus.IDLE
                        break
                    elif site_id == "hankyung_consensus":
                        # 한경 컨센서스 크롤러 사용
                        from crawler_hankyung_consensus import HankyungConsensusCrawler
                        crawler = HankyungConsensusCrawler(
                            delay=3.0,
                            max_retries=3,
                            use_adaptive=True
                        )
                        
                        # 최근 보고서 크롤링
                        self.logger.info(f"크롤링 실행 중: {site_id} (days={state.days}, max={state.max_reports})")
                        reports = crawler.crawl_recent_reports(
                            days=state.days,
                            max_reports=state.max_reports,
                            report_type="stock"  # 기본적으로 종목 리포트
                        )
                        
                        if reports:
                            state.current_progress = len(reports)
                            state.total_collected += len(reports)
                            state.last_collected = datetime.now()
                            state.updated_at = datetime.now()
                            self.logger.info(f"✅ 크롤링 완료: {site_id} - {len(reports)}개 보고서 수집")
                            
                            # 정규화 및 저장 파이프라인 통합 (옵션)
                            try:
                                from analyst_report_pipeline import AnalystReportPipeline
                                import os
                                
                                db_params = {
                                    'host': os.getenv('DB_HOST', 'localhost'),
                                    'database': os.getenv('DB_NAME', 'crawler_db'),
                                    'user': os.getenv('DB_USER', 'postgres'),
                                    'password': os.getenv('DB_PASSWORD', '')
                                }
                                
                                # DB 저장 활성화 여부 확인 (환경변수 또는 설정)
                                enable_db = os.getenv('ENABLE_DB_STORAGE', 'false').lower() == 'true'
                                
                                if enable_db and db_params.get('password'):
                                    pipeline = AnalystReportPipeline(db_params, enable_db=True)
                                    saved_count = pipeline.process_reports(reports, source='hankyung', skip_errors=True)
                                    self.logger.info(f"💾 DB 저장 완료: {saved_count}개 리포트 저장")
                                else:
                                    self.logger.debug("DB 저장 비활성화 (ENABLE_DB_STORAGE=false 또는 DB_PASSWORD 없음)")
                                    
                            except ImportError:
                                self.logger.debug("정규화 파이프라인 모듈을 사용할 수 없습니다. 크롤링만 수행합니다.")
                            except Exception as e:
                                self.logger.warning(f"정규화/저장 실패 (크롤링은 성공): {e}")
                        else:
                            self.logger.warning(f"⚠️  크롤링 결과 없음: {site_id}")
                        
                        # 크롤링 완료 후 종료
                        state.status = CrawlingStatus.IDLE
                        break
                    else:
                        # 다른 사이트는 통합 크롤러 사용
                        # 여기서는 시뮬레이션 (필요시 확장)
                        state.current_progress += 1
                        state.total_collected += 1
                        state.last_collected = datetime.now()
                        state.updated_at = datetime.now()
                        
                        self._save_states()
                        
                        # 대기
                        time.sleep(2)
                        
                        # 목표 달성 확인
                        if state.current_progress >= state.total_target:
                            state.status = CrawlingStatus.IDLE
                            break
                
                except Exception as e:
                    self.logger.error(f"크롤링 실행 중 오류 ({site_id}): {e}")
                    state.total_failed += 1
                    state.last_error = str(e)
                    # 오류 발생해도 계속 진행 (재시도)
                    time.sleep(5)
                    continue
        
        except Exception as e:
            state.status = CrawlingStatus.ERROR
            state.last_error = str(e)
            state.updated_at = datetime.now()
            self.logger.error(f"크롤링 워커 오류 ({site_id}): {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        finally:
            state.updated_at = datetime.now()
            self._save_states()
            if site_id in self._running_tasks:
                del self._running_tasks[site_id]
            self.logger.info(f"크롤링 워커 종료: {site_id}")
    
    def _load_states(self):
        """상태 로드"""
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for site_data in data.get('sites', []):
                state = SiteCrawlingState(**site_data)
                # enum 변환
                state.status = CrawlingStatus(state.status) if isinstance(state.status, str) else state.status
                state.mode = CrawlingMode(state.mode) if isinstance(state.mode, str) else state.mode
                # datetime 변환
                if isinstance(state.last_collected, str):
                    state.last_collected = datetime.fromisoformat(state.last_collected)
                if isinstance(state.next_run, str):
                    state.next_run = datetime.fromisoformat(state.next_run)
                
                self.sites[state.site_id] = state
            
            self.logger.info(f"상태 로드 완료: {len(self.sites)}개 사이트")
        
        except FileNotFoundError:
            self.logger.info("상태 파일이 없습니다. 새로 시작합니다.")
        except Exception as e:
            self.logger.error(f"상태 로드 실패: {e}")
    
    def _save_states(self):
        """상태 저장"""
        
        try:
            data = {
                'sites': [state.to_dict() for state in self.sites.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"상태 저장 실패: {e}")
    
    def get_all_states(self) -> List[SiteCrawlingState]:
        """모든 사이트 상태 가져오기"""
        return list(self.sites.values())
    
    def update_schedule(self, site_id: str, schedule: Dict):
        """스케줄 업데이트"""
        
        state = self.sites.get(site_id)
        if not state:
            return False
        
        state.schedule = schedule
        state.mode = CrawlingMode.AUTO if schedule else CrawlingMode.MANUAL
        
        # 다음 실행 시간 계산
        if schedule:
            state.next_run = self._calculate_next_run(schedule)
        
        state.updated_at = datetime.now()
        self._save_states()
        
        return True
    
    def _calculate_next_run(self, schedule: Dict) -> Optional[datetime]:
        """다음 실행 시간 계산"""
        
        now = datetime.now()
        
        if schedule.get('interval') == 'daily':
            time_str = schedule.get('time', '09:00')
            hour, minute = map(int, time_str.split(':'))
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            
            return next_run
        
        elif schedule.get('interval') == 'weekly':
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2,
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            target_day = day_map.get(schedule.get('day', 'monday').lower(), 0)
            time_str = schedule.get('time', '10:00')
            hour, minute = map(int, time_str.split(':'))
            
            days_ahead = target_day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_run
        
        return None

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("사이트별 크롤링 관리 시스템 테스트")
    print("="*60)
    print()
    
    manager = SiteCrawlingManager()
    
    # 사이트 등록
    site1 = manager.register_site(
        site_id="38com",
        site_name="38커뮤니케이션",
        site_url="http://www.38.co.kr",
        days=1,
        max_reports=50,
        fake_face_profile='casual'
    )
    
    print(f"사이트 등록: {site1.site_name}")
    print(f"  상태: {site1.status.value}")
    print(f"  모드: {site1.mode.value}")
    
    # 스케줄 설정
    manager.update_schedule("38com", {
        'interval': 'daily',
        'time': '09:00'
    })
    
    state = manager.get_site_state("38com")
    if state and state.next_run:
        print(f"  다음 실행: {state.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n✅ 테스트 완료!")


