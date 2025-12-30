# crawler_38com.py
"""
38커뮤니케이션 크롤러

증권 리서치 보고서 수집
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
from urllib.parse import urljoin, urlparse
import urllib3

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
    
    def to_dict(self) -> dict:
        data = asdict(self)
        # datetime을 문자열로 변환
        data['published_date'] = self.published_date.isoformat()
        return data

class ThirtyEightComCrawler:
    """
    38커뮤니케이션 크롤러
    
    사용법:
        crawler = ThirtyEightComCrawler()
        reports = crawler.crawl_recent_reports(days=1)
    """
    
    BASE_URL = "http://www.38.co.kr"  # HTTPS SSL 문제로 HTTP 사용
    REPORT_LIST_URL = "http://www.38.co.kr/html/fund/"
    # 대안 URL들
    ALTERNATIVE_URLS = [
        "http://www.38.co.kr/html/fund/",
        "http://www.38.co.kr/html/news/?m=kosdaq&nkey=report",
        "http://www.38.co.kr/html/news/?m=kospi&nkey=report",
    ]
    
    def __init__(self, delay: float = 3.0, max_retries: int = 3, retry_delay: float = 5.0,
                 use_adaptive: bool = True, site_domain: str = "www.38.co.kr"):
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            })
            self.adaptive_crawler = None
    
    def crawl_recent_reports(
        self, 
        days: int = 1,
        max_reports: int = 100
    ) -> List[ReportMetadata]:
        """
        최근 보고서 크롤링
        
        Args:
            days: 최근 N일
            max_reports: 최대 수집 개수
            
        Returns:
            보고서 메타데이터 리스트
        """
        
        self.logger.info(f"📊 크롤링 시작: 최근 {days}일")
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # 1. 보고서 목록 페이지 조회 (여러 URL 시도)
            list_urls = [
                f"{self.REPORT_LIST_URL}research_sec.html",
                f"{self.REPORT_LIST_URL}",
            ] + self.ALTERNATIVE_URLS
            
            html = None
            list_url = None
            
            for url in list_urls:
                self.logger.info(f"🔍 목록 조회 시도: {url}")
                html = self._fetch(url)
                
                if html and len(html) > 1000:  # 의미있는 내용이 있는지 확인
                    list_url = url
                    self.logger.info(f"✅ 목록 페이지 조회 성공: {url}")
                    break
                else:
                    self.logger.warning(f"⚠️  응답이 비어있거나 너무 짧음: {url}")
            
            if not html:
                self.logger.error("모든 목록 페이지 URL 조회 실패")
                return []
            
            # 2. 보고서 링크 추출
            report_links = self._extract_report_links(html)
            
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
                        reports.append(report)
                        self.logger.info(
                            f"{progress} ✅ 수집: {report.stock_name} - {report.analyst_name}"
                        )
                    else:
                        self.logger.info(f"{progress} ⏭️  오래된 보고서 (날짜: {report.published_date.strftime('%Y-%m-%d')}), 중단")
                        break
                else:
                    self.logger.warning(f"{progress} ❌ 추출 실패")
                
                # 예의바른 대기
                if i < total_links:  # 마지막 항목은 대기 불필요
                    time.sleep(self.delay)
            
            self.logger.info(f"🎉 크롤링 완료: {len(reports)}개 수집")
            
        except Exception as e:
            self.logger.error(f"크롤링 오류: {e}", exc_info=True)
        
        return reports
    
    def _fetch(self, url: str) -> Optional[str]:
        """페이지 조회 (재시도 로직 포함, 대응형 크롤러 지원)"""
        
        # 대응형 크롤러 사용
        if self.use_adaptive and self.adaptive_crawler:
            response = self.adaptive_crawler.fetch(url)
            if response:
                # 인코딩 처리
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    content_type = response.headers.get('Content-Type', '')
                    if 'euc-kr' in content_type.lower() or 'euckr' in content_type.lower():
                        response.encoding = 'euc-kr'
                    else:
                        response.encoding = 'utf-8'
                return response.text
            return None
        
        # 기본 크롤러 (기존 로직)
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=10, verify=False)
                response.raise_for_status()
                
                # 인코딩 처리 (한글)
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    content_type = response.headers.get('Content-Type', '')
                    if 'euc-kr' in content_type.lower() or 'euckr' in content_type.lower():
                        response.encoding = 'euc-kr'
                    else:
                        response.encoding = 'utf-8'
                
                return response.text
            
            except requests.exceptions.SSLError as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"SSL 오류 (시도 {attempt}/{self.max_retries}): {url} - {e}. "
                        f"{self.retry_delay}초 후 재시도..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"페이지 조회 최종 실패 (SSL 오류): {url} - {e}")
                    return None
            
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
            url: 테스트할 URL (None이면 기본 URL 사용)
            
        Returns:
            (success, message)
        """
        if not self.use_adaptive or not self.adaptive_crawler:
            self.logger.warning("대응형 크롤러가 비활성화되어 있어 사전 테스트를 건너뜁니다.")
            return True, "대응형 크롤러 비활성화"
        
        test_url = url or f"{self.REPORT_LIST_URL}"
        return self.adaptive_crawler.pre_test(test_url)
    
    def get_crawler_status(self) -> Optional[Dict]:
        """크롤러 상태 조회"""
        if self.use_adaptive and self.adaptive_crawler:
            return self.adaptive_crawler.get_status()
        return None
    
    def _extract_report_links(self, html: str) -> List[str]:
        """
        목록 페이지에서 보고서 링크 추출
        
        38커뮤니케이션 실제 구조:
        - 리포트 목록: /html/news/?m=kosdaq&nkey=report
        - 상세 페이지: /html/news/?o=v&m=kosdaq&key=report&no=1879932&page=1
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 패턴 1: 리포트 상세 페이지 링크 (o=v&no= 패턴)
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # 리포트 상세 페이지 패턴
            if ('o=v' in href or 'no=' in href) and ('report' in href.lower() or 'key=report' in href):
                # 상대 경로 → 절대 경로
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.BASE_URL, href)
                links.append(full_url)
        
        # 패턴 2: 기존 패턴 (하위 호환성)
        if not links:
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if 'research_view' in href or 'report_view' in href:
                    full_url = urljoin(self.REPORT_LIST_URL, href)
                    links.append(full_url)
        
        # 중복 제거
        links = list(dict.fromkeys(links))
        
        return links
    
    def _crawl_report_detail(self, url: str) -> Optional[ReportMetadata]:
        """
        보고서 상세 페이지 크롤링
        
        38커뮤니케이션 구조 (예상):
        <div class="report-info">
          <h2>삼성전자 - 4Q24 Preview</h2>
          <div class="analyst">홍길동 / 삼성증권 / IT</div>
          <div class="date">2024.12.30</div>
          <div class="opinion">매수</div>
          <div class="target">목표가: 75,000원</div>
        </div>
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
                target_price=target_price
            )
        
        except Exception as e:
            self.logger.error(f"상세 정보 추출 실패: {url} - {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """제목 추출"""
        
        # 패턴 시도 순서 (실제 사이트 구조 반영)
        patterns = [
            ('span', {'id': 'subject'}),  # 38커뮤니케이션 실제 구조
            ('b', {}),  # <b>태그 안의 제목
            ('h1', {}),
            ('h2', {'class': 'report-title'}),
            ('h2', {}),
            ('div', {'class': 'title'}),
            ('title', {}),
        ]
        
        for tag, attrs in patterns:
            element = soup.find(tag, attrs)
            if element:
                text = element.get_text(strip=True)
                # 의미있는 제목인지 확인 (너무 짧거나 일반적인 텍스트 제외)
                if text and 5 < len(text) < 500 and not text.startswith('비상장주식거래'):
                    return text
        
        return None
    
    def _extract_analyst(self, soup: BeautifulSoup) -> dict:
        """
        애널리스트 정보 추출
        
        형식: "홍길동 / 삼성증권 / IT팀"
        """
        
        # 패턴 1: analyst 클래스
        analyst_div = soup.find('div', {'class': 'analyst'})
        
        if not analyst_div:
            # 패턴 2: 텍스트 검색
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if '증권' in text and '/' in text:
                    analyst_div = div
                    break
        
        if analyst_div:
            text = analyst_div.get_text(strip=True)
            parts = [p.strip() for p in text.split('/')]
            
            return {
                'name': parts[0] if len(parts) > 0 else 'UNKNOWN',
                'firm': parts[1] if len(parts) > 1 else 'UNKNOWN',
                'department': parts[2] if len(parts) > 2 else None
            }
        
        return {'name': 'UNKNOWN', 'firm': 'UNKNOWN'}
    
    def _extract_stock(self, soup: BeautifulSoup) -> dict:
        """종목 정보 추출"""
        
        # 제목에서 추출 시도
        title = self._extract_title(soup)
        
        if title:
            # "삼성전자 - 4Q24 Preview" → "삼성전자"
            stock_name = title.split('-')[0].strip()
            
            # 종목 코드는 별도 조회 필요
            # (38커뮤니케이션에 있을 수도)
            stock_code = self._find_stock_code(soup) or 'UNKNOWN'
            
            return {
                'name': stock_name,
                'code': stock_code
            }
        
        return {'name': 'UNKNOWN', 'code': 'UNKNOWN'}
    
    def _find_stock_code(self, soup: BeautifulSoup) -> Optional[str]:
        """종목 코드 찾기"""
        
        # 패턴 1: 직접 표시
        code_span = soup.find('span', {'class': 'stock-code'})
        if code_span:
            return code_span.get_text(strip=True)
        
        # 패턴 2: 텍스트에서 6자리 숫자 찾기
        import re
        text = soup.get_text()
        
        # 한국 주식은 6자리
        codes = re.findall(r'\b\d{6}\b', text)
        
        if codes:
            return codes[0]
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        """날짜 추출"""
        
        # 패턴 1: "2025년 12월 30일" 형식 (38커뮤니케이션 실제 구조)
        import re
        text = soup.get_text()
        
        # "2025년 12월 30일" 패턴
        date_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass
        
        # 패턴 2: date 클래스
        date_div = soup.find('div', {'class': 'date'})
        
        if not date_div:
            # 패턴 3: 날짜 형식 텍스트 검색
            for div in soup.find_all('div', 'td'):
                text = div.get_text(strip=True)
                if self._looks_like_date(text):
                    date_div = div
                    break
        
        if date_div:
            text = date_div.get_text(strip=True)
            return self._parse_date(text)
        
        # 기본값: 오늘
        return datetime.now()
    
    def _looks_like_date(self, text: str) -> bool:
        """날짜 형식인지 확인"""
        import re
        
        # "2024.12.30", "2024-12-30", "2024/12/30"
        pattern = r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}'
        return bool(re.search(pattern, text))
    
    def _parse_date(self, text: str) -> datetime:
        """날짜 파싱"""
        import re
        
        # "2024.12.30 14:30" → "2024.12.30"
        match = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', text)
        
        if match:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day))
        
        return datetime.now()
    
    def _extract_opinion(self, soup: BeautifulSoup) -> Optional[str]:
        """투자의견 추출"""
        
        # 패턴 1: opinion 클래스
        opinion_div = soup.find('div', {'class': 'opinion'})
        
        if not opinion_div:
            # 패턴 2: 키워드 검색
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if any(word in text for word in ['매수', '중립', '매도', 'Buy', 'Hold', 'Sell']):
                    opinion_div = div
                    break
        
        if opinion_div:
            text = opinion_div.get_text(strip=True)
            
            # 정규화
            if '매수' in text or 'Buy' in text:
                return 'buy'
            elif '매도' in text or 'Sell' in text:
                return 'sell'
            elif '중립' in text or 'Hold' in text:
                return 'hold'
        
        return None
    
    def _extract_target_price(self, soup: BeautifulSoup) -> Optional[str]:
        """목표가 추출"""
        
        # 패턴 1: target 클래스
        target_div = soup.find('div', {'class': 'target'})
        
        if not target_div:
            # 패턴 2: "목표가" 텍스트 검색
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if '목표가' in text:
                    target_div = div
                    break
        
        if target_div:
            text = target_div.get_text(strip=True)
            
            # "목표가: 75,000원" → "75,000원"
            import re
            match = re.search(r'[\d,]+원?', text)
            
            if match:
                return match.group()
        
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
    crawler = ThirtyEightComCrawler(delay=3.0)
    
    # 최근 1일 보고서 수집
    print("🚀 38커뮤니케이션 크롤러 시작\n")
    
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
        crawler.save_to_json(reports, '38com_reports.json')
        crawler.save_to_csv(reports, '38com_reports.csv')
    
    print("✅ 완료!")

if __name__ == "__main__":
    main()

