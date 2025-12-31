# crawler_naver_finance_research.py
"""
네이버 금융 리서치 크롤러

네이버 금융에서 애널리스트 리포트 수집
https://finance.naver.com/research/

계약:
- 입력: stock_name (str, 종목명), stock_code (Optional[str], 종목코드), days (int, 최근 N일)
- 출력: List[ReportMetadata] (보고서 메타데이터 리스트)
- 예외: requests.RequestException (네트워크 오류), ValueError (잘못된 파라미터), OSError (파일 저장 오류)
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
import os

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
    """보고서 메타데이터 (네이버 금융용)"""
    report_id: str
    title: str
    stock_code: str
    stock_name: str
    analyst_name: str
    firm: str
    published_date: datetime
    source_url: str
    pdf_url: Optional[str] = None
    
    # 투자 정보
    investment_opinion: Optional[str] = None  # BUY, HOLD, SELL
    target_price: Optional[int] = None  # 숫자로 저장
    current_price: Optional[int] = None
    
    # 소스 정보
    source: str = "NaverFinance"  # NaverFinance, HankyungConsensus
    
    # 파일 경로
    pdf_path: Optional[str] = None
    meta_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['published_date'] = self.published_date.isoformat()
        return data
    
    def to_meta_json(self) -> dict:
        """메타데이터 JSON 형식 (파일 저장용)"""
        return {
            "symbol": self.stock_code,
            "company": self.stock_name,
            "date": self.published_date.strftime("%Y-%m-%d"),
            "securities": self.firm,
            "analyst": self.analyst_name,
            "rating": self.investment_opinion or "N/A",
            "target_price": self.target_price,
            "current_price": self.current_price,
            "source": self.source,
            "url": self.source_url,
            "pdf_url": self.pdf_url,
            "title": self.title
        }

class NaverFinanceResearchCrawler:
    """
    네이버 금융 리서치 크롤러
    
    사용법:
        crawler = NaverFinanceResearchCrawler()
        reports = crawler.search_by_stock("삼성전자", days=7)
        
        # PDF 다운로드 포함
        reports = crawler.search_by_stock("삼성전자", days=7, download_pdf=True)
    """
    
    BASE_URL = "https://finance.naver.com"
    RESEARCH_URL = "https://finance.naver.com/research"
    
    def __init__(self, delay: float = 2.0, max_retries: int = 3, retry_delay: float = 5.0,
                 use_adaptive: bool = True, site_domain: str = "finance.naver.com",
                 download_dir: str = "AnalystReports"):
        """
        초기화
        
        Args:
            delay: 요청 간 대기 시간 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 대기 시간 (초)
            use_adaptive: 대응형 크롤러 사용 여부
            site_domain: 사이트 도메인
            download_dir: 리포트 다운로드 기본 디렉토리
        """
        self.delay = delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_adaptive = use_adaptive and ADAPTIVE_CRAWLER_AVAILABLE
        self.site_domain = site_domain
        self.download_dir = download_dir
        
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
                'Referer': 'https://finance.naver.com/',
            })
            self.adaptive_crawler = None
    
    def search_by_stock(
        self,
        stock_name: str,
        stock_code: Optional[str] = None,
        days: int = 7,
        max_reports: int = 50,
        download_pdf: bool = False
    ) -> List[ReportMetadata]:
        """
        특정 종목으로 리포트 검색
        
        Args:
            stock_name: 종목명 (예: "삼성전자")
            stock_code: 종목코드 (예: "005930", None이면 자동 검색, 기본값: None)
            days: 최근 N일 (기본값: 7)
            max_reports: 최대 수집 개수 (기본값: 50)
            download_pdf: PDF 다운로드 여부 (기본값: False)
            
        Returns:
            List[ReportMetadata]: 보고서 메타데이터 리스트
            
        Raises:
            ValueError: 잘못된 stock_name 또는 days < 0
            requests.RequestException: 네트워크 오류 또는 페이지 조회 실패
            OSError: PDF 다운로드 또는 파일 저장 실패
            
        계약:
        - 입력: stock_name은 비어있지 않은 문자열, days는 양수
        - 출력: ReportMetadata 리스트 (빈 리스트 가능)
        - 예외: ValueError (잘못된 파라미터), RequestException (네트워크 오류), OSError (파일 오류)
        """
        
        # 입력 검증
        if not stock_name or not isinstance(stock_name, str):
            raise ValueError(f"stock_name must be a non-empty string, got {stock_name}")
        if days < 0:
            raise ValueError(f"days must be non-negative, got {days}")
        if max_reports < 0:
            raise ValueError(f"max_reports must be non-negative, got {max_reports}")
        
        self.logger.info(f"🔍 네이버 금융 리서치 검색: {stock_name} (최근 {days}일)")
        
        # 종목 코드가 없으면 검색
        if not stock_code:
            stock_code = self._search_stock_code(stock_name)
            if not stock_code:
                self.logger.error(f"종목 코드를 찾을 수 없습니다: {stock_name}")
                return []
        
        # 리서치 페이지 접근
        research_url = f"{self.RESEARCH_URL}/company_list.naver?code={stock_code}"
        
        html = self._fetch(research_url)
        
        if not html:
            self.logger.error(f"리서치 페이지 접근 실패: {stock_name}")
            return []
        
        # 리포트 목록 추출
        report_links = self._extract_report_links(html, stock_code)
        
        self.logger.info(f"📋 발견된 리포트: {len(report_links)}개")
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for i, link_info in enumerate(report_links[:max_reports], 1):
            try:
                report = self._crawl_report_detail(link_info, stock_code, stock_name)
                
                if report:
                    # 날짜 필터링
                    if report.published_date >= cutoff_date:
                        # PDF 다운로드
                        if download_pdf and report.pdf_url:
                            pdf_path = self._download_pdf(
                                report.pdf_url,
                                report.stock_name,
                                report.stock_code,
                                report.published_date,
                                report.firm,
                                report.investment_opinion,
                                report.target_price
                            )
                            report.pdf_path = pdf_path
                            
                            # 메타데이터 저장
                            meta_path = self._save_metadata(report)
                            report.meta_path = meta_path
                        
                        reports.append(report)
                        self.logger.info(
                            f"[{i}] ✅ {report.stock_name} - {report.analyst_name} ({report.firm}) "
                            f"- {report.investment_opinion} - 목표가: {report.target_price}"
                        )
                
                if i < len(report_links):
                    time.sleep(self.delay)
                    
            except Exception as e:
                self.logger.error(f"리포트 처리 실패 [{i}]: {e}")
                continue
        
        self.logger.info(f"🎉 수집 완료: {len(reports)}개")
        return reports
    
    def _search_stock_code(self, stock_name: str) -> Optional[str]:
        """종목명으로 종목 코드 검색"""
        
        search_url = f"{self.BASE_URL}/item/search.naver?query={stock_name}"
        
        html = self._fetch(search_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 종목 코드 패턴 찾기 (6자리 숫자)
        code_match = re.search(r'code=(\d{6})', html)
        if code_match:
            return code_match.group(1)
        
        return None
    
    def _fetch(self, url: str) -> Optional[str]:
        """페이지 조회"""
        
        if self.use_adaptive and self.adaptive_crawler:
            response = self.adaptive_crawler.fetch(url)
            if response:
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'
                return response.text
            return None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=10, verify=True)
                response.raise_for_status()
                
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'
                
                return response.text
            
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"페이지 조회 실패 (시도 {attempt}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"페이지 조회 최종 실패: {url} - {e}")
                    return None
        
        return None
    
    def _extract_report_links(self, html: str, stock_code: str) -> List[Dict]:
        """
        리포트 목록에서 링크 추출
        
        Returns:
            [{'url': '...', 'title': '...', 'date': '...', ...}, ...]
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 네이버 금융 리서치 테이블 구조 파싱
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 4:  # 최소 컬럼 수 확인
                    continue
                
                # 리포트 링크 찾기
                link_elem = row.find('a', href=True)
                if not link_elem:
                    continue
                
                href = link_elem['href']
                if not href.startswith('http'):
                    href = urljoin(self.BASE_URL, href)
                
                # 테이블에서 정보 추출
                link_info = {
                    'url': href,
                    'title': link_elem.get_text(strip=True),
                    'date': None,
                    'firm': None,
                    'analyst': None,
                    'opinion': None,
                    'target_price': None
                }
                
                # 각 셀에서 정보 추출
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    
                    # 날짜 (YYYY.MM.DD 형식)
                    if re.match(r'\d{4}\.\d{2}\.\d{2}', text):
                        link_info['date'] = text
                    
                    # 증권사명
                    if '증권' in text or '투자' in text or '자산' in text:
                        link_info['firm'] = text
                    
                    # 투자의견 (BUY, HOLD, SELL 등)
                    if any(word in text.upper() for word in ['BUY', 'HOLD', 'SELL', '매수', '보유', '매도']):
                        link_info['opinion'] = text
                    
                    # 목표가 (숫자 + 원)
                    price_match = re.search(r'([\d,]+)\s*원?', text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            link_info['target_price'] = int(price_str)
                        except:
                            pass
                
                if link_info['url']:
                    links.append(link_info)
        
        return links
    
    def _crawl_report_detail(
        self,
        link_info: Dict,
        stock_code: str,
        stock_name: str
    ) -> Optional[ReportMetadata]:
        """리포트 상세 정보 추출"""
        
        url = link_info['url']
        html = self._fetch(url)
        
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목
            title = link_info.get('title') or self._extract_title(soup)
            
            if not title:
                return None
            
            # 날짜 파싱
            date_str = link_info.get('date')
            if date_str:
                published_date = self._parse_date(date_str)
            else:
                published_date = self._extract_date(soup)
            
            # 애널리스트 정보
            analyst_info = self._extract_analyst(soup, link_info)
            
            # 투자의견
            opinion = link_info.get('opinion') or self._extract_opinion(soup)
            
            # 목표가
            target_price = link_info.get('target_price') or self._extract_target_price(soup)
            
            # PDF 링크 찾기
            pdf_url = self._extract_pdf_link(soup, url)
            
            # 리포트 ID 생성
            report_id = self._generate_report_id(url, title)
            
            return ReportMetadata(
                report_id=report_id,
                title=title,
                stock_code=stock_code,
                stock_name=stock_name,
                analyst_name=analyst_info.get('name', 'UNKNOWN'),
                firm=link_info.get('firm') or analyst_info.get('firm', 'UNKNOWN'),
                published_date=published_date,
                source_url=url,
                pdf_url=pdf_url,
                investment_opinion=self._normalize_opinion(opinion),
                target_price=target_price,
                source="NaverFinance"
            )
        
        except Exception as e:
            self.logger.error(f"상세 정보 추출 실패: {url} - {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """제목 추출"""
        for tag in ['h1', 'h2', 'h3', 'title']:
            elem = soup.find(tag)
            if elem:
                text = elem.get_text(strip=True)
                if text and 5 < len(text) < 500:
                    return text
        return None
    
    def _extract_analyst(self, soup: BeautifulSoup, link_info: Dict) -> dict:
        """애널리스트 정보 추출"""
        analyst = link_info.get('analyst', 'UNKNOWN')
        firm = link_info.get('firm', 'UNKNOWN')
        
        # 페이지에서 추가 정보 추출 시도
        text = soup.get_text()
        match = re.search(r'([가-힣]{2,4})\s*[/·]\s*([가-힣\w]+증권)', text)
        if match:
            analyst = match.group(1)
            firm = match.group(2)
        
        return {'name': analyst, 'firm': firm}
    
    def _extract_opinion(self, soup: BeautifulSoup) -> Optional[str]:
        """투자의견 추출"""
        text = soup.get_text()
        
        if '매수' in text or 'BUY' in text.upper():
            return 'BUY'
        elif '매도' in text or 'SELL' in text.upper():
            return 'SELL'
        elif '보유' in text or 'HOLD' in text.upper() or '중립' in text:
            return 'HOLD'
        
        return None
    
    def _extract_target_price(self, soup: BeautifulSoup) -> Optional[int]:
        """목표가 추출"""
        text = soup.get_text()
        
        # "목표가: 98,000원" 패턴
        match = re.search(r'목표가[:\s]*([\d,]+)', text)
        if match:
            try:
                return int(match.group(1).replace(',', ''))
            except:
                pass
        
        return None
    
    def _extract_pdf_link(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """PDF 링크 추출"""
        
        # PDF 링크 찾기
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            
            if 'pdf' in href.lower() or 'pdf' in link_text:
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """날짜 파싱 (YYYY.MM.DD 형식)"""
        try:
            return datetime.strptime(date_str, '%Y.%m.%d')
        except:
            return datetime.now()
    
    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        """날짜 추출"""
        text = soup.get_text()
        match = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', text)
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass
        return datetime.now()
    
    def _normalize_opinion(self, opinion: Optional[str]) -> Optional[str]:
        """투자의견 정규화"""
        if not opinion:
            return None
        
        opinion_upper = opinion.upper()
        
        if 'BUY' in opinion_upper or '매수' in opinion:
            return 'BUY'
        elif 'SELL' in opinion_upper or '매도' in opinion:
            return 'SELL'
        elif 'HOLD' in opinion_upper or '보유' in opinion or '중립' in opinion:
            return 'HOLD'
        
        return opinion
    
    def _generate_report_id(self, url: str, title: str) -> str:
        """보고서 ID 생성"""
        content = f"{url}:{title}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _download_pdf(
        self,
        pdf_url: str,
        stock_name: str,
        stock_code: str,
        date: datetime,
        firm: str,
        opinion: Optional[str],
        target_price: Optional[int]
    ) -> Optional[str]:
        """PDF 다운로드"""
        
        try:
            # 폴더 구조 생성: AnalystReports/종목명_종목코드/
            folder_name = f"{stock_name}_{stock_code}"
            folder_path = os.path.join(self.download_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # 파일명 생성: YYYY-MM-DD_증권사_의견_목표가.pdf
            date_str = date.strftime("%Y-%m-%d")
            firm_clean = firm.replace('/', '_').replace('\\', '_')
            opinion_str = opinion or "N/A"
            price_str = f"{target_price}" if target_price else "N/A"
            
            filename = f"{date_str}_{firm_clean}_{opinion_str}_{price_str}.pdf"
            filepath = os.path.join(folder_path, filename)
            
            # PDF 다운로드
            response = self.session.get(pdf_url, timeout=30, verify=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"📄 PDF 다운로드 완료: {filepath}")
            return filepath
        
        except Exception as e:
            self.logger.error(f"PDF 다운로드 실패: {pdf_url} - {e}")
            return None
    
    def _save_metadata(self, report: ReportMetadata) -> Optional[str]:
        """메타데이터 JSON 저장"""
        
        try:
            if not report.pdf_path:
                return None
            
            # PDF 파일과 같은 폴더에 메타데이터 저장
            folder_path = os.path.dirname(report.pdf_path)
            meta_filename = os.path.basename(report.pdf_path).replace('.pdf', '.meta.json')
            meta_path = os.path.join(folder_path, meta_filename)
            
            meta_data = report.to_meta_json()
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 메타데이터 저장 완료: {meta_path}")
            return meta_path
        
        except Exception as e:
            self.logger.error(f"메타데이터 저장 실패: {e}")
            return None

# ============================================================
# 사용 예제
# ============================================================

def main():
    """메인 함수"""
    
    crawler = NaverFinanceResearchCrawler(delay=2.0)
    
    print("🚀 네이버 금융 리서치 크롤러 시작\n")
    
    # 삼성전자 리포트 수집 (PDF 다운로드 포함)
    reports = crawler.search_by_stock(
        stock_name="삼성전자",
        stock_code="005930",
        days=7,
        max_reports=20,
        download_pdf=True
    )
    
    print(f"\n📊 수집 결과: {len(reports)}개\n")
    
    for i, report in enumerate(reports, 1):
        print(f"{i}. {report.stock_name} ({report.stock_code})")
        print(f"   제목: {report.title}")
        print(f"   애널리스트: {report.analyst_name} ({report.firm})")
        print(f"   날짜: {report.published_date.strftime('%Y-%m-%d')}")
        print(f"   의견: {report.investment_opinion}")
        print(f"   목표가: {report.target_price}")
        if report.pdf_path:
            print(f"   PDF: {report.pdf_path}")
        print()
    
    print("✅ 완료!")

if __name__ == "__main__":
    main()

