# crawler_hankyung_consensus.py
"""
한경 컨센서스 크롤러

한경코리아마켓 컨센서스 리포트 수집
https://markets.hankyung.com/consensus

계약:
- 입력: days (int, 최근 N일), max_reports (int, 최대 수집 개수)
- 출력: List[ReportMetadata] (보고서 메타데이터 리스트)
- 예외: requests.RequestException (네트워크 오류), ValueError (잘못된 파라미터)
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import hashlib
from urllib.parse import urljoin, urlparse, urlencode
import urllib3
import re

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 대응형 크롤러 임포트
try:
    from adaptive_crawler import AdaptiveCrawler, SiteProfile
    ADAPTIVE_CRAWLER_AVAILABLE = True
except ImportError:
    ADAPTIVE_CRAWLER_AVAILABLE = False

@dataclass
class ReportMetadata:
    """보고서 메타데이터"""
    report_id: str
    title: str
    stock_code: str
    stock_name: str
    analyst_name: str
    firm: str
    published_date: datetime
    source_url: str
    
    # 추가 정보 (있으면)
    investment_opinion: Optional[str] = None
    target_price: Optional[str] = None
    current_price: Optional[str] = None
    consensus_rating: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        # datetime을 문자열로 변환
        data['published_date'] = self.published_date.isoformat()
        return data

class HankyungConsensusCrawler:
    """
    한경 컨센서스 크롤러
    
    사용법:
        crawler = HankyungConsensusCrawler()
        reports = crawler.crawl_recent_reports(days=1)
        
        # 특정 종목 검색
        reports = crawler.search_by_stock("삼성전자", days=7)
        
        # 필터링 옵션
        reports = crawler.crawl_recent_reports(
            days=7,
            report_type="stock",  # stock, industry, market, analyst
            firm_filter=None  # 특정 증권사 필터
        )
    """
    
    BASE_URL = "https://markets.hankyung.com"
    CONSENSUS_URL = "https://markets.hankyung.com/consensus"
    
    # 리포트 유형
    REPORT_TYPE_STOCK = "stock"  # 종목 리포트
    REPORT_TYPE_INDUSTRY = "industry"  # 산업 리포트
    REPORT_TYPE_MARKET = "market"  # 시황/전략 리포트
    REPORT_TYPE_ANALYST = "analyst"  # 애널리스트 코멘트
    
    def __init__(self, delay: float = 3.0, max_retries: int = 3, retry_delay: float = 5.0,
                 use_adaptive: bool = True, site_domain: str = "markets.hankyung.com"):
        """
        초기화
        
        Args:
            delay: 요청 간 대기 시간 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 대기 시간 (초)
            use_adaptive: 대응형 크롤러 사용 여부
            site_domain: 사이트 도메인
        """
        self.delay = delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_adaptive = use_adaptive and ADAPTIVE_CRAWLER_AVAILABLE
        self.site_domain = site_domain
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 대응형 크롤러 초기화
        if self.use_adaptive:
            profile = SiteProfile(
                domain=site_domain,
                base_delay=delay,
                max_retries=max_retries
            )
            self.adaptive_crawler = AdaptiveCrawler(profile)
            self.session = self.adaptive_crawler.session
            self.logger.info("대응형 크롤러 활성화")
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://markets.hankyung.com/',
            })
            self.adaptive_crawler = None
    
    def crawl_recent_reports(
        self, 
        days: int = 1,
        max_reports: int = 100,
        report_type: str = "stock",
        firm_filter: Optional[str] = None
    ) -> List[ReportMetadata]:
        """
        최근 보고서 크롤링
        
        Args:
            days: 최근 N일 (기본값: 1)
            max_reports: 최대 수집 개수 (기본값: 100)
            report_type: 리포트 유형 (기본값: "stock")
                - "stock": 종목 리포트
                - "industry": 산업 리포트
                - "market": 시황/전략 리포트
                - "analyst": 애널리스트 코멘트
            firm_filter: 증권사 필터 (None이면 전체, 기본값: None)
            
        Returns:
            List[ReportMetadata]: 보고서 메타데이터 리스트
            
        Raises:
            ValueError: 잘못된 report_type 또는 days < 0
            requests.RequestException: 네트워크 오류 또는 페이지 조회 실패
            
        계약:
        - 입력: days는 양수, report_type은 유효한 값
        - 출력: ReportMetadata 리스트 (빈 리스트 가능)
        - 예외: ValueError (잘못된 파라미터), RequestException (네트워크 오류)
        """
        
        # 입력 검증
        if days < 0:
            raise ValueError(f"days must be non-negative, got {days}")
        if max_reports < 0:
            raise ValueError(f"max_reports must be non-negative, got {max_reports}")
        if report_type not in [self.REPORT_TYPE_STOCK, self.REPORT_TYPE_INDUSTRY, 
                               self.REPORT_TYPE_MARKET, self.REPORT_TYPE_ANALYST]:
            raise ValueError(f"Invalid report_type: {report_type}")
        
        self.logger.info(f"📊 한경 컨센서스 크롤링 시작: 최근 {days}일, 유형={report_type}")
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # 1. 종목 리포트 탭으로 이동 (기본값)
            if report_type == "stock":
                # 종목 리포트 페이지 URL 구성
                # 실제 API나 페이지 구조에 맞춰 조정 필요
                list_url = f"{self.CONSENSUS_URL}?type=stock"
            else:
                list_url = f"{self.CONSENSUS_URL}?type={report_type}"
            
            self.logger.info(f"🔍 목록 조회: {list_url}")
            html = self._fetch(list_url)
            
            if not html:
                # 기본 URL로 재시도
                self.logger.warning("필터 URL 실패, 기본 URL로 재시도")
                html = self._fetch(self.CONSENSUS_URL)
            
            if not html:
                self.logger.error("목록 페이지 조회 실패")
                return []
            
            # 2. 보고서 메타데이터 추출 (개선된 방식)
            report_list = self._extract_report_list(html, report_type=report_type)
            
            self.logger.info(f"📋 발견된 보고서: {len(report_list)}개")
            
            # 3. 각 보고서 처리
            total_reports = min(len(report_list), max_reports)
            
            for i, report_data in enumerate(report_list[:max_reports], 1):
                progress = f"[{i}/{total_reports}]"
                url = report_data.get('url')
                if not url:
                    continue
                
                try:
                    # 날짜 확인
                    report_date = report_data.get('date')
                    if isinstance(report_date, str):
                        report_date = self._parse_date_from_text(report_date)
                    elif not isinstance(report_date, datetime):
                        report_date = datetime.now()
                    
                    if report_date < cutoff_date:
                        self.logger.info(f"{progress} ⏭️  오래된 보고서 (날짜: {report_date.strftime('%Y-%m-%d')})")
                        if i > 10:  # 최소 10개는 확인
                            break
                        continue
                    
                    # 증권사 필터링
                    if firm_filter and report_data.get('firm'):
                        if firm_filter not in report_data.get('firm', ''):
                            self.logger.info(f"{progress} ⏭️  증권사 필터 불일치: {report_data.get('firm')}")
                            continue
                    
                    # 목록 페이지에서 충분한 정보가 있으면 바로 사용
                    if report_data.get('firm') and report_data.get('firm') != 'UNKNOWN':
                        report = ReportMetadata(
                            report_id=self._generate_report_id(url, report_data.get('title', '')),
                            title=report_data.get('title', '리포트'),
                            stock_code=report_data.get('stock_code', 'UNKNOWN'),
                            stock_name=report_data.get('stock_name', 'UNKNOWN'),
                            analyst_name=report_data.get('analyst_name', 'UNKNOWN'),
                            firm=report_data.get('firm', 'UNKNOWN'),
                            published_date=report_date,
                            source_url=url,
                            investment_opinion=report_data.get('opinion'),
                            target_price=report_data.get('target_price'),
                            current_price=None,
                            consensus_rating=None
                        )
                        reports.append(report)
                        self.logger.info(
                            f"{progress} ✅ 수집: {report.stock_name} - {report.analyst_name} ({report.firm}) "
                            f"- {report.investment_opinion or 'N/A'} - 목표가: {report.target_price or 'N/A'}"
                        )
                    else:
                        # 상세 페이지 방문 필요
                        self.logger.info(f"{progress} 처리 중: {url[:80]}...")
                        report = self._crawl_report_detail(url)
                        
                        if report:
                            # 증권사 필터링
                            if firm_filter and firm_filter not in report.firm:
                                self.logger.info(f"{progress} ⏭️  증권사 필터 불일치: {report.firm}")
                                continue
                            
                            reports.append(report)
                            self.logger.info(
                                f"{progress} ✅ 수집: {report.stock_name} - {report.analyst_name} ({report.firm})"
                            )
                        else:
                            self.logger.warning(f"{progress} ❌ 추출 실패")
                    
                    # 예의바른 대기
                    if i < total_reports:
                        time.sleep(self.delay)
                
                except Exception as e:
                    self.logger.error(f"{progress} 처리 실패: {e}")
                    continue
            
            self.logger.info(f"🎉 크롤링 완료: {len(reports)}개 수집")
            
        except Exception as e:
            self.logger.error(f"크롤링 오류: {e}", exc_info=True)
        
        return reports
    
    def search_by_stock(
        self,
        stock_name: str,
        days: int = 7,
        max_reports: int = 50
    ) -> List[ReportMetadata]:
        """
        특정 종목으로 리포트 검색
        
        Args:
            stock_name: 종목명 (예: "삼성전자")
            days: 최근 N일 (기본값: 7)
            max_reports: 최대 수집 개수 (기본값: 50)
            
        Returns:
            List[ReportMetadata]: 보고서 메타데이터 리스트
            
        Raises:
            ValueError: 잘못된 stock_name 또는 days < 0
            requests.RequestException: 네트워크 오류 또는 페이지 조회 실패
            
        계약:
        - 입력: stock_name은 비어있지 않은 문자열, days는 양수
        - 출력: ReportMetadata 리스트 (빈 리스트 가능)
        - 예외: ValueError (잘못된 파라미터), RequestException (네트워크 오류)
        """
        
        # 입력 검증
        if not stock_name or not isinstance(stock_name, str):
            raise ValueError(f"stock_name must be a non-empty string, got {stock_name}")
        if days < 0:
            raise ValueError(f"days must be non-negative, got {days}")
        if max_reports < 0:
            raise ValueError(f"max_reports must be non-negative, got {max_reports}")
        
        self.logger.info(f"🔍 종목 검색: {stock_name} (최근 {days}일)")
        
        # 종목 리포트 탭으로 이동 후 검색
        # 실제 API 엔드포인트나 검색 파라미터에 맞춰 조정 필요
        search_url = f"{self.CONSENSUS_URL}?type=stock&search={stock_name}"
        
        html = self._fetch(search_url)
        
        if not html:
            self.logger.error(f"종목 검색 실패: {stock_name}")
            return []
        
        # 검색 결과에서 리포트 메타데이터 추출 (개선된 방식)
        report_list = self._extract_report_list(html, report_type="stock")
        
        self.logger.info(f"📋 발견된 리포트: {len(report_list)}개")
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for i, report_data in enumerate(report_list[:max_reports], 1):
            try:
                # 목록 페이지에서 추출한 메타데이터 활용
                url = report_data.get('url')
                if not url:
                    continue
                
                # 종목명 확인
                extracted_stock_name = report_data.get('stock_name', '')
                if stock_name not in extracted_stock_name and extracted_stock_name:
                    continue
                
                # 날짜 확인
                report_date = report_data.get('date')
                if isinstance(report_date, str):
                    report_date = self._parse_date_from_text(report_date)
                elif not isinstance(report_date, datetime):
                    report_date = datetime.now()
                
                if report_date < cutoff_date:
                    continue
                
                # 목록 페이지에서 충분한 정보가 있으면 바로 사용
                if report_data.get('firm') and report_data.get('firm') != 'UNKNOWN':
                    # ReportMetadata 생성
                    report = ReportMetadata(
                        report_id=self._generate_report_id(url, report_data.get('title', '')),
                        title=report_data.get('title', '리포트'),
                        stock_code=report_data.get('stock_code', 'UNKNOWN'),
                        stock_name=report_data.get('stock_name', stock_name),
                        analyst_name=report_data.get('analyst_name', 'UNKNOWN'),
                        firm=report_data.get('firm', 'UNKNOWN'),
                        published_date=report_date,
                        source_url=url,
                        investment_opinion=report_data.get('opinion'),
                        target_price=report_data.get('target_price'),
                        current_price=None,
                        consensus_rating=None
                    )
                    reports.append(report)
                    self.logger.info(
                        f"[{i}] ✅ {report.stock_name} - {report.analyst_name} ({report.firm}) "
                        f"- {report.investment_opinion or 'N/A'} - 목표가: {report.target_price or 'N/A'}"
                    )
                else:
                    # 상세 페이지 방문 필요
                    report = self._crawl_report_detail(url)
                    if report:
                        # 종목명 확인
                        if stock_name not in report.stock_name:
                            continue
                        
                        # 날짜 필터링
                        if report.published_date >= cutoff_date:
                            reports.append(report)
                            self.logger.info(
                                f"[{i}] ✅ {report.stock_name} - {report.analyst_name} ({report.firm})"
                            )
                
                if i < len(report_list):
                    time.sleep(self.delay)
            
            except Exception as e:
                self.logger.error(f"리포트 처리 실패 [{i}]: {e}")
                continue
        
        return reports
    
    def _fetch(self, url: str) -> Optional[str]:
        """
        페이지 조회 (재시도 로직 포함, 대응형 크롤러 지원)
        
        Args:
            url: 조회할 URL
            
        Returns:
            Optional[str]: HTML 내용 (실패 시 None)
            
        Raises:
            requests.RequestException: 네트워크 오류 (최대 재시도 후에도 실패 시)
        """
        
        # 대응형 크롤러 사용
        if self.use_adaptive and self.adaptive_crawler:
            response = self.adaptive_crawler.fetch(url)
            if response:
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'
                return response.text
            return None
        
        # 기본 크롤러 (기존 로직)
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=10, verify=True)
                response.raise_for_status()
                
                # 인코딩 처리
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'
                
                return response.text
            
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"페이지 조회 실패 (시도 {attempt}/{self.max_retries}): {url} - {e}. "
                        f"{self.retry_delay}초 후 재시도..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"페이지 조회 최종 실패: {url} - {e}")
                    return None
        
        return None
    
    def pre_test_connection(self, url: Optional[str] = None) -> Tuple[bool, str]:
        """
        사전 연결 테스트
        
        Args:
            url: 테스트할 URL (None이면 기본 URL 사용, 기본값: None)
            
        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
                - (True, "연결 성공") 또는 (False, "연결 실패: 이유")
            
        Raises:
            requests.RequestException: 네트워크 오류
        """
        if not self.use_adaptive or not self.adaptive_crawler:
            self.logger.warning("대응형 크롤러가 비활성화되어 있어 사전 테스트를 건너뜁니다.")
            return True, "대응형 크롤러 비활성화"
        
        test_url = url or self.CONSENSUS_URL
        return self.adaptive_crawler.pre_test(test_url)
    
    def get_crawler_status(self) -> Optional[Dict]:
        """크롤러 상태 조회"""
        if self.use_adaptive and self.adaptive_crawler:
            return self.adaptive_crawler.get_status()
        return None
    
    def _extract_report_links(self, html: str, report_type: str = "stock") -> List[str]:
        """
        목록 페이지에서 보고서 링크 추출 (기존 메서드 유지 - 호환성)
        
        한경 컨센서스 리포트 목록 구조:
        - 리포트 목록은 테이블 또는 리스트 형태
        - 각 리포트 행에 링크가 있음
        - 리포트 보기 / PDF 버튼이 있음
        """
        report_list = self._extract_report_list(html, report_type)
        return [report['url'] for report in report_list if 'url' in report]
    
    def _extract_report_list(self, html: str, report_type: str = "stock") -> List[Dict[str, any]]:
        """
        목록 페이지에서 보고서 메타데이터 추출 (개선된 버전)
        
        PDF 참고: 리포트 목록 테이블에서 다음 정보 추출
        - 증권사명 (예: NH투자증권)
        - 애널리스트 이름
        - 투자의견 (BUY / HOLD / SELL)
        - 목표주가
        - 리포트 날짜
        - 리포트 URL
        - PDF URL (있는 경우)
        
        Args:
            html: 목록 페이지 HTML
            report_type: 리포트 유형 (stock, industry, market, analyst)
        
        Returns:
            List[Dict]: 리포트 메타데이터 리스트
                [
                    {
                        'url': 'https://...',
                        'pdf_url': 'https://...' (옵션),
                        'title': '제목',
                        'firm': 'NH투자증권',
                        'analyst_name': '홍길동',
                        'opinion': 'BUY',
                        'target_price': '98000',
                        'date': '2025-01-05',
                        'stock_name': '삼성전자',
                        'stock_code': '005930'
                    },
                    ...
                ]
        """
        soup = BeautifulSoup(html, 'html.parser')
        reports = []
        
        # 패턴 1: 테이블 구조에서 추출 (한경 컨센서스 주요 구조)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            
            # 헤더 행 찾기 (컬럼 인덱스 확인)
            header_row = None
            header_indices = {}
            for i, row in enumerate(rows[:3]):  # 처음 3행 중 헤더 찾기
                cells = row.find_all(['th', 'td'])
                cell_texts = [cell.get_text(strip=True).lower() for cell in cells]
                
                # 헤더 키워드 확인
                if any(keyword in ' '.join(cell_texts) for keyword in ['날짜', '증권사', '애널리스트', '의견', '목표', '리포트']):
                    header_row = i
                    for j, text in enumerate(cell_texts):
                        if '날짜' in text or 'date' in text:
                            header_indices['date'] = j
                        if '증권사' in text or 'firm' in text or 'company' in text:
                            header_indices['firm'] = j
                        if '애널리스트' in text or 'analyst' in text or '작성' in text:
                            header_indices['analyst'] = j
                        if '의견' in text or 'opinion' in text or 'rating' in text:
                            header_indices['opinion'] = j
                        if '목표' in text or 'target' in text:
                            header_indices['target_price'] = j
                        if '종목' in text or 'stock' in text:
                            header_indices['stock'] = j
                    break
            
            # 데이터 행 처리
            start_idx = header_row + 1 if header_row is not None else 0
            for row in rows[start_idx:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # 최소 3개 셀 필요
                    continue
                
                report_data = {}
                
                # 각 셀에서 정보 추출
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    
                    # 날짜 추출
                    if i == header_indices.get('date', -1) or (i == 0 and re.match(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text)):
                        report_data['date'] = self._parse_date_from_text(text)
                    
                    # 증권사명 추출
                    if i == header_indices.get('firm', -1) or ('증권' in text or '투자' in text or '자산' in text):
                        if not report_data.get('firm'):
                            report_data['firm'] = text
                    
                    # 애널리스트 이름 추출
                    if i == header_indices.get('analyst', -1) or (re.match(r'^[가-힣]{2,4}$', text) and '증권' not in text):
                        if not report_data.get('analyst_name'):
                            report_data['analyst_name'] = text
                    
                    # 투자의견 추출
                    if i == header_indices.get('opinion', -1):
                        report_data['opinion'] = self._normalize_opinion(text)
                    elif any(keyword in text.upper() for keyword in ['BUY', 'HOLD', 'SELL', '매수', '중립', '매도']):
                        if not report_data.get('opinion'):
                            report_data['opinion'] = self._normalize_opinion(text)
                    
                    # 목표주가 추출
                    if i == header_indices.get('target_price', -1):
                        report_data['target_price'] = self._extract_price_from_text(text)
                    elif re.search(r'\d{1,3}(?:,\d{3})*\s*원', text) or re.search(r'\d{4,6}', text):
                        price = self._extract_price_from_text(text)
                        if price and not report_data.get('target_price'):
                            report_data['target_price'] = price
                    
                    # 종목 정보 추출
                    if i == header_indices.get('stock', -1):
                        # 종목명과 코드 분리
                        stock_match = re.search(r'([가-힣\w]+)\s*\(?(\d{6})?\)?', text)
                        if stock_match:
                            report_data['stock_name'] = stock_match.group(1)
                            if stock_match.group(2):
                                report_data['stock_code'] = stock_match.group(2)
                    
                    # 링크 추출
                    link = cell.find('a', href=True)
                    if link:
                        href = link['href']
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(self.BASE_URL, href)
                        
                        # 리포트 링크인지 확인
                        if any(pattern in url.lower() for pattern in ['/consensus/', '/report/', '/analyst/', 'detail', 'view']):
                            report_data['url'] = url
                            
                            # PDF 링크 확인
                            link_text = link.get_text(strip=True).lower()
                            if 'pdf' in link_text or '다운로드' in link_text:
                                report_data['pdf_url'] = url
                        
                        # 제목 추출 (링크 텍스트)
                        if not report_data.get('title'):
                            title_text = link.get_text(strip=True)
                            if title_text and len(title_text) > 5:
                                report_data['title'] = title_text
                
                # 리포트 데이터가 충분히 수집되었는지 확인
                if report_data.get('url') or report_data.get('firm'):
                    # 기본값 설정
                    if not report_data.get('firm'):
                        report_data['firm'] = 'UNKNOWN'
                    if not report_data.get('analyst_name'):
                        report_data['analyst_name'] = 'UNKNOWN'
                    if not report_data.get('date'):
                        report_data['date'] = datetime.now()
                    
                    reports.append(report_data)
        
        # 패턴 2: 리스트 구조에서 추출 (테이블이 없는 경우)
        if not reports:
            lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'list|report|item', re.I))
            for list_elem in lists:
                items = list_elem.find_all(['li', 'div'], recursive=False)
                for item in items:
                    report_data = {}
                    text = item.get_text()
                    
                    # 링크 추출
                    link = item.find('a', href=True)
                    if link:
                        href = link['href']
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(self.BASE_URL, href)
                        report_data['url'] = url
                        report_data['title'] = link.get_text(strip=True)
                    
                    # 텍스트에서 정보 추출
                    if '증권' in text:
                        firm_match = re.search(r'([가-힣\w]+증권)', text)
                        if firm_match:
                            report_data['firm'] = firm_match.group(1)
                    
                    analyst_match = re.search(r'([가-힣]{2,4})\s*[/·]', text)
                    if analyst_match:
                        report_data['analyst_name'] = analyst_match.group(1)
                    
                    date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})', text)
                    if date_match:
                        report_data['date'] = self._parse_date_from_text(date_match.group(1))
                    
                    if report_data.get('url'):
                        reports.append(report_data)
        
        # 패턴 3: 기존 방식 (링크만 추출) - 호환성 유지
        if not reports:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(pattern in href.lower() for pattern in ['/consensus/', '/report/', '/analyst/', 'detail', 'view']):
                    if href.startswith('http'):
                        url = href
                    else:
                        url = urljoin(self.BASE_URL, href)
                    
                    if self.BASE_URL in url:
                        reports.append({'url': url, 'title': link.get_text(strip=True)})
        
        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_reports = []
        for report in reports:
            url = report.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_reports.append(report)
        
        self.logger.info(f"추출된 리포트: {len(unique_reports)}개 (메타데이터 포함: {sum(1 for r in unique_reports if r.get('firm') != 'UNKNOWN')}개)")
        
        return unique_reports
    
    def _crawl_report_detail(self, url: str) -> Optional[ReportMetadata]:
        """
        보고서 상세 페이지 크롤링
        
        한경 컨센서스 리포트 구조 분석 필요
        """
        
        html = self._fetch(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목 추출
            title = self._extract_title(soup)
            
            if not title:
                self.logger.warning(f"제목 없음: {url}")
                return None
            
            # 애널리스트 정보
            analyst_info = self._extract_analyst(soup)
            
            # 종목 정보
            stock_info = self._extract_stock(soup)
            
            # 날짜
            published_date = self._extract_date(soup)
            
            # 투자의견
            opinion = self._extract_opinion(soup)
            
            # 목표가
            target_price = self._extract_target_price(soup)
            
            # 현재가
            current_price = self._extract_current_price(soup)
            
            # 컨센서스 등급
            consensus_rating = self._extract_consensus_rating(soup)
            
            # 보고서 ID 생성
            report_id = self._generate_report_id(url, title)
            
            return ReportMetadata(
                report_id=report_id,
                title=title,
                stock_code=stock_info.get('code', 'UNKNOWN'),
                stock_name=stock_info.get('name', 'UNKNOWN'),
                analyst_name=analyst_info.get('name', 'UNKNOWN'),
                firm=analyst_info.get('firm', 'UNKNOWN'),
                published_date=published_date,
                source_url=url,
                investment_opinion=opinion,
                target_price=target_price,
                current_price=current_price,
                consensus_rating=consensus_rating
            )
        
        except Exception as e:
            self.logger.error(f"상세 정보 추출 실패: {url} - {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """제목 추출"""
        
        # 패턴 시도 순서
        patterns = [
            ('h1', {}),
            ('h2', {}),
            ('h3', {}),
            ('div', {'class': re.compile(r'title', re.I)}),
            ('span', {'class': re.compile(r'title', re.I)}),
            ('title', {}),
        ]
        
        for tag, attrs in patterns:
            element = soup.find(tag, attrs)
            if element:
                text = element.get_text(strip=True)
                if text and 5 < len(text) < 500:
                    return text
        
        return None
    
    def _extract_analyst(self, soup: BeautifulSoup) -> dict:
        """
        애널리스트 정보 추출
        
        한경 컨센서스 리포트 구조:
        - 증권사명: 보통 테이블이나 특정 영역에 표시
        - 애널리스트 이름: 증권사명과 함께 표시
        - 형식: "애널리스트명 / 증권사명" 또는 별도 필드
        """
        
        # 패턴 1: analyst, firm, company 클래스
        analyst_elem = soup.find(['div', 'span', 'td'], {'class': re.compile(r'analyst|writer|author', re.I)})
        firm_elem = soup.find(['div', 'span', 'td'], {'class': re.compile(r'firm|company|sec|증권', re.I)})
        
        analyst_name = 'UNKNOWN'
        firm_name = 'UNKNOWN'
        
        if analyst_elem:
            analyst_name = analyst_elem.get_text(strip=True)
        
        if firm_elem:
            firm_name = firm_elem.get_text(strip=True)
        
        # 패턴 2: 테이블에서 추출 (한경 컨센서스는 보통 테이블 구조)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    
                    # 증권사명 찾기
                    if '증권' in text or '투자' in text or '자산' in text:
                        firm_name = text
                        # 다음 셀에 애널리스트 이름이 있을 수 있음
                        if i + 1 < len(cells):
                            next_text = cells[i + 1].get_text(strip=True)
                            if next_text and len(next_text) < 20:  # 이름 길이 가정
                                analyst_name = next_text
                    
                    # 애널리스트 이름 찾기 (한글 이름 패턴)
                    if re.match(r'^[가-힣]{2,4}$', text) and '증권' not in text:
                        analyst_name = text
        
        # 패턴 3: 텍스트 검색 (최후의 수단)
        if analyst_name == 'UNKNOWN' or firm_name == 'UNKNOWN':
            full_text = soup.get_text()
            
            # "홍길동 / NH투자증권" 패턴
            match = re.search(r'([가-힣]{2,4})\s*[/·]\s*([가-힣\w]+증권)', full_text)
            if match:
                analyst_name = match.group(1)
                firm_name = match.group(2)
            else:
                # "NH투자증권 / 홍길동" 패턴
                match = re.search(r'([가-힣\w]+증권)\s*[/·]\s*([가-힣]{2,4})', full_text)
                if match:
                    firm_name = match.group(1)
                    analyst_name = match.group(2)
        
        return {
            'name': analyst_name,
            'firm': firm_name,
            'department': None
        }
    
    def _extract_stock(self, soup: BeautifulSoup) -> dict:
        """종목 정보 추출"""
        
        # 제목에서 추출 시도
        title = self._extract_title(soup)
        
        if title:
            # "삼성전자 - 4Q24 Preview" → "삼성전자"
            stock_name = title.split('-')[0].split('(')[0].strip()
            
            # 종목 코드 찾기
            stock_code = self._find_stock_code(soup) or 'UNKNOWN'
            
            return {
                'name': stock_name,
                'code': stock_code
            }
        
        return {'name': 'UNKNOWN', 'code': 'UNKNOWN'}
    
    def _find_stock_code(self, soup: BeautifulSoup) -> Optional[str]:
        """종목 코드 찾기"""
        
        # 패턴 1: 직접 표시
        code_elements = soup.find_all(['span', 'div', 'td'], {'class': re.compile(r'code|stock', re.I)})
        for elem in code_elements:
            text = elem.get_text(strip=True)
            if re.match(r'^\d{6}$', text):
                return text
        
        # 패턴 2: 텍스트에서 6자리 숫자 찾기
        text = soup.get_text()
        codes = re.findall(r'\b\d{6}\b', text)
        
        if codes:
            return codes[0]
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        """날짜 추출"""
        
        # 패턴 1: date 클래스
        date_elements = soup.find_all(['div', 'span', 'td'], {'class': re.compile(r'date|time', re.I)})
        
        for date_elem in date_elements:
            text = date_elem.get_text(strip=True)
            parsed = self._parse_date(text)
            if parsed:
                return parsed
        
        # 패턴 2: 날짜 형식 텍스트 검색
        text = soup.get_text()
        date_match = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', text)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass
        
        # 기본값: 오늘
        return datetime.now()
    
    def _parse_date(self, text: str) -> Optional[datetime]:
        """날짜 파싱"""
        
        # "2024.12.30 14:30" → "2024.12.30"
        match = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', text)
        
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass
        
        return None
    
    def _parse_date_from_text(self, text: str) -> datetime:
        """
        텍스트에서 날짜 파싱 (목록 페이지용)
        
        Args:
            text: 날짜 텍스트 (예: "2025-01-05", "2025.01.05")
        
        Returns:
            datetime: 파싱된 날짜 (실패 시 현재 날짜)
        """
        parsed = self._parse_date(text)
        return parsed if parsed else datetime.now()
    
    def _normalize_opinion(self, text: str) -> Optional[str]:
        """
        투자의견 텍스트 정규화
        
        PDF 참고: BUY / HOLD / SELL로 정규화
        
        Args:
            text: 원본 의견 텍스트
        
        Returns:
            Optional[str]: 정규화된 의견 ('BUY', 'HOLD', 'SELL', None)
        """
        if not text:
            return None
        
        text_upper = text.upper().strip()
        text_lower = text.lower().strip()
        
        # Strong Buy 패턴
        if any(keyword in text_upper for keyword in ['STRONG BUY', 'STRONGBUY', '매수(강력)', '강력매수', '적극매수']):
            return 'STRONG_BUY'
        
        # Buy 패턴
        if any(keyword in text_upper for keyword in ['BUY', '매수', '비중확대']):
            return 'BUY'
        
        # Strong Sell 패턴
        if any(keyword in text_upper for keyword in ['STRONG SELL', 'STRONGSELL', '매도(강력)', '강력매도']):
            return 'STRONG_SELL'
        
        # Sell 패턴
        if any(keyword in text_upper for keyword in ['SELL', '매도', '비중축소']):
            return 'SELL'
        
        # Hold 패턴
        if any(keyword in text_upper for keyword in ['HOLD', '중립', '보유', '시장수익률', 'NEUTRAL']):
            return 'HOLD'
        
        return None
    
    def _extract_price_from_text(self, text: str) -> Optional[str]:
        """
        텍스트에서 가격 추출
        
        Args:
            text: 가격이 포함된 텍스트 (예: "98,000원", "98000", "목표가: 98,000원")
        
        Returns:
            Optional[str]: 추출된 가격 문자열 (예: "98000") 또는 None
        """
        if not text:
            return None
        
        # 패턴 1: "98,000원" 또는 "98,000"
        match = re.search(r'([\d,]+)\s*원?', text)
        if match:
            price_str = match.group(1).replace(',', '')
            # 유효한 가격 범위 확인 (1,000원 ~ 1,000,000,000원)
            try:
                price = int(price_str)
                if 1000 <= price <= 1000000000:
                    return price_str
            except ValueError:
                pass
        
        # 패턴 2: 숫자만 (4자리 이상)
        match = re.search(r'\b(\d{4,})\b', text)
        if match:
            price_str = match.group(1)
            try:
                price = int(price_str)
                if 1000 <= price <= 1000000000:
                    return price_str
            except ValueError:
                pass
        
        return None
    
    def _extract_opinion(self, soup: BeautifulSoup) -> Optional[str]:
        """투자의견 추출 (상세 페이지용)"""
        
        # 패턴 1: opinion 클래스
        opinion_elements = soup.find_all(['div', 'span', 'td'], {'class': re.compile(r'opinion|rating|recommend', re.I)})
        
        for elem in opinion_elements:
            text = elem.get_text(strip=True)
            normalized = self._normalize_opinion(text)
            if normalized:
                return normalized
        
        # 패턴 2: 키워드 검색
        text = soup.get_text()
        normalized = self._normalize_opinion(text)
        if normalized:
            return normalized
        
        return None
    
    def _extract_target_price(self, soup: BeautifulSoup) -> Optional[str]:
        """목표가 추출 (상세 페이지용)"""
        
        # 패턴 1: target 클래스
        target_elements = soup.find_all(['div', 'span', 'td'], {'class': re.compile(r'target|price', re.I)})
        
        for elem in target_elements:
            text = elem.get_text(strip=True)
            if '목표가' in text or 'target' in text.lower():
                price = self._extract_price_from_text(text)
                if price:
                    return price
        
        # 패턴 2: "목표가" 텍스트 검색
        text = soup.get_text()
        if '목표가' in text:
            price = self._extract_price_from_text(text)
            if price:
                return price
        
        return None
    
    def _extract_current_price(self, soup: BeautifulSoup) -> Optional[str]:
        """현재가 추출"""
        
        # 패턴: 현재가 관련 텍스트 검색
        text = soup.get_text()
        
        # "현재가: 75,000원" 패턴
        match = re.search(r'현재가[:\s]*([\d,]+원?)', text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_consensus_rating(self, soup: BeautifulSoup) -> Optional[str]:
        """컨센서스 등급 추출"""
        
        # 패턴: 컨센서스 관련 텍스트 검색
        consensus_elements = soup.find_all(['div', 'span'], {'class': re.compile(r'consensus|rating', re.I)})
        
        for elem in consensus_elements:
            text = elem.get_text(strip=True)
            if text and len(text) < 50:
                return text
        
        return None
    
    def _extract_pdf_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        PDF 다운로드 링크 추출 (강화)
        
        PDF 참고: [PDF] 버튼 또는 리포트 보기 링크에서 PDF URL 추출
        
        Args:
            soup: BeautifulSoup 객체
            base_url: 기본 URL (상대 경로 변환용)
        
        Returns:
            Optional[str]: PDF URL 또는 None
        """
        # 패턴 1: PDF 링크 직접 찾기
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|pdf|download', re.I))
        for link in pdf_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            if 'pdf' in link_text or '다운로드' in link_text or 'download' in link_text:
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        # 패턴 2: [PDF] 버튼 텍스트로 찾기
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            if 'pdf' in link_text or '다운로드' in link_text:
                href = link.get('href', '')
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        # 패턴 3: iframe 내 PDF 링크
        iframes = soup.find_all('iframe', src=True)
        for iframe in iframes:
            src = iframe.get('src', '')
            if '.pdf' in src.lower() or 'pdf' in src.lower():
                if src.startswith('http'):
                    return src
                else:
                    return urljoin(base_url, src)
        
        # 패턴 4: data-url 속성
        for elem in soup.find_all(attrs={'data-pdf-url': True}):
            pdf_url = elem.get('data-pdf-url')
            if pdf_url:
                if pdf_url.startswith('http'):
                    return pdf_url
                else:
                    return urljoin(base_url, pdf_url)
        
        return None
    
    def _generate_report_id(self, url: str, title: str) -> str:
        """보고서 ID 생성"""
        
        # URL + 제목의 해시
        content = f"{url}:{title}"
        
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def save_to_json(self, reports: List[ReportMetadata], filename: str):
        """JSON 파일로 저장"""
        
        data = [report.to_dict() for report in reports]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 저장 완료: {filename}")
    
    def save_to_csv(self, reports: List[ReportMetadata], filename: str):
        """CSV 파일로 저장"""
        
        import csv
        
        if not reports:
            return
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reports[0].to_dict().keys())
            writer.writeheader()
            
            for report in reports:
                writer.writerow(report.to_dict())
        
        self.logger.info(f"💾 저장 완료: {filename}")

# ============================================================
# 사용 예제
# ============================================================

def main():
    """메인 함수"""
    
    # 크롤러 초기화
    crawler = HankyungConsensusCrawler(delay=3.0)
    
    # 최근 1일 보고서 수집
    print("🚀 한경 컨센서스 크롤러 시작\n")
    
    reports = crawler.crawl_recent_reports(
        days=1,
        max_reports=20  # 테스트용 20개만
    )
    
    # 결과 출력
    print(f"\n📊 수집 결과: {len(reports)}개\n")
    
    for i, report in enumerate(reports, 1):
        print(f"{i}. {report.stock_name} ({report.stock_code})")
        print(f"   제목: {report.title}")
        print(f"   애널리스트: {report.analyst_name} ({report.firm})")
        print(f"   날짜: {report.published_date.strftime('%Y-%m-%d')}")
        
        if report.investment_opinion:
            print(f"   의견: {report.investment_opinion}")
        
        if report.target_price:
            print(f"   목표가: {report.target_price}")
        
        print()
    
    # 저장
    if reports:
        crawler.save_to_json(reports, 'hankyung_consensus_reports.json')
        crawler.save_to_csv(reports, 'hankyung_consensus_reports.csv')
    
    print("✅ 완료!")

if __name__ == "__main__":
    main()

