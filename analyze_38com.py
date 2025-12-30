# analyze_38com.py
"""
38커뮤니케이션 HTML 구조 분석 도구

실제 사이트의 구조를 파악하여 크롤러를 수정하는 데 사용
"""

import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import json

class SiteAnalyzer:
    """사이트 구조 분석기"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_list_page(self, url: str):
        """목록 페이지 분석"""
        
        print("="*60)
        print("📊 38커뮤니케이션 목록 페이지 분석")
        print("="*60)
        print()
        
        # 1. HTML 가져오기
        print(f"🔍 URL 조회: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            html = response.text
            
            print(f"✅ 조회 성공 ({len(html):,} bytes)\n")
        
        except Exception as e:
            print(f"❌ 조회 실패: {e}")
            return
        
        # HTML 파일로 저장
        with open('38com_list_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 저장: 38com_list_page.html\n")
        
        # 2. 구조 분석
        soup = BeautifulSoup(html, 'html.parser')
        
        # 2-1. 링크 분석
        self._analyze_links(soup)
        
        # 2-2. 테이블 분석
        self._analyze_tables(soup)
        
        # 2-3. 날짜 패턴
        self._analyze_dates(soup)
        
        # 2-4. 클래스 사용 현황
        self._analyze_classes(soup)
    
    def analyze_detail_page(self, url: str):
        """상세 페이지 분석"""
        
        print("\n" + "="*60)
        print("📄 38커뮤니케이션 상세 페이지 분석")
        print("="*60)
        print()
        
        # 1. HTML 가져오기
        print(f"🔍 URL 조회: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            html = response.text
            
            print(f"✅ 조회 성공 ({len(html):,} bytes)\n")
        
        except Exception as e:
            print(f"❌ 조회 실패: {e}")
            return
        
        # HTML 파일로 저장
        with open('38com_detail_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 저장: 38com_detail_page.html\n")
        
        # 2. 구조 분석
        soup = BeautifulSoup(html, 'html.parser')
        
        # 2-1. 제목 후보
        self._find_title_candidates(soup)
        
        # 2-2. 애널리스트 정보
        self._find_analyst_candidates(soup)
        
        # 2-3. 종목 정보
        self._find_stock_candidates(soup)
        
        # 2-4. 투자의견
        self._find_opinion_candidates(soup)
        
        # 2-5. 목표가
        self._find_target_price_candidates(soup)
        
        # 2-6. 날짜
        self._find_date_candidates(soup)
    
    def _analyze_links(self, soup: BeautifulSoup):
        """링크 분석"""
        
        print("🔗 링크 분석")
        print("-" * 40)
        
        links = soup.find_all('a', href=True)
        
        print(f"총 {len(links)}개 링크 발견\n")
        
        # 링크 패턴 분류
        patterns = Counter()
        
        for link in links:
            href = link['href']
            
            # 패턴 추출
            if 'research' in href.lower():
                patterns['research'] += 1
            elif 'report' in href.lower():
                patterns['report'] += 1
            elif 'view' in href.lower():
                patterns['view'] += 1
        
        print("패턴별 개수:")
        for pattern, count in patterns.most_common():
            print(f"  {pattern}: {count}개")
        
        # 샘플 링크 출력
        print("\n샘플 링크 (최대 10개):")
        
        relevant_links = [
            link for link in links
            if any(kw in link['href'].lower() for kw in ['research', 'report', 'view'])
        ]
        
        for i, link in enumerate(relevant_links[:10], 1):
            href = link['href']
            text = link.get_text(strip=True)[:50]
            print(f"  {i}. {href}")
            if text:
                print(f"     텍스트: {text}")
        
        print()
    
    def _analyze_tables(self, soup: BeautifulSoup):
        """테이블 분석"""
        
        print("📊 테이블 분석")
        print("-" * 40)
        
        tables = soup.find_all('table')
        
        print(f"총 {len(tables)}개 테이블 발견\n")
        
        for i, table in enumerate(tables, 1):
            rows = table.find_all('tr')
            cols = table.find_all('td')
            
            print(f"테이블 {i}:")
            print(f"  행: {len(rows)}개")
            print(f"  셀: {len(cols)}개")
            
            # class 확인
            if table.get('class'):
                print(f"  클래스: {table['class']}")
            
            # 첫 행 샘플
            if rows:
                first_row = rows[0]
                cells = first_row.find_all(['td', 'th'])
                
                if cells:
                    print(f"  첫 행 샘플:")
                    for cell in cells[:5]:
                        text = cell.get_text(strip=True)[:30]
                        if text:
                            print(f"    - {text}")
            
            print()
    
    def _analyze_dates(self, soup: BeautifulSoup):
        """날짜 패턴 분석"""
        
        print("📅 날짜 패턴 분석")
        print("-" * 40)
        
        text = soup.get_text()
        
        # 날짜 패턴
        patterns = {
            'YYYY.MM.DD': r'20\d{2}\.\d{1,2}\.\d{1,2}',
            'YYYY-MM-DD': r'20\d{2}-\d{1,2}-\d{1,2}',
            'YYYY/MM/DD': r'20\d{2}/\d{1,2}/\d{1,2}',
        }
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, text)
            
            if matches:
                print(f"\n{pattern_name} 패턴:")
                print(f"  발견: {len(matches)}개")
                print(f"  샘플: {matches[:5]}")
        
        print()
    
    def _analyze_classes(self, soup: BeautifulSoup):
        """CSS 클래스 분석"""
        
        print("🎨 CSS 클래스 분석")
        print("-" * 40)
        
        # 모든 클래스 수집
        classes = []
        
        for element in soup.find_all(class_=True):
            classes.extend(element['class'])
        
        # 빈도수 계산
        class_counter = Counter(classes)
        
        print(f"총 {len(set(classes))}개 고유 클래스\n")
        print("자주 사용되는 클래스 (Top 20):")
        
        for cls, count in class_counter.most_common(20):
            print(f"  {cls}: {count}회")
        
        print()
    
    def _find_title_candidates(self, soup: BeautifulSoup):
        """제목 후보 찾기"""
        
        print("📌 제목 후보")
        print("-" * 40)
        
        candidates = []
        
        # h1, h2, h3, title 태그
        for tag in ['h1', 'h2', 'h3', 'title']:
            elements = soup.find_all(tag)
            
            for el in elements:
                text = el.get_text(strip=True)
                
                if text and 5 < len(text) < 200:
                    candidates.append({
                        'tag': tag,
                        'text': text,
                        'class': el.get('class', [])
                    })
        
        print(f"발견: {len(candidates)}개\n")
        
        for i, cand in enumerate(candidates[:10], 1):
            print(f"{i}. <{cand['tag']}> {cand['text'][:80]}")
            if cand['class']:
                print(f"   클래스: {cand['class']}")
        
        print()
    
    def _find_analyst_candidates(self, soup: BeautifulSoup):
        """애널리스트 정보 후보"""
        
        print("👤 애널리스트 정보 후보")
        print("-" * 40)
        
        candidates = []
        
        # '증권' 키워드가 있는 요소
        for element in soup.find_all(['div', 'span', 'p', 'td']):
            text = element.get_text(strip=True)
            
            if '증권' in text and '/' in text and len(text) < 150:
                candidates.append({
                    'tag': element.name,
                    'text': text,
                    'class': element.get('class', [])
                })
        
        print(f"발견: {len(candidates)}개\n")
        
        # 중복 제거 (동일 텍스트)
        seen = set()
        unique = []
        
        for cand in candidates:
            if cand['text'] not in seen:
                seen.add(cand['text'])
                unique.append(cand)
        
        for i, cand in enumerate(unique[:10], 1):
            print(f"{i}. {cand['text']}")
            if cand['class']:
                print(f"   클래스: {cand['class']}")
        
        print()
    
    def _find_stock_candidates(self, soup: BeautifulSoup):
        """종목 정보 후보"""
        
        print("📈 종목 정보 후보")
        print("-" * 40)
        
        # 6자리 숫자 (종목 코드)
        text = soup.get_text()
        codes = re.findall(r'\b\d{6}\b', text)
        
        print(f"6자리 코드 발견: {len(codes)}개")
        print(f"고유 코드: {len(set(codes))}개\n")
        
        if codes:
            print("샘플:")
            for code in list(set(codes))[:10]:
                print(f"  {code}")
        
        print()
    
    def _find_opinion_candidates(self, soup: BeautifulSoup):
        """투자의견 후보"""
        
        print("💡 투자의견 후보")
        print("-" * 40)
        
        keywords = ['매수', '매도', '중립', 'Buy', 'Sell', 'Hold', 
                   '상향', '하향', '유지']
        
        candidates = []
        
        for element in soup.find_all(['div', 'span', 'td', 'strong']):
            text = element.get_text(strip=True)
            
            if any(kw in text for kw in keywords) and len(text) < 100:
                candidates.append({
                    'tag': element.name,
                    'text': text,
                    'class': element.get('class', [])
                })
        
        print(f"발견: {len(candidates)}개\n")
        
        # 중복 제거
        seen = set()
        unique = []
        
        for cand in candidates:
            if cand['text'] not in seen:
                seen.add(cand['text'])
                unique.append(cand)
        
        for i, cand in enumerate(unique[:10], 1):
            print(f"{i}. {cand['text']}")
            if cand['class']:
                print(f"   클래스: {cand['class']}")
        
        print()
    
    def _find_target_price_candidates(self, soup: BeautifulSoup):
        """목표가 후보"""
        
        print("💰 목표가 후보")
        print("-" * 40)
        
        candidates = []
        
        for element in soup.find_all(['div', 'span', 'td', 'strong']):
            text = element.get_text(strip=True)
            
            # "목표가" 키워드 또는 숫자+원 패턴
            if ('목표' in text or 'target' in text.lower()) and \
               re.search(r'\d{1,3}[,\d]*원?', text):
                candidates.append({
                    'tag': element.name,
                    'text': text,
                    'class': element.get('class', [])
                })
        
        print(f"발견: {len(candidates)}개\n")
        
        # 중복 제거
        seen = set()
        unique = []
        
        for cand in candidates:
            if cand['text'] not in seen:
                seen.add(cand['text'])
                unique.append(cand)
        
        for i, cand in enumerate(unique[:10], 1):
            print(f"{i}. {cand['text']}")
            if cand['class']:
                print(f"   클래스: {cand['class']}")
        
        print()
    
    def _find_date_candidates(self, soup: BeautifulSoup):
        """날짜 후보"""
        
        print("📅 날짜 후보")
        print("-" * 40)
        
        candidates = []
        
        # 날짜 패턴
        date_pattern = r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}'
        
        for element in soup.find_all(['div', 'span', 'td', 'time']):
            text = element.get_text(strip=True)
            
            if re.search(date_pattern, text):
                candidates.append({
                    'tag': element.name,
                    'text': text,
                    'class': element.get('class', [])
                })
        
        print(f"발견: {len(candidates)}개\n")
        
        # 중복 제거
        seen = set()
        unique = []
        
        for cand in candidates:
            if cand['text'] not in seen:
                seen.add(cand['text'])
                unique.append(cand)
        
        for i, cand in enumerate(unique[:10], 1):
            print(f"{i}. {cand['text']}")
            if cand['class']:
                print(f"   클래스: {cand['class']}")
        
        print()
    
    def generate_extraction_code(self):
        """추출 코드 생성"""
        
        print("\n" + "="*60)
        print("🔧 크롤러 수정 코드 생성")
        print("="*60)
        print()
        
        print("위에서 확인한 패턴을 바탕으로 crawler_38com.py를 수정하세요:")
        print()
        
        print("""
# 예시: 제목 추출
def _extract_title(self, soup):
    # 방법 1: 특정 클래스
    title_div = soup.find('div', {'class': 'report-title'})
    if title_div:
        return title_div.get_text(strip=True)
    
    # 방법 2: h1 태그
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    
    return None

# 예시: 애널리스트 추출
def _extract_analyst(self, soup):
    # 발견한 클래스명으로 수정
    analyst_div = soup.find('div', {'class': 'analyst-info'})
    if analyst_div:
        text = analyst_div.get_text(strip=True)
        parts = text.split('/')
        return {
            'name': parts[0].strip(),
            'firm': parts[1].strip() if len(parts) > 1 else None
        }
    
    return {'name': 'UNKNOWN', 'firm': 'UNKNOWN'}
        """)

def main():
    """메인 실행"""
    
    analyzer = SiteAnalyzer()
    
    # 1. 목록 페이지 분석
    list_url = "https://www.38.co.kr/html/fund/research_sec.html"
    
    print("38커뮤니케이션 HTML 구조 분석 도구\n")
    print("이 도구는 실제 사이트의 HTML 구조를 분석하여")
    print("크롤러를 수정하는 데 필요한 정보를 제공합니다.\n")
    
    choice = input("분석할 페이지를 선택하세요:\n1. 목록 페이지\n2. 상세 페이지\n3. 둘 다\n선택 (1-3): ")
    
    if choice in ['1', '3']:
        analyzer.analyze_list_page(list_url)
    
    if choice in ['2', '3']:
        # 상세 페이지 URL 입력
        detail_url = input("\n상세 페이지 URL을 입력하세요: ").strip()
        
        if detail_url:
            analyzer.analyze_detail_page(detail_url)
        else:
            print("⚠️  URL이 입력되지 않아 상세 페이지 분석을 건너뜁니다.")
    
    # 코드 생성 가이드
    analyzer.generate_extraction_code()
    
    print("\n✅ 분석 완료!")
    print("\n다음 단계:")
    print("1. 생성된 HTML 파일 확인 (38com_list_page.html, 38com_detail_page.html)")
    print("2. 위의 분석 결과를 바탕으로 crawler_38com.py 수정")
    print("3. test_crawler.py로 테스트")

if __name__ == "__main__":
    main()


