"""
통합 개선: 검색 결과 데이터 모델
사용자(a) + 시스템(b) + 정보품질(c) 통합
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ================================================================
# 정보 품질 (c): 신뢰도 및 신선도
# ================================================================

class VerificationStatus(Enum):
    """검증 상태"""
    VERIFIED = "verified"           # ✅ 검증됨
    UNVERIFIED = "unverified"       # ⚠️ 미검증
    DISPUTED = "disputed"           # ⚡ 논쟁중
    FALSE = "false"                 # ❌ 거짓
    CHECKING = "checking"           # 🔄 확인중


class DataFreshness(Enum):
    """데이터 신선도"""
    HOT = "hot"                     # 🔥 1시간 이내
    FRESH = "fresh"                 # ✨ 1일 이내
    NORMAL = "normal"               # 📅 1주 이내
    OLD = "old"                     # 🗄️ 1주 초과


class SourceTier(Enum):
    """소스 등급"""
    TIER_1 = 1  # 공식 (거래소, 금감원)
    TIER_2 = 2  # 언론 (연합뉴스, 한경)
    TIER_3 = 3  # 커뮤니티 (토론방, SNS)


@dataclass
class CredibilityScore:
    """신뢰도 점수 (정보 품질 c)"""
    overall: float  # 0.0 ~ 1.0
    source_tier_score: float
    cross_verify_score: float
    past_accuracy: float
    llm_confidence: float
    
    verification_status: VerificationStatus
    
    # 근거
    supporting_sources: List[str] = field(default_factory=list)
    contradicting_sources: List[str] = field(default_factory=list)
    
    def get_display_text(self) -> str:
        """사용자용 표시 텍스트 (사용자 관점 a)"""
        if self.overall >= 0.90:
            return f"✅ 매우 높음 ({int(self.overall*100)}%)"
        elif self.overall >= 0.75:
            return f"✅ 높음 ({int(self.overall*100)}%)"
        elif self.overall >= 0.60:
            return f"⚠️ 보통 ({int(self.overall*100)}%)"
        elif self.overall >= 0.40:
            return f"⚡ 낮음 ({int(self.overall*100)}%)"
        else:
            return f"❌ 매우 낮음 ({int(self.overall*100)}%)"


@dataclass
class TimeInfo:
    """시간 정보 (정보 품질 c)"""
    published_at: datetime
    collected_at: datetime
    
    @property
    def freshness(self) -> DataFreshness:
        """신선도 계산"""
        delta = datetime.now() - self.published_at
        
        if delta.total_seconds() < 3600:  # 1시간
            return DataFreshness.HOT
        elif delta.days < 1:
            return DataFreshness.FRESH
        elif delta.days < 7:
            return DataFreshness.NORMAL
        else:
            return DataFreshness.OLD
    
    @property
    def time_ago(self) -> str:
        """'N분 전' 형식 (사용자 관점 a)"""
        delta = datetime.now() - self.published_at
        
        if delta.total_seconds() < 60:
            return "방금 전"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}분 전"
        elif delta.days < 1:
            return f"{int(delta.total_seconds() / 3600)}시간 전"
        elif delta.days < 7:
            return f"{delta.days}일 전"
        else:
            return self.published_at.strftime("%Y-%m-%d")


# ================================================================
# 사용자 관점 (a): 액션 가능한 정보
# ================================================================

@dataclass
class ActionButton:
    """액션 버튼 (사용자 관점 a)"""
    label: str
    action: str
    icon: str
    style: str = "primary"  # primary, secondary, danger
    
    def to_dict(self) -> Dict:
        return {
            'label': self.label,
            'action': self.action,
            'icon': self.icon,
            'style': self.style
        }


@dataclass
class AIInsight:
    """AI 인사이트 (사용자 관점 a)"""
    recommendation: str  # "강력 매수", "매수", "보유", "매도", "강력 매도"
    confidence: float  # 0.0 ~ 1.0
    
    reasoning: List[str]  # 근거
    risks: List[str]  # 리스크
    
    key_points: List[str]  # 핵심 포인트 (3줄 요약)
    
    def get_emoji(self) -> str:
        """추천에 맞는 이모지"""
        mapping = {
            "강력 매수": "🚀",
            "매수": "📈",
            "보유": "📊",
            "매도": "📉",
            "강력 매도": "⚠️"
        }
        return mapping.get(self.recommendation, "📊")


@dataclass
class RelatedStock:
    """관련 종목 정보 (사용자 관점 a)"""
    code: str
    name: str
    current_price: float
    change_rate: float
    volume_ratio: float  # 평소 대비 거래량 비율
    
    def get_status_emoji(self) -> str:
        """상태 이모지"""
        if self.change_rate >= 3.0:
            return "🔥"
        elif self.change_rate >= 1.0:
            return "📈"
        elif self.change_rate <= -3.0:
            return "❄️"
        elif self.change_rate <= -1.0:
            return "📉"
        else:
            return "➡️"


# ================================================================
# 시스템 관점 (b): 성능 및 상태 모니터링
# ================================================================

@dataclass
class SystemMetrics:
    """시스템 메트릭 (시스템 관점 b)"""
    search_time_ms: int
    total_sources_checked: int
    cache_hit: bool
    data_freshness_minutes: int
    
    crawl_status: Dict[str, str]  # {source: status}
    
    def get_status_summary(self) -> str:
        """상태 요약"""
        active = sum(1 for s in self.crawl_status.values() if s == "정상")
        total = len(self.crawl_status)
        
        if active == total:
            return f"✅ 모든 소스 정상 ({total}개)"
        else:
            return f"⚠️ 일부 소스 지연 ({active}/{total}개)"


@dataclass
class ErrorInfo:
    """오류 정보 (시스템 관점 b)"""
    has_error: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def get_user_message(self) -> str:
        """사용자용 오류 메시지"""
        if not self.has_error:
            return ""
        
        messages = {
            "NO_DATA": "검색 결과가 없습니다. 다른 키워드를 시도해보세요.",
            "TIMEOUT": "응답 시간 초과. 잠시 후 다시 시도해주세요.",
            "CRAWL_FAILED": "일부 데이터 수집 실패. 부분 결과만 표시됩니다.",
        }
        
        return messages.get(self.error_type, "알 수 없는 오류가 발생했습니다.")


# ================================================================
# 통합 검색 결과 항목
# ================================================================

@dataclass
class SearchResultItem:
    """검색 결과 단일 항목"""
    
    # 기본 정보
    title: str
    content: str
    summary: str
    url: str
    
    # 분류
    item_type: str  # report, news, stock, disclosure, community
    source: str
    source_tier: SourceTier
    
    # 시간 정보 (c)
    time_info: TimeInfo
    
    # 신뢰도 (c)
    credibility: CredibilityScore
    
    # 관련 정보
    stock_codes: List[str] = field(default_factory=list)
    related_stocks: List[RelatedStock] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # 메타데이터
    relevance_score: float = 1.0  # 검색어 관련도
    urgency_level: int = 1  # 1~5
    sentiment: str = "neutral"  # positive, negative, neutral
    
    def get_freshness_badge(self) -> str:
        """신선도 뱃지 (사용자 관점 a)"""
        badges = {
            DataFreshness.HOT: "🔥 신규",
            DataFreshness.FRESH: "✨ 최신",
            DataFreshness.NORMAL: "📅 일반",
            DataFreshness.OLD: "🗄️ 과거"
        }
        return badges[self.time_info.freshness]
    
    def get_type_icon(self) -> str:
        """타입별 아이콘"""
        icons = {
            'report': '📊',
            'news': '📰',
            'stock': '📈',
            'disclosure': '📋',
            'community': '💬'
        }
        return icons.get(self.item_type, '📄')
    
    def to_display_dict(self) -> Dict:
        """화면 표시용 딕셔너리 (사용자 관점 a)"""
        return {
            'icon': self.get_type_icon(),
            'title': self.title,
            'summary': self.summary[:100] + '...' if len(self.summary) > 100 else self.summary,
            'source': self.source,
            'time_ago': self.time_info.time_ago,
            'freshness_badge': self.get_freshness_badge(),
            'credibility': self.credibility.get_display_text(),
            'verification_status': self.credibility.verification_status.value,
            'url': self.url,
            'stock_codes': self.stock_codes,
            'urgency_level': self.urgency_level
        }


# ================================================================
# 통합 검색 결과 컨테이너
# ================================================================

@dataclass
class EnhancedSearchResult:
    """개선된 검색 결과 (a + b + c 통합)"""
    
    query: str
    
    # 결과 항목들
    items: List[SearchResultItem]
    
    # AI 인사이트 (사용자 관점 a)
    ai_insight: Optional[AIInsight] = None
    
    # 시스템 메트릭 (시스템 관점 b)
    metrics: Optional[SystemMetrics] = None
    
    # 오류 정보 (시스템 관점 b)
    error: ErrorInfo = field(default_factory=lambda: ErrorInfo(has_error=False))
    
    # 액션 버튼들 (사용자 관점 a)
    action_buttons: List[ActionButton] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        return len(self.items)
    
    @property
    def by_type(self) -> Dict[str, int]:
        """타입별 카운트"""
        from collections import Counter
        return dict(Counter(item.item_type for item in self.items))
    
    @property
    def urgent_count(self) -> int:
        """긴급 항목 수"""
        return sum(1 for item in self.items if item.urgency_level >= 4)
    
    def get_summary(self) -> Dict:
        """전체 요약 (사용자 관점 a)"""
        return {
            'query': self.query,
            'total': self.total_count,
            'by_type': self.by_type,
            'urgent': self.urgent_count,
            'has_ai_insight': self.ai_insight is not None,
            'search_time': f"{self.metrics.search_time_ms}ms" if self.metrics else "N/A",
            'data_status': self.metrics.get_status_summary() if self.metrics else "N/A"
        }
    
    def to_json(self) -> Dict:
        """JSON 직렬화"""
        return {
            'query': self.query,
            'summary': self.get_summary(),
            'items': [item.to_display_dict() for item in self.items],
            'ai_insight': {
                'recommendation': self.ai_insight.recommendation,
                'emoji': self.ai_insight.get_emoji(),
                'confidence': self.ai_insight.confidence,
                'key_points': self.ai_insight.key_points,
                'reasoning': self.ai_insight.reasoning,
                'risks': self.ai_insight.risks
            } if self.ai_insight else None,
            'metrics': {
                'search_time_ms': self.metrics.search_time_ms,
                'cache_hit': self.metrics.cache_hit,
                'status': self.metrics.get_status_summary()
            } if self.metrics else None,
            'actions': [btn.to_dict() for btn in self.action_buttons],
            'error': {
                'has_error': self.error.has_error,
                'message': self.error.get_user_message()
            } if self.error.has_error else None
        }



