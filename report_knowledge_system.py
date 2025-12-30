# report_knowledge_system.py
"""
보고서 지식 시스템

1번 분석으로 수백 아바타 지원
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# ============================================================
# Core: Report Knowledge
# ============================================================

@dataclass
class ReportKnowledge:
    """보고서 지식"""
    
    report_id: str
    timestamp: datetime
    
    # 기본 정보
    stock_name: str
    stock_code: str
    analyst: str
    firm: str
    report_date: str
    
    # 투자 정보
    investment_opinion: str  # buy/hold/sell
    target_price: Optional[float]
    expected_return: Optional[float]
    
    # 재무 지표 (JSONB)
    financial_metrics: dict
    
    # 매매 신호 (JSONB)
    trading_signals: dict
    
    # 리스크 (List)
    risks: list
    
    # 시장 심리
    sentiment: dict
    
    # 이벤트
    events: list
    
    # 섹터/기술
    sector_info: dict
    technical_info: dict
    
    # 밸류에이션
    valuation: dict
    
    # 원본 텍스트
    raw_content: str

class KnowledgeStore:
    """지식 저장소"""
    
    def __init__(self):
        self.knowledge_db: Dict[str, ReportKnowledge] = {}
        
        # 인덱스 (빠른 조회)
        self.index_by_stock = {}      # stock_code → [report_ids]
        self.index_by_date = {}       # date → [report_ids]
        self.index_by_analyst = {}    # analyst → [report_ids]
        
        self.logger = logging.getLogger(__name__)
    
    def store(self, knowledge: ReportKnowledge):
        """지식 저장"""
        
        report_id = knowledge.report_id
        
        # 메인 저장소
        self.knowledge_db[report_id] = knowledge
        
        # 인덱스 업데이트
        self._update_indexes(knowledge)
        
        self.logger.info(f"저장 완료: {report_id}")
    
    def get(self, report_id: str) -> Optional[ReportKnowledge]:
        """지식 조회"""
        return self.knowledge_db.get(report_id)
    
    def query_aspect(
        self, 
        report_id: str, 
        aspect: str
    ) -> Any:
        """
        특정 측면 쿼리
        
        Args:
            report_id: 보고서 ID
            aspect: 'trading_signals', 'risks', 'financial_metrics' 등
        
        Returns:
            해당 측면 데이터
        """
        
        knowledge = self.get(report_id)
        
        if not knowledge:
            return None
        
        # 속성 가져오기
        return getattr(knowledge, aspect, None)
    
    def query_filtered(
        self,
        report_id: str,
        aspect: str,
        filters: dict
    ) -> Any:
        """
        필터 기반 쿼리
        
        Args:
            report_id: 보고서 ID
            aspect: 측면
            filters: {'timeframe': 'short', 'confidence': 0.8}
        """
        
        data = self.query_aspect(report_id, aspect)
        
        if not data:
            return None
        
        # 필터 적용
        return self._apply_filters(data, filters)
    
    def search_by_stock(self, stock_code: str) -> List[str]:
        """종목별 검색"""
        return self.index_by_stock.get(stock_code, [])
    
    def search_by_date(self, date: str) -> List[str]:
        """날짜별 검색"""
        return self.index_by_date.get(date, [])
    
    def search_by_analyst(self, analyst: str) -> List[str]:
        """애널리스트별 검색"""
        return self.index_by_analyst.get(analyst, [])
    
    def get_all_report_ids(self) -> List[str]:
        """모든 보고서 ID 반환"""
        return list(self.knowledge_db.keys())
    
    def get_stats(self) -> dict:
        """통계 반환"""
        return {
            'total_reports': len(self.knowledge_db),
            'stocks': len(self.index_by_stock),
            'analysts': len(self.index_by_analyst),
            'dates': len(self.index_by_date)
        }
    
    def _update_indexes(self, knowledge: ReportKnowledge):
        """인덱스 업데이트"""
        
        report_id = knowledge.report_id
        
        # 종목 인덱스
        stock_code = knowledge.stock_code
        if stock_code not in self.index_by_stock:
            self.index_by_stock[stock_code] = []
        if report_id not in self.index_by_stock[stock_code]:
            self.index_by_stock[stock_code].append(report_id)
        
        # 날짜 인덱스
        date = knowledge.report_date
        if date not in self.index_by_date:
            self.index_by_date[date] = []
        if report_id not in self.index_by_date[date]:
            self.index_by_date[date].append(report_id)
        
        # 애널리스트 인덱스
        analyst = knowledge.analyst
        if analyst not in self.index_by_analyst:
            self.index_by_analyst[analyst] = []
        if report_id not in self.index_by_analyst[analyst]:
            self.index_by_analyst[analyst].append(report_id)
    
    def _apply_filters(self, data: Any, filters: dict) -> Any:
        """필터 적용"""
        
        if isinstance(data, dict):
            # 딕셔너리: 키로 필터링
            for key, value in filters.items():
                if key in data:
                    data = data[key]
            
            return data
        
        elif isinstance(data, list):
            # 리스트: 조건으로 필터링
            filtered = []
            
            for item in data:
                match = True
                
                for key, value in filters.items():
                    if isinstance(item, dict):
                        if item.get(key) != value:
                            match = False
                            break
                
                if match:
                    filtered.append(item)
            
            return filtered
        
        else:
            return data

# ============================================================
# Extractor: Comprehensive Analysis
# ============================================================

class ComprehensiveExtractor:
    """종합 추출기"""
    
    def __init__(self, llm_processor):
        self.llm = llm_processor
        self.logger = logging.getLogger(__name__)
    
    def extract(self, report_content: str) -> dict:
        """
        보고서에서 모든 정보 추출
        
        Returns:
            종합 추출 결과 (dict)
        """
        
        self.logger.info("종합 정보 추출 시작...")
        
        # 프롬프트 생성
        prompt = self._create_prompt(report_content)
        
        # LLM 호출 (1번만!)
        start = time.time()
        result = self.llm.process(prompt)
        elapsed = time.time() - start
        
        self.logger.info(f"LLM 처리 완료 ({elapsed:.2f}초)")
        
        # JSON 파싱
        extracted = self._parse_json(result)
        
        # 검증
        extracted = self._validate(extracted)
        
        return extracted
    
    def _create_prompt(self, content: str) -> str:
        """프롬프트 생성"""
        
        return f"""다음 애널리스트 보고서를 종합 분석하여 **반드시 유효한 JSON 형식으로만** 반환하세요. 다른 설명이나 텍스트는 포함하지 마세요.

보고서 내용:
{content}

**중요: 반드시 아래 JSON 형식으로만 응답하세요. JSON 코드 블록이나 다른 텍스트 없이 순수 JSON만 반환하세요.**

{{
  "basic": {{
    "stock_name": "종목명",
    "stock_code": "종목코드",
    "analyst": "애널리스트명",
    "firm": "증권사",
    "date": "2024-12-30"
  }},
  "investment": {{
    "opinion": "buy",
    "target_price": 75000,
    "expected_return": 15.5
  }},
  "financial_metrics": {{
    "2024": {{"revenue": 250000000000000, "operating_profit": 35000000000000}},
    "2025": {{"revenue": 270000000000000, "operating_profit": 40000000000000}}
  }},
  "trading_signals": {{
    "short_term": [{{"signal": "buy", "confidence": 0.8, "reason": "실적 호조"}}],
    "medium_term": [{{"signal": "hold", "confidence": 0.7, "reason": "업황 불확실"}}],
    "long_term": [{{"signal": "buy", "confidence": 0.9, "reason": "장기 성장성"}}]
  }},
  "risks": [
    {{"type": "downside", "description": "메모리 가격 하락", "probability": "medium", "impact": "high"}},
    {{"type": "upside", "description": "HBM 수요 증가", "probability": "high", "impact": "high"}}
  ],
  "sentiment": {{
    "overall": "bullish",
    "confidence": 85,
    "factors": ["실적 개선", "신규 수주"]
  }},
  "events": [
    {{"date": "2025-01-15", "event": "실적 발표", "impact": "high"}}
  ],
  "sector_info": {{
    "industry": "반도체",
    "theme": ["AI", "HBM"],
    "competitors": ["SK하이닉스"]
  }},
  "technical_info": {{
    "key_technology": ["HBM3E", "GAA"],
    "competitive_advantage": "공정 기술"
  }},
  "valuation": {{
    "fair_value": 80000,
    "method": "DCF"
  }}
}}

**응답은 순수 JSON만 반환하세요. 다른 텍스트는 포함하지 마세요.**
"""
    
    def _parse_json(self, result: str) -> dict:
        """JSON 파싱"""
        
        # 마크다운 코드 블록 제거
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            # ``` 로 시작하는 코드 블록 찾기
            parts = result.split("```")
            if len(parts) >= 3:
                # 두 번째 부분이 코드 블록 내용
                result = parts[1]
                # 첫 줄이 언어 태그일 수 있으므로 제거
                if result.startswith("json"):
                    result = result[4:].lstrip()
        
        # JSON 시작 부분 찾기
        start_idx = result.find('{')
        if start_idx >= 0:
            result = result[start_idx:]
        
        # JSON 끝 부분 찾기 (마지막 } 찾기)
        last_brace = result.rfind('}')
        if last_brace >= 0:
            result = result[:last_brace + 1]
        
        # 파싱
        try:
            parsed = json.loads(result.strip())
            self.logger.info("✅ JSON 파싱 성공")
            return parsed
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 실패: {e}")
            self.logger.debug(f"파싱 시도한 텍스트 (처음 500자): {result[:500]}")
            
            # 재시도: 더 공격적인 정리
            try:
                # 모든 줄에서 JSON 부분만 추출
                lines = result.split('\n')
                json_lines = []
                in_json = False
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('{') or in_json:
                        in_json = True
                        json_lines.append(line)
                        if stripped.endswith('}') and stripped.count('{') <= stripped.count('}'):
                            break
                
                if json_lines:
                    cleaned = '\n'.join(json_lines)
                    return json.loads(cleaned)
            except:
                pass
            
            return {}
    
    def _validate(self, extracted: dict) -> dict:
        """검증 및 기본값 설정"""
        
        # 필수 필드 확인
        required = ['basic', 'investment', 'trading_signals']
        
        for field in required:
            if field not in extracted:
                extracted[field] = {}
        
        # 기본값 설정
        if 'risks' not in extracted:
            extracted['risks'] = []
        
        if 'events' not in extracted:
            extracted['events'] = []
        
        if 'sentiment' not in extracted:
            extracted['sentiment'] = {}
        
        if 'sector_info' not in extracted:
            extracted['sector_info'] = {}
        
        if 'technical_info' not in extracted:
            extracted['technical_info'] = {}
        
        if 'valuation' not in extracted:
            extracted['valuation'] = {}
        
        if 'financial_metrics' not in extracted:
            extracted['financial_metrics'] = {}
        
        return extracted

# ============================================================
# Avatar: Base Class
# ============================================================

class BaseAvatar:
    """기본 아바타 클래스"""
    
    def __init__(self, avatar_id: str, specialty: str):
        self.avatar_id = avatar_id
        self.specialty = specialty  # 전문 분야
        self.logger = logging.getLogger(f"Avatar.{avatar_id}")
    
    def analyze(
        self, 
        report_id: str, 
        knowledge_store: KnowledgeStore
    ) -> dict:
        """
        분석 (쿼리만)
        
        Args:
            report_id: 보고서 ID
            knowledge_store: 지식 저장소
        
        Returns:
            분석 결과
        """
        
        # 전문 분야 데이터만 쿼리 (0.005초)
        data = knowledge_store.query_aspect(
            report_id=report_id,
            aspect=self.specialty
        )
        
        if not data:
            return {'decision': 'NO_DATA', 'error': '데이터 없음'}
        
        # 분석 로직 (각 아바타 구현)
        result = self._analyze_logic(data)
        
        return result
    
    def _analyze_logic(self, data: Any) -> dict:
        """분석 로직 (override)"""
        raise NotImplementedError

# ============================================================
# Specialized Avatars
# ============================================================

class TradingAvatar(BaseAvatar):
    """매매 전문 아바타"""
    
    def __init__(self, avatar_id: str, timeframe: str = 'short'):
        super().__init__(avatar_id, 'trading_signals')
        self.timeframe = timeframe  # short/medium/long
    
    def _analyze_logic(self, data: dict) -> dict:
        """매매 신호 분석"""
        
        # 시간대별 신호 추출
        timeframe_key = f"{self.timeframe}_term"
        signals = data.get(timeframe_key, [])
        
        if not signals:
            return {'decision': 'HOLD', 'confidence': 0, 'reason': '신호 없음'}
        
        # 평균 신뢰도 계산
        confidences = [s.get('confidence', 0) for s in signals if isinstance(s, dict)]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 결정
        if avg_confidence > 0.7:
            decision = signals[0].get('signal', 'HOLD').upper() if signals else 'HOLD'
        else:
            decision = 'HOLD'
        
        return {
            'decision': decision,
            'confidence': avg_confidence,
            'timeframe': self.timeframe,
            'signals': signals[:3]  # 최대 3개만 반환
        }

class RiskAvatar(BaseAvatar):
    """리스크 전문 아바타"""
    
    def __init__(self, avatar_id: str, focus: str = 'downside'):
        super().__init__(avatar_id, 'risks')
        self.focus = focus  # upside/downside
    
    def _analyze_logic(self, data: list) -> dict:
        """리스크 분석"""
        
        if not isinstance(data, list):
            return {'risk_level': 'UNKNOWN', 'count': 0, 'error': '잘못된 데이터 형식'}
        
        # 관심 리스크만 필터링
        focused_risks = [
            r for r in data
            if isinstance(r, dict) and r.get('type') == self.focus
        ]
        
        if not focused_risks:
            return {'risk_level': 'LOW', 'count': 0, 'focus': self.focus}
        
        # 고위험 개수
        high_risks = sum(
            1 for r in focused_risks
            if r.get('impact') == 'high'
        )
        
        # 위험 수준
        if high_risks >= 3:
            risk_level = 'HIGH'
        elif high_risks >= 1:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_level': risk_level,
            'count': len(focused_risks),
            'high_count': high_risks,
            'focus': self.focus,
            'risks': focused_risks[:5]  # 최대 5개만 반환
        }

class FinancialAvatar(BaseAvatar):
    """재무 전문 아바타"""
    
    def __init__(self, avatar_id: str):
        super().__init__(avatar_id, 'financial_metrics')
    
    def _analyze_logic(self, data: dict) -> dict:
        """재무 분석"""
        
        if not isinstance(data, dict):
            return {'assessment': 'UNKNOWN', 'error': '잘못된 데이터 형식'}
        
        # 2024 vs 2025 성장률
        metrics_2024 = data.get('2024', {})
        metrics_2025 = data.get('2025', {})
        
        revenue_2024 = metrics_2024.get('revenue', 0) if isinstance(metrics_2024, dict) else 0
        revenue_2025 = metrics_2025.get('revenue', 0) if isinstance(metrics_2025, dict) else 0
        
        if revenue_2024 > 0:
            growth_rate = (revenue_2025 - revenue_2024) / revenue_2024
        else:
            growth_rate = 0
        
        # 평가
        if growth_rate > 0.10:
            assessment = 'STRONG_GROWTH'
        elif growth_rate > 0.05:
            assessment = 'MODERATE_GROWTH'
        elif growth_rate > 0:
            assessment = 'WEAK_GROWTH'
        elif growth_rate == 0:
            assessment = 'STABLE'
        else:
            assessment = 'DECLINING'
        
        return {
            'assessment': assessment,
            'growth_rate': round(growth_rate, 4),
            'revenue_2024': revenue_2024,
            'revenue_2025': revenue_2025
        }

# ============================================================
# Orchestrator
# ============================================================

class ReportAnalysisOrchestrator:
    """보고서 분석 조율기"""
    
    def __init__(self, llm_processor):
        self.extractor = ComprehensiveExtractor(llm_processor)
        self.knowledge_store = KnowledgeStore()
        self.avatars: List[BaseAvatar] = []
        
        self.logger = logging.getLogger(__name__)
    
    def register_avatar(self, avatar: BaseAvatar):
        """아바타 등록"""
        self.avatars.append(avatar)
        self.logger.info(f"아바타 등록: {avatar.avatar_id} ({avatar.specialty})")
    
    def process_report(
        self, 
        report_id: str, 
        report_content: str
    ) -> dict:
        """
        보고서 처리
        
        Returns:
            {
                'report_id': ...,
                'extract_time': ...,
                'avatar_results': [...]
            }
        """
        
        self.logger.info("="*60)
        self.logger.info(f"📄 보고서 처리: {report_id}")
        self.logger.info("="*60)
        
        # 1. 종합 추출 (1번만!)
        self.logger.info("🔍 종합 정보 추출...")
        start = time.time()
        
        extracted = self.extractor.extract(report_content)
        
        extract_time = time.time() - start
        self.logger.info(f"✅ 추출 완료 ({extract_time:.2f}초)")
        
        # 2. 지식 저장
        self.logger.info("💾 지식 저장...")
        
        knowledge = self._create_knowledge(report_id, extracted, report_content)
        self.knowledge_store.store(knowledge)
        
        self.logger.info("✅ 저장 완료")
        
        # 3. 모든 아바타 분석
        if self.avatars:
            self.logger.info(f"🤖 {len(self.avatars)}개 아바타 분석 시작...")
            
            start = time.time()
            avatar_results = []
            
            for avatar in self.avatars:
                result = avatar.analyze(report_id, self.knowledge_store)
                avatar_results.append({
                    'avatar_id': avatar.avatar_id,
                    'specialty': avatar.specialty,
                    'result': result
                })
            
            avatar_time = time.time() - start
            
            self.logger.info(f"✅ 아바타 분석 완료 ({avatar_time:.2f}초)")
            
            # 결과
            total_time = extract_time + avatar_time
            
            self.logger.info("")
            self.logger.info("📊 결과 요약:")
            self.logger.info(f"  추출 시간: {extract_time:.2f}초")
            self.logger.info(f"  아바타 시간: {avatar_time:.2f}초")
            self.logger.info(f"  총 시간: {total_time:.2f}초")
            if len(self.avatars) > 0:
                self.logger.info(f"  아바타당: {avatar_time/len(self.avatars):.4f}초")
            self.logger.info("")
        else:
            avatar_results = []
            avatar_time = 0.0
            total_time = extract_time
            self.logger.info("⚠️  등록된 아바타가 없습니다.")
        
        return {
            'report_id': report_id,
            'extract_time': extract_time,
            'avatar_time': avatar_time,
            'total_time': total_time,
            'avatar_results': avatar_results,
            'knowledge': knowledge
        }
    
    def _create_knowledge(
        self, 
        report_id: str, 
        extracted: dict,
        raw_content: str
    ) -> ReportKnowledge:
        """ReportKnowledge 객체 생성"""
        
        basic = extracted.get('basic', {})
        investment = extracted.get('investment', {})
        
        return ReportKnowledge(
            report_id=report_id,
            timestamp=datetime.now(),
            stock_name=basic.get('stock_name', 'UNKNOWN') if isinstance(basic, dict) else 'UNKNOWN',
            stock_code=basic.get('stock_code', 'UNKNOWN') if isinstance(basic, dict) else 'UNKNOWN',
            analyst=basic.get('analyst', 'UNKNOWN') if isinstance(basic, dict) else 'UNKNOWN',
            firm=basic.get('firm', 'UNKNOWN') if isinstance(basic, dict) else 'UNKNOWN',
            report_date=basic.get('date', '') if isinstance(basic, dict) else '',
            investment_opinion=investment.get('opinion', '') if isinstance(investment, dict) else '',
            target_price=investment.get('target_price') if isinstance(investment, dict) else None,
            expected_return=investment.get('expected_return') if isinstance(investment, dict) else None,
            financial_metrics=extracted.get('financial_metrics', {}),
            trading_signals=extracted.get('trading_signals', {}),
            risks=extracted.get('risks', []),
            sentiment=extracted.get('sentiment', {}),
            events=extracted.get('events', []),
            sector_info=extracted.get('sector_info', {}),
            technical_info=extracted.get('technical_info', {}),
            valuation=extracted.get('valuation', {}),
            raw_content=raw_content
        )

# ============================================================
# Mock LLM (테스트용)
# ============================================================

class MockLLM:
    """Mock LLM 프로세서 (테스트용)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, prompt: str) -> str:
        """프롬프트 처리 (Mock)"""
        
        # 시뮬레이션 지연
        time.sleep(0.1)  # 0.1초 시뮬레이션
        
        # Mock 응답
        return json.dumps({
            "basic": {
                "stock_name": "삼성전자",
                "stock_code": "005930",
                "analyst": "홍길동",
                "firm": "삼성증권",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "investment": {
                "opinion": "buy",
                "target_price": 75000,
                "expected_return": 15.5
            },
            "trading_signals": {
                "short_term": [{"signal": "buy", "confidence": 0.8, "reason": "실적 호조"}],
                "medium_term": [{"signal": "hold", "confidence": 0.7, "reason": "업황 불확실"}],
                "long_term": [{"signal": "buy", "confidence": 0.9, "reason": "장기 성장성"}]
            },
            "risks": [
                {"type": "downside", "description": "메모리 가격 하락", "probability": "medium", "impact": "high"},
                {"type": "upside", "description": "HBM 수요 증가", "probability": "high", "impact": "high"}
            ],
            "financial_metrics": {
                "2024": {"revenue": 250000000000000, "operating_profit": 35000000000000},
                "2025": {"revenue": 270000000000000, "operating_profit": 40000000000000}
            },
            "sentiment": {
                "overall": "bullish",
                "confidence": 85,
                "factors": ["실적 개선", "신규 수주"]
            },
            "events": [
                {"date": "2025-01-15", "event": "실적 발표", "impact": "high"}
            ],
            "sector_info": {
                "industry": "반도체",
                "theme": ["AI", "HBM"],
                "competitors": ["SK하이닉스"]
            },
            "technical_info": {
                "key_technology": ["HBM3E", "GAA"],
                "competitive_advantage": "공정 기술"
            },
            "valuation": {
                "fair_value": 80000,
                "method": "DCF"
            }
        })

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Mock LLM
    llm = MockLLM()
    
    # 오케스트레이터
    orchestrator = ReportAnalysisOrchestrator(llm)
    
    # 아바타 등록
    orchestrator.register_avatar(TradingAvatar("trader_short", "short"))
    orchestrator.register_avatar(TradingAvatar("trader_medium", "medium"))
    orchestrator.register_avatar(TradingAvatar("trader_long", "long"))
    orchestrator.register_avatar(RiskAvatar("risk_downside", "downside"))
    orchestrator.register_avatar(RiskAvatar("risk_upside", "upside"))
    orchestrator.register_avatar(FinancialAvatar("finance_1"))
    
    # 보고서 처리
    report = "삼성전자 4Q24 Preview: 반도체 업황 개선..."
    
    result = orchestrator.process_report("RPT_001", report)
    
    # 결과 출력
    print("\n" + "="*60)
    print("아바타 결과 샘플:")
    print("="*60)
    
    for res in result['avatar_results'][:5]:
        print(f"\n{res['avatar_id']} ({res['specialty']}):")
        print(f"  {res['result']}")

