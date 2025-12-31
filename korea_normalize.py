"""
Korea Analyst Report Normalizer
한국 애널리스트 리포트 정규화

지원 소스:
- 38커뮤니케이션 (38com)
- 한경 컨센서스 (hankyung)
- 네이버 금융 (naver)

계약:
- 입력: raw_data (Dict, 크롤러 원본 데이터)
- 출력: KoreaAnalystSnapshot v1 형식 (Dict)
- 예외: ValueError (필수 필드 누락)
"""

from typing import Any, Dict, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def safe_int(value: Any, default: int = 0) -> int:
    """
    안전한 정수 변환
    
    Args:
        value: 변환할 값
        default: 기본값 (변환 실패 시)
        
    Returns:
        int: 변환된 정수값
    """
    try:
        if value is None or value == '':
            return default
        # 문자열에서 쉼표, 원화 기호 제거
        cleaned = str(value).replace(',', '').replace('원', '').strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any) -> Optional[float]:
    """
    안전한 실수 변환
    
    Args:
        value: 변환할 값
        
    Returns:
        Optional[float]: 변환된 실수값 (실패 시 None)
    """
    try:
        if value is None or value == '':
            return None
        cleaned = str(value).replace(',', '').replace('원', '').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def today_yyyy_mm_dd() -> str:
    """오늘 날짜 YYYY-MM-DD 형식"""
    return date.today().isoformat()


def normalize_opinion(opinion_text: Optional[str]) -> str:
    """
    한국 증권사 의견을 표준 형식으로 변환
    
    매핑:
    - 매수(강력), 적극 매수, StrongBuy → Strong Buy
    - 매수, Buy → Buy
    - 중립, 보유, 시장수익률, Hold, Neutral → Hold
    - 매도, Sell → Sell
    - 매도(강력), 비중축소, StrongSell → Strong Sell
    
    Args:
        opinion_text: 원본 의견 텍스트
        
    Returns:
        str: 정규화된 의견 ('Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell')
    """
    if not opinion_text:
        return 'Hold'
    
    opinion_lower = str(opinion_text).lower().strip()
    
    # Strong Buy 패턴
    if any(keyword in opinion_lower for keyword in [
        '매수(강력)', '적극 매수', '강력 매수', 'strongbuy', 'strong buy'
    ]):
        return 'Strong Buy'
    
    # Buy 패턴
    if any(keyword in opinion_lower for keyword in [
        '매수', 'buy', '비중확대'
    ]):
        return 'Buy'
    
    # Sell 패턴
    if any(keyword in opinion_lower for keyword in [
        '매도', 'sell', '비중축소'
    ]) and '강력' not in opinion_lower:
        return 'Sell'
    
    # Strong Sell 패턴
    if any(keyword in opinion_lower for keyword in [
        '매도(강력)', '강력 매도', 'strongsell', 'strong sell'
    ]):
        return 'Strong Sell'
    
    # 기본값: Hold
    return 'Hold'


def normalize_from_38com(
    raw_data: Dict[str, Any],
    currency: str = 'KRW'
) -> Dict[str, Any]:
    """
    38커뮤니케이션 리포트 → KoreaAnalystSnapshot v1
    
    Args:
        raw_data: 38커뮤니케이션 크롤러 원본 데이터
            {
                'stock_code': '005930',
                'stock_name': '삼성전자',
                'published_date': datetime 또는 '2025-12-31',
                'analyst_name': '홍길동',
                'analyst_firm': 'KB증권',
                'investment_opinion': '매수',
                'target_price': 95000,
                'current_price': 85000,
                'source_url': 'https://...',
                'pdf_url': 'https://...'
            }
        currency: 통화 (기본값: 'KRW')
        
    Returns:
        Dict: KoreaAnalystSnapshot v1 형식
        
    Raises:
        ValueError: 필수 필드 누락
    """
    # 기본 정보 추출
    stock_code = str(raw_data.get('stock_code', '')).strip()
    stock_name = str(raw_data.get('stock_name', '')).strip()
    
    # 날짜 처리
    published_date = raw_data.get('published_date')
    if isinstance(published_date, datetime):
        report_date = published_date.strftime('%Y-%m-%d')
    elif isinstance(published_date, str):
        report_date = published_date
    else:
        report_date = today_yyyy_mm_dd()
    
    # 필수 필드 검증
    if not stock_code or len(stock_code) != 6:
        raise ValueError(f"Invalid stock_code: {stock_code}")
    
    # 의견 정규화
    opinion_raw = raw_data.get('investment_opinion') or raw_data.get('opinion', 'Hold')
    opinion_normalized = normalize_opinion(opinion_raw)
    
    # 목표주가
    target_price = safe_int(raw_data.get('target_price'))
    current_price = safe_int(raw_data.get('current_price'))
    
    # 애널리스트 정보
    analyst_name = raw_data.get('analyst_name')
    analyst_firm = raw_data.get('analyst_firm') or raw_data.get('firm')
    
    # 추천 분포 (단일 리포트이므로 1개만 카운트)
    recommendation = {
        'strong_buy': 1 if opinion_normalized == 'Strong Buy' else 0,
        'buy': 1 if opinion_normalized == 'Buy' else 0,
        'hold': 1 if opinion_normalized == 'Hold' else 0,
        'sell': 1 if opinion_normalized == 'Sell' else 0,
        'strong_sell': 1 if opinion_normalized == 'Strong Sell' else 0,
        'rating_text': opinion_normalized,
        'analyst_count': 1
    }
    
    # 목표주가 정보
    price_target = {
        'low': target_price if target_price > 0 else None,
        'mean': target_price if target_price > 0 else None,
        'high': target_price if target_price > 0 else None,
        'median': target_price if target_price > 0 else None,
        'currency': currency,
        'horizon_months': 12
    }
    
    # 가치평가 (현재가 기준)
    valuation = {
        'fair_value': target_price if target_price > 0 else None,
        'price_to_fair_value': None
    }
    
    if current_price and target_price:
        try:
            valuation['price_to_fair_value'] = current_price / target_price
        except ZeroDivisionError:
            pass
    
    # 신뢰도 (38커뮤니케이션 기본 신뢰도: 0.80)
    confidence = {
        'source_quality': 0.80,
        'freshness_days': 0,  # 발행 당일 기준
        'coverage_score': 0.05  # 단일 리포트 = 5% (20개 = 100%)
    }
    
    # 원본 참조
    raw_refs = {
        'source_url': raw_data.get('source_url') or raw_data.get('report_url'),
        'pdf_url': raw_data.get('pdf_url'),
        'report_id': raw_data.get('report_id'),
        'raw_payload': raw_data
    }
    
    # 스냅샷 생성
    snapshot = {
        'version': 'v1',
        'asof': report_date,
        'stock_code': stock_code,
        'stock_name': stock_name,
        'market': raw_data.get('market'),
        'source': '38com',
        'recommendation': recommendation,
        'price_target': price_target,
        'valuation': valuation,
        'confidence': confidence,
        'raw_refs': raw_refs
    }
    
    # 애널리스트 정보 추가
    if analyst_name or analyst_firm:
        snapshot['analyst_info'] = {
            'name': analyst_name,
            'firm': analyst_firm,
            'track_record': None
        }
    
    return snapshot


def normalize_from_hankyung(
    raw_data: Dict[str, Any],
    currency: str = 'KRW'
) -> Dict[str, Any]:
    """
    한경 컨센서스 리포트 → KoreaAnalystSnapshot v1
    
    Args:
        raw_data: 한경 컨센서스 크롤러 원본 데이터
            - 단일 리포트: 38com과 동일 형식
            - 다중 리포트: 'reports' 리스트 포함
        currency: 통화 (기본값: 'KRW')
        
    Returns:
        Dict: KoreaAnalystSnapshot v1 형식
        
    Raises:
        ValueError: 필수 필드 누락
    """
    stock_code = str(raw_data.get('stock_code', '')).strip()
    stock_name = str(raw_data.get('stock_name', '')).strip()
    
    # 날짜 처리
    published_date = raw_data.get('published_date')
    if isinstance(published_date, datetime):
        report_date = published_date.strftime('%Y-%m-%d')
    elif isinstance(published_date, str):
        report_date = published_date
    else:
        report_date = today_yyyy_mm_dd()
    
    # 필수 필드 검증
    if not stock_code or len(stock_code) != 6:
        raise ValueError(f"Invalid stock_code: {stock_code}")
    
    reports = raw_data.get('reports', [])
    
    if not reports:
        # 단일 리포트로 처리
        return normalize_from_38com(raw_data, currency)
    
    # 여러 리포트 집계
    opinion_counts = {
        'strong_buy': 0,
        'buy': 0,
        'hold': 0,
        'sell': 0,
        'strong_sell': 0
    }
    
    target_prices = []
    
    for report in reports:
        # 의견 집계
        opinion_raw = report.get('investment_opinion') or report.get('opinion', 'Hold')
        opinion_normalized = normalize_opinion(opinion_raw)
        
        opinion_key = opinion_normalized.lower().replace(' ', '_')
        if opinion_key in opinion_counts:
            opinion_counts[opinion_key] += 1
        
        # 목표주가 수집
        target = safe_int(report.get('target_price'))
        if target > 0:
            target_prices.append(target)
    
    # 컨센서스 의견 결정
    total_analysts = sum(opinion_counts.values())
    
    if total_analysts > 0:
        # 가중 평균 계산
        score = (
            2 * opinion_counts['strong_buy'] +
            1 * opinion_counts['buy'] +
            0 * opinion_counts['hold'] -
            1 * opinion_counts['sell'] -
            2 * opinion_counts['strong_sell']
        ) / total_analysts
        
        if score >= 1.2:
            rating_text = 'Strong Buy'
        elif score >= 0.4:
            rating_text = 'Buy'
        elif score > -0.4:
            rating_text = 'Hold'
        elif score > -1.2:
            rating_text = 'Sell'
        else:
            rating_text = 'Strong Sell'
    else:
        rating_text = 'Hold'
    
    # 추천 분포
    recommendation = {
        **opinion_counts,
        'rating_text': rating_text,
        'analyst_count': total_analysts
    }
    
    # 목표주가 통계
    price_target = {
        'low': min(target_prices) if target_prices else None,
        'mean': sum(target_prices) / len(target_prices) if target_prices else None,
        'high': max(target_prices) if target_prices else None,
        'median': sorted(target_prices)[len(target_prices) // 2] if target_prices else None,
        'currency': currency,
        'horizon_months': 12
    }
    
    # 신뢰도 (한경 컨센서스: 0.85)
    confidence = {
        'source_quality': 0.85,
        'freshness_days': 0,
        'coverage_score': min(1.0, total_analysts / 20.0)  # 20개 = 100%
    }
    
    # 스냅샷 생성
    snapshot = {
        'version': 'v1',
        'asof': report_date,
        'stock_code': stock_code,
        'stock_name': stock_name,
        'market': raw_data.get('market'),
        'source': 'hankyung',
        'recommendation': recommendation,
        'price_target': price_target,
        'valuation': {
            'fair_value': price_target['mean'],
            'price_to_fair_value': None
        },
        'confidence': confidence,
        'raw_refs': {
            'source_url': raw_data.get('source_url'),
            'pdf_url': None,
            'report_id': raw_data.get('report_id'),
            'raw_payload': raw_data
        }
    }
    
    return snapshot


def normalize_from_naver(
    raw_data: Dict[str, Any],
    currency: str = 'KRW'
) -> Dict[str, Any]:
    """
    네이버 금융 리서치 → KoreaAnalystSnapshot v1
    
    Args:
        raw_data: 네이버 금융 크롤러 원본 데이터
            - ReportMetadata.to_dict() 형식
        currency: 통화 (기본값: 'KRW')
        
    Returns:
        Dict: KoreaAnalystSnapshot v1 형식
        
    Raises:
        ValueError: 필수 필드 누락
    """
    # 네이버는 단일 리포트 형식이므로 38com과 유사하게 처리
    # 다만 source를 'naver'로 설정하고 신뢰도를 조정
    
    # 날짜 처리
    published_date = raw_data.get('published_date')
    if isinstance(published_date, str):
        # ISO 형식 문자열 파싱
        try:
            dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            report_date = dt.strftime('%Y-%m-%d')
        except:
            report_date = today_yyyy_mm_dd()
    elif isinstance(published_date, datetime):
        report_date = published_date.strftime('%Y-%m-%d')
    else:
        report_date = today_yyyy_mm_dd()
    
    # 38com 정규화 함수 재사용
    snapshot = normalize_from_38com(raw_data, currency)
    
    # 네이버 특화 설정
    snapshot['source'] = 'naver'
    snapshot['confidence']['source_quality'] = 0.75  # 네이버는 조금 낮게
    
    # 날짜 업데이트
    snapshot['asof'] = report_date
    
    return snapshot


def normalize_report_metadata(
    report: Any,
    source: str = 'auto'
) -> Dict[str, Any]:
    """
    ReportMetadata 객체 또는 dict를 정규화
    
    Args:
        report: ReportMetadata 객체 또는 dict
        source: 소스 타입 ('auto', '38com', 'hankyung', 'naver')
            'auto'이면 report의 source 필드로 자동 판단
        
    Returns:
        Dict: KoreaAnalystSnapshot v1 형식
        
    Raises:
        ValueError: 알 수 없는 소스 또는 필수 필드 누락
    """
    # dict로 변환
    if hasattr(report, 'to_dict'):
        raw_data = report.to_dict()
    elif isinstance(report, dict):
        raw_data = report
    else:
        raise ValueError(f"Unsupported report type: {type(report)}")
    
    # 소스 자동 판단
    if source == 'auto':
        source = raw_data.get('source', '').lower()
        if 'naver' in source or 'NaverFinance' in source:
            source = 'naver'
        elif 'hankyung' in source or 'HankyungConsensus' in source:
            source = 'hankyung'
        elif '38com' in source or '38' in source:
            source = '38com'
        else:
            # 기본값: naver (가장 많이 사용)
            source = 'naver'
    
    # 소스별 정규화
    if source == 'naver':
        return normalize_from_naver(raw_data)
    elif source == 'hankyung':
        return normalize_from_hankyung(raw_data)
    elif source == '38com':
        return normalize_from_38com(raw_data)
    else:
        raise ValueError(f"Unknown source: {source}")


if __name__ == '__main__':
    # 테스트: 38커뮤니케이션 단일 리포트
    test_38com = {
        'stock_code': '005930',
        'stock_name': '삼성전자',
        'published_date': '2025-12-31',
        'analyst_name': '홍길동',
        'analyst_firm': 'KB증권',
        'investment_opinion': '매수',
        'target_price': 95000,
        'current_price': 85000,
        'source_url': 'https://www.38.co.kr/example/12345',
        'pdf_url': 'https://www.38.co.kr/pdf/12345.pdf'
    }
    
    snapshot_38 = normalize_from_38com(test_38com)
    print("=" * 60)
    print("38커뮤니케이션 단일 리포트 정규화 결과:")
    print("=" * 60)
    print(f"종목: {snapshot_38['stock_name']} ({snapshot_38['stock_code']})")
    print(f"의견: {snapshot_38['recommendation']['rating_text']}")
    print(f"목표가: {snapshot_38['price_target']['mean']:,} 원")
    print(f"신뢰도: {snapshot_38['confidence']['source_quality']}")
    
    # 테스트: 한경 컨센서스 (다중 리포트)
    test_hankyung = {
        'stock_code': '000660',
        'stock_name': 'SK하이닉스',
        'published_date': '2025-12-31',
        'reports': [
            {'analyst_name': '김철수', 'analyst_firm': 'NH투자증권', 'opinion': '매수', 'target_price': 180000},
            {'analyst_name': '박영희', 'analyst_firm': '미래에셋증권', 'opinion': '매수(강력)', 'target_price': 200000},
            {'analyst_name': '이민수', 'analyst_firm': '삼성증권', 'opinion': '매수', 'target_price': 190000},
            {'analyst_name': '정수진', 'analyst_firm': '키움증권', 'opinion': '중립', 'target_price': 170000},
        ],
        'source_url': 'https://consensus.hankyung.com/000660'
    }
    
    snapshot_hk = normalize_from_hankyung(test_hankyung)
    print("\n" + "=" * 60)
    print("한경 컨센서스 정규화 결과:")
    print("=" * 60)
    print(f"종목: {snapshot_hk['stock_name']} ({snapshot_hk['stock_code']})")
    print(f"컨센서스: {snapshot_hk['recommendation']['rating_text']}")
    print(f"애널리스트 수: {snapshot_hk['recommendation']['analyst_count']}")
    print(f"목표가 평균: {snapshot_hk['price_target']['mean']:,.0f} 원")
    print(f"목표가 범위: {snapshot_hk['price_target']['low']:,.0f} ~ {snapshot_hk['price_target']['high']:,.0f} 원")
    print(f"의견 분포:")
    print(f"  - 매수(강력): {snapshot_hk['recommendation']['strong_buy']}")
    print(f"  - 매수: {snapshot_hk['recommendation']['buy']}")
    print(f"  - 중립: {snapshot_hk['recommendation']['hold']}")
    print(f"  - 매도: {snapshot_hk['recommendation']['sell']}")


