# analyst_report_scorer.py
"""
애널리스트 리포트 점수화 시스템

실전 투자 관점에서 리포트를 점수화하여 매매 신호로 변환

계약:
- 입력: report (Dict, 리포트 메타데이터), previous_reports (Optional[List[Dict]], 이전 리포트 목록)
- 출력: ReportScore (점수화된 리포트) 또는 Dict (컨센서스 정보)
- 예외: ValueError (잘못된 리포트 데이터), KeyError (필수 필드 누락)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

@dataclass
class ReportScore:
    """리포트 점수"""
    report_id: str
    stock_code: str
    stock_name: str
    
    # 기본 점수
    base_score: float  # BUY/HOLD/SELL 점수
    
    # 목표가 변화 점수
    target_price_change_score: float  # 상향/하향 점수
    
    # 시간 가중치
    time_weight: float  # 최근 리포트 가중치
    
    # 최종 점수
    final_score: float
    
    # 메타데이터
    firm: str
    analyst: str
    date: datetime
    opinion: str
    target_price: Optional[int]
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data

class AnalystReportScorer:
    """
    애널리스트 리포트 점수화 시스템
    
    점수 체계:
    - BUY = +2
    - HOLD = 0
    - SELL = -2
    
    - 목표가 상향 = +1
    - 목표가 하향 = -1
    
    - 최근 7일 리포트 = 가중치 ×1.5
    """
    
    # 의견 점수
    OPINION_SCORES = {
        'BUY': 2.0,
        'HOLD': 0.0,
        'SELL': -2.0,
        '매수': 2.0,
        '보유': 0.0,
        '매도': -2.0
    }
    
    # 목표가 변화 점수
    TARGET_PRICE_UP = 1.0
    TARGET_PRICE_DOWN = -1.0
    
    # 시간 가중치
    RECENT_DAYS = 7
    RECENT_WEIGHT = 1.5
    NORMAL_WEIGHT = 1.0
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.history: Dict[str, List[Dict]] = {}  # stock_code → [이전 리포트들]
    
    def score_report(
        self,
        report: Dict,
        previous_reports: Optional[List[Dict]] = None
    ) -> ReportScore:
        """
        리포트 점수화
        
        Args:
            report: 리포트 메타데이터 (dict)
                - 필수 키: 'stock_code', 'stock_name', 'published_date'
                - 선택 키: 'investment_opinion', 'target_price', 'firm', 'analyst_name'
            previous_reports: 이전 리포트 목록 (목표가 변화 계산용, 기본값: None)
                - 각 리포트는 'date', 'target_price', 'opinion' 키 포함
        
        Returns:
            ReportScore: 점수화된 리포트 객체
            
        Raises:
            ValueError: report가 None이거나 필수 필드 누락
            KeyError: 필수 키가 report에 없음
            
        계약:
        - 입력: report는 dict 타입, 필수 키 포함
        - 출력: ReportScore 객체 (final_score 포함)
        - 예외: ValueError (잘못된 데이터), KeyError (필수 필드 누락)
        """
        
        # 입력 검증
        if not report or not isinstance(report, dict):
            raise ValueError(f"report must be a non-empty dict, got {report}")
        
        stock_code = report.get('stock_code', 'UNKNOWN')
        stock_name = report.get('stock_name', 'UNKNOWN')
        opinion = report.get('investment_opinion', 'HOLD')
        target_price = report.get('target_price')
        published_date = report.get('published_date')
        
        if not published_date:
            raise ValueError("published_date is required in report")
        
        # datetime 변환
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date)
            except:
                published_date = datetime.now()
        elif not isinstance(published_date, datetime):
            published_date = datetime.now()
        
        # 1. 기본 점수 (의견)
        base_score = self._get_opinion_score(opinion)
        
        # 2. 목표가 변화 점수
        target_price_change_score = self._calculate_target_price_change(
            stock_code,
            target_price,
            previous_reports or self.history.get(stock_code, [])
        )
        
        # 3. 시간 가중치
        days_ago = (datetime.now() - published_date).days
        time_weight = self._calculate_time_weight(days_ago)
        
        # 4. 최종 점수 계산
        final_score = (base_score + target_price_change_score) * time_weight
        
        # 이력 저장
        if stock_code not in self.history:
            self.history[stock_code] = []
        
        self.history[stock_code].append({
            'date': published_date,
            'target_price': target_price,
            'opinion': opinion
        })
        
        # 오래된 이력 정리 (최근 30일만 유지)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.history[stock_code] = [
            h for h in self.history[stock_code]
            if h['date'] >= cutoff_date
        ]
        
        return ReportScore(
            report_id=report.get('report_id', ''),
            stock_code=stock_code,
            stock_name=stock_name,
            base_score=base_score,
            target_price_change_score=target_price_change_score,
            time_weight=time_weight,
            final_score=final_score,
            firm=report.get('firm', 'UNKNOWN'),
            analyst=report.get('analyst_name', 'UNKNOWN'),
            date=published_date,
            opinion=opinion,
            target_price=target_price
        )
    
    def score_multiple_reports(
        self,
        reports: List[Dict]
    ) -> List[ReportScore]:
        """여러 리포트 점수화"""
        
        scores = []
        
        # 종목별로 그룹화
        reports_by_stock: Dict[str, List[Dict]] = {}
        for report in reports:
            stock_code = report.get('stock_code', 'UNKNOWN')
            if stock_code not in reports_by_stock:
                reports_by_stock[stock_code] = []
            reports_by_stock[stock_code].append(report)
        
        # 종목별로 점수화 (이전 리포트 참조 가능)
        for stock_code, stock_reports in reports_by_stock.items():
            # 날짜순 정렬
            stock_reports.sort(key=lambda x: self._get_date(x))
            
            previous_reports = self.history.get(stock_code, [])
            
            for report in stock_reports:
                score = self.score_report(report, previous_reports)
                scores.append(score)
                
                # 이전 리포트 목록 업데이트
                previous_reports.append({
                    'date': score.date,
                    'target_price': score.target_price,
                    'opinion': score.opinion
                })
        
        return scores
    
    def get_stock_consensus_score(
        self,
        stock_code: str,
        days: int = 7
    ) -> Dict:
        """
        종목별 컨센서스 점수 계산
        
        Args:
            stock_code: 종목 코드
            days: 최근 N일 리포트만 고려
            
        Returns:
            {
                'total_score': float,
                'average_score': float,
                'report_count': int,
                'buy_count': int,
                'hold_count': int,
                'sell_count': int,
                'recent_upgrades': int,  # 목표가 상향
                'recent_downgrades': int  # 목표가 하향
            }
        """
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_reports = [
            h for h in self.history.get(stock_code, [])
            if h['date'] >= cutoff_date
        ]
        
        if not recent_reports:
            return {
                'total_score': 0.0,
                'average_score': 0.0,
                'report_count': 0,
                'buy_count': 0,
                'hold_count': 0,
                'sell_count': 0,
                'recent_upgrades': 0,
                'recent_downgrades': 0
            }
        
        total_score = 0.0
        buy_count = 0
        hold_count = 0
        sell_count = 0
        upgrades = 0
        downgrades = 0
        
        # 이전 목표가 추적
        previous_target = None
        
        for report in sorted(recent_reports, key=lambda x: x['date']):
            # 의견 점수
            opinion_score = self._get_opinion_score(report.get('opinion', 'HOLD'))
            total_score += opinion_score
            
            # 의견 카운트
            opinion = report.get('opinion', '').upper()
            if 'BUY' in opinion or '매수' in opinion:
                buy_count += 1
            elif 'SELL' in opinion or '매도' in opinion:
                sell_count += 1
            else:
                hold_count += 1
            
            # 목표가 변화 추적
            current_target = report.get('target_price')
            if previous_target is not None and current_target is not None:
                if current_target > previous_target:
                    upgrades += 1
                elif current_target < previous_target:
                    downgrades += 1
            
            previous_target = current_target
        
        return {
            'total_score': total_score,
            'average_score': total_score / len(recent_reports) if recent_reports else 0.0,
            'report_count': len(recent_reports),
            'buy_count': buy_count,
            'hold_count': hold_count,
            'sell_count': sell_count,
            'recent_upgrades': upgrades,
            'recent_downgrades': downgrades
        }
    
    def _get_opinion_score(self, opinion: Optional[str]) -> float:
        """의견 점수 계산"""
        if not opinion:
            return 0.0
        
        opinion_upper = str(opinion).upper()
        
        for key, score in self.OPINION_SCORES.items():
            if key.upper() in opinion_upper:
                return score
        
        return 0.0
    
    def _calculate_target_price_change(
        self,
        stock_code: str,
        current_target_price: Optional[int],
        previous_reports: List[Dict]
    ) -> float:
        """목표가 변화 점수 계산"""
        
        if not current_target_price or not previous_reports:
            return 0.0
        
        # 가장 최근 리포트의 목표가 찾기
        sorted_reports = sorted(
            previous_reports,
            key=lambda x: x.get('date', datetime.min),
            reverse=True
        )
        
        for prev_report in sorted_reports:
            prev_target = prev_report.get('target_price')
            if prev_target is not None:
                if current_target_price > prev_target:
                    return self.TARGET_PRICE_UP
                elif current_target_price < prev_target:
                    return self.TARGET_PRICE_DOWN
        
        return 0.0
    
    def _calculate_time_weight(self, days_ago: int) -> float:
        """시간 가중치 계산"""
        if days_ago <= self.RECENT_DAYS:
            return self.RECENT_WEIGHT
        return self.NORMAL_WEIGHT
    
    def _get_date(self, report: Dict) -> datetime:
        """리포트에서 날짜 추출"""
        date = report.get('published_date')
        if isinstance(date, str):
            try:
                return datetime.fromisoformat(date)
            except:
                return datetime.now()
        elif isinstance(date, datetime):
            return date
        return datetime.now()

# ============================================================
# 사용 예제
# ============================================================

def main():
    """메인 함수"""
    
    scorer = AnalystReportScorer()
    
    # 예시 리포트들
    reports = [
        {
            'report_id': '1',
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'investment_opinion': 'BUY',
            'target_price': 98000,
            'firm': 'NH투자증권',
            'analyst_name': '홍길동',
            'published_date': datetime.now() - timedelta(days=1)
        },
        {
            'report_id': '2',
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'investment_opinion': 'HOLD',
            'target_price': 85000,
            'firm': 'KB증권',
            'analyst_name': '김철수',
            'published_date': datetime.now() - timedelta(days=3)
        },
        {
            'report_id': '3',
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'investment_opinion': 'BUY',
            'target_price': 95000,  # 이전보다 상향
            'firm': '미래에셋',
            'analyst_name': '이영희',
            'published_date': datetime.now() - timedelta(days=5)
        }
    ]
    
    # 점수화
    scores = scorer.score_multiple_reports(reports)
    
    print("📊 리포트 점수화 결과:\n")
    for score in scores:
        print(f"종목: {score.stock_name} ({score.stock_code})")
        print(f"  증권사: {score.firm} / 애널리스트: {score.analyst}")
        print(f"  의견: {score.opinion} (기본 점수: {score.base_score})")
        print(f"  목표가: {score.target_price} (변화 점수: {score.target_price_change_score})")
        print(f"  시간 가중치: {score.time_weight}")
        print(f"  최종 점수: {score.final_score:.2f}")
        print()
    
    # 컨센서스 점수
    consensus = scorer.get_stock_consensus_score('005930', days=7)
    print("📈 종목 컨센서스:")
    print(f"  총 점수: {consensus['total_score']:.2f}")
    print(f"  평균 점수: {consensus['average_score']:.2f}")
    print(f"  리포트 수: {consensus['report_count']}개")
    print(f"  BUY: {consensus['buy_count']}개, HOLD: {consensus['hold_count']}개, SELL: {consensus['sell_count']}개")
    print(f"  목표가 상향: {consensus['recent_upgrades']}개, 하향: {consensus['recent_downgrades']}개")

if __name__ == "__main__":
    main()

