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
            
            # 2. 보고서 링크 추출 (종목 리포트 목록)
            report_links = self._extract_report_links(html, report_type=report_type)
            
            self.logger.info(f"📋 발견된 보고서: {len(report_links)}개")
            
            # 3. 각 보고서 상세 정보 수집
            total_links = min(len(report_links), max_reports)
            
            for i, link in enumerate(report_links[:max_reports], 1):
                progress = f"[{i}/{total_links}]"
                self.logger.info(f"{progress} 처리 중: {link[:80]}...")
                
                report = self._crawl_report_detail(link)
                
                if report:
                    # 날짜 필터링
                    if report.published_date >= cutoff_date:
                        # 증권사 필터링
                        if firm_filter and firm_filter not in report.firm:
                            self.logger.info(f"{progress} ⏭️  증권사 필터 불일치: {report.firm}")
                            continue
                        
                        reports.append(report)
                        self.logger.info(
                            f"{progress} ✅ 수집: {report.stock_name} - {report.analyst_name} ({report.firm})"
                        )
                    else:
                        self.logger.info(f"{progress} ⏭️  오래된 보고서 (날짜: {report.published_date.strftime('%Y-%m-%d')})")
                        # 날짜가 오래된 경우 더 이상 진행하지 않음 (최신순 정렬 가정)
                        if i > 10:  # 최소 10개는 확인
                            break
                else:
                    self.logger.warning(f"{progress} ❌ 추출 실패")
                
                # 예의바른 대기
                if i < total_links:
                    time.sleep(self.delay)
            
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
        
        # 검색 결과에서 리포트 링크 추출
        report_links = self._extract_report_links(html, report_type="stock")
        
        self.logger.info(f"📋 발견된 리포트: {len(report_links)}개")
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for i, link in enumerate(report_links[:max_reports], 1):
            report = self._crawl_report_detail(link)
            
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
            
            if i < len(report_links):
                time.sleep(self.delay)
        
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
        목록 페이지에서 보고서 링크 추출
        
        한경 컨센서스 리포트 목록 구조:
        - 리포트 목록은 테이블 또는 리스트 형태
        - 각 리포트 행에 링크가 있음
        - 리포트 보기 / PDF 버튼이 있음
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 패턴 1: 리포트 목록 테이블에서 링크 추출
        # 한경 컨센서스는 보통 <table> 또는 <ul>/<li> 구조 사용
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                for cell in row.find_all(['td', 'th']):
                    for link in cell.find_all('a', href=True):
                        href = link['href']
                        link_text = link.get_text(strip=True)
                        
                        # 리포트 관련 링크 확인
                        if any(keyword in link_text.lower() for keyword in ['리포트', '보기', 'pdf', 'report', 'view']):
                            if href.startswith('http'):
                                full_url = href
                            else:
                                full_url = urljoin(self.BASE_URL, href)
                            
                            if full_url not in links:
                                links.append(full_url)
        
        # 패턴 2: 리스트 구조에서 링크 추출
        lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'list|report|item', re.I))
        for list_elem in lists:
            for item in list_elem.find_all(['li', 'div'], recursive=False):
                for link in item.find_all('a', href=True):
                    href = link['href']
                    
                    # 리포트 링크 패턴
                    if '/consensus' in href or 'report' in href.lower() or 'analyst' in href.lower():
                        if href.startswith('http'):
                            full_url = href
                        else:
                            full_url = urljoin(self.BASE_URL, href)
                        
                        if full_url not in links:
                            links.append(full_url)
        
        # 패턴 3: 모든 링크에서 리포트 관련 링크 찾기
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # 리포트 상세 페이지 링크 패턴
            if any(pattern in href.lower() for pattern in ['/consensus/', '/report/', '/analyst/', 'detail', 'view']):
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.BASE_URL, href)
                
                # 중복 제거 및 유효성 확인
                if full_url not in links and self.BASE_URL in full_url:
                    links.append(full_url)
        
        # 패턴 4: 데이터 속성에서 링크 추출 (동적 로딩)
        for element in soup.find_all(attrs={'data-url': True}):
            href = element.get('data-url')
            if href:
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
        
        # 패턴 5: onclick 이벤트에서 URL 추출
        for element in soup.find_all(attrs={'onclick': True}):
            onclick = element.get('onclick', '')
            # onclick="location.href='/consensus/...'" 패턴
            match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick)
            if match:
                href = match.group(1)
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
        
        # 중복 제거
        links = list(dict.fromkeys(links))
        
        # 리포트 링크만 필터링 (불필요한 링크 제거)
        filtered_links = []
        for link in links:
            # 메인 페이지, 로그인, 광고 등 제외
            if any(exclude in link.lower() for exclude in ['login', 'signup', 'ad', 'banner', 'main', 'index']):
                continue
            filtered_links.append(link)
        
        self.logger.info(f"추출된 링크: {len(filtered_links)}개 (전체 {len(links)}개 중)")
        
        return filtered_links
    
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
    
    def _extract_opinion(self, soup: BeautifulSoup) -> Optional[str]:
        """투자의견 추출"""
        
        # 패턴 1: opinion 클래스
        opinion_elements = soup.find_all(['div', 'span'], {'class': re.compile(r'opinion|rating|recommend', re.I)})
        
        for elem in opinion_elements:
            text = elem.get_text(strip=True)
            if any(word in text for word in ['매수', '중립', '매도', 'Buy', 'Hold', 'Sell', '강력매수', '보유']):
                # 정규화
                if '매수' in text or 'Buy' in text:
                    return 'buy'
                elif '매도' in text or 'Sell' in text:
                    return 'sell'
                elif '중립' in text or 'Hold' in text or '보유' in text:
                    return 'hold'
        
        # 패턴 2: 키워드 검색
        text = soup.get_text()
        if '매수' in text or 'Buy' in text:
            return 'buy'
        elif '매도' in text or 'Sell' in text:
            return 'sell'
        elif '중립' in text or 'Hold' in text or '보유' in text:
            return 'hold'
        
        return None
    
    def _extract_target_price(self, soup: BeautifulSoup) -> Optional[str]:
        """목표가 추출"""
        
        # 패턴 1: target 클래스
        target_elements = soup.find_all(['div', 'span', 'td'], {'class': re.compile(r'target|price', re.I)})
        
        for elem in target_elements:
            text = elem.get_text(strip=True)
            if '목표가' in text or 'target' in text.lower():
                match = re.search(r'[\d,]+원?', text)
                if match:
                    return match.group()
        
        # 패턴 2: "목표가" 텍스트 검색
        text = soup.get_text()
        if '목표가' in text:
            match = re.search(r'목표가[:\s]*([\d,]+원?)', text)
            if match:
                return match.group(1)
        
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

