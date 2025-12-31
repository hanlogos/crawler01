# adaptive_parser.py
"""
적응형 파서 시스템

사이트 구조 변경 시 자동으로 대응하는 파서
"""

import sys
import io
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import json
from dataclasses import dataclass

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from site_structure_analyzer import SiteStructure, DataStructure

@dataclass
class ExtractionResult:
    """추출 결과"""
    success: bool
    value: Any
    method: str  # 사용된 추출 방법
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    error: Optional[str] = None

class AdaptiveParser:
    """적응형 파서"""
    
    def __init__(self, structure: Optional[SiteStructure] = None):
        self.structure = structure
        self.logger = logging.getLogger(__name__)
        
        # 추출 방법 우선순위 (여러 방법 시도)
        self.extraction_methods = {
            'title': self._extract_title_multiple,
            'date': self._extract_date_multiple,
            'analyst': self._extract_analyst_multiple,
            'stock': self._extract_stock_multiple,
            'opinion': self._extract_opinion_multiple,
            'target_price': self._extract_target_price_multiple,
            'content': self._extract_content_multiple,
        }
    
    def parse(self, html: str, page_type: str = 'detail') -> Dict[str, ExtractionResult]:
        """HTML 파싱"""
        
        soup = BeautifulSoup(html, 'html.parser')
        results = {}
        
        # 구조에서 선택자 가져오기
        selectors = {}
        if self.structure and page_type in self.structure.data_structures:
            ds = self.structure.data_structures[page_type]
            selectors = {
                'title': ds.title_selector,
                'date': ds.date_selector,
                'content': ds.content_selector
            }
        
        # 각 필드 추출
        for field, method in self.extraction_methods.items():
            try:
                result = method(soup, selectors.get(field))
                results[field] = result
            except Exception as e:
                results[field] = ExtractionResult(
                    success=False,
                    value=None,
                    method='error',
                    confidence=0.0,
                    error=str(e)
                )
        
        return results
    
    def _extract_title_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """제목 추출 (여러 방법 시도)"""
        
        methods = []
        
        # 방법 1: 구조에서 제공된 선택자
        if preferred_selector:
            methods.append(('structure_selector', preferred_selector))
        
        # 방법 2: 일반적인 선택자들
        common_selectors = [
            ('h1', 'h1'),
            ('h2', 'h2'),
            ('.title', '.title'),
            ('.subject', '.subject'),
            ('#title', '#title'),
            ('title', 'title'),
            ('.report-title', '.report-title'),
            ('.article-title', '.article-title'),
        ]
        
        methods.extend(common_selectors)
        
        # 각 방법 시도
        for method_name, selector in methods:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and 5 < len(text) < 200:  # 적절한 길이
                        return ExtractionResult(
                            success=True,
                            value=text,
                            method=method_name,
                            confidence=0.9 if method_name == 'structure_selector' else 0.7
                        )
            except:
                continue
        
        # 방법 3: 메타 태그
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return ExtractionResult(
                success=True,
                value=meta_title['content'],
                method='meta_og_title',
                confidence=0.8
            )
        
        # 방법 4: title 태그
        title_tag = soup.find('title')
        if title_tag:
            text = title_tag.get_text(strip=True)
            if text and len(text) > 5:
                return ExtractionResult(
                    success=True,
                    value=text,
                    method='title_tag',
                    confidence=0.6
                )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='제목을 찾을 수 없습니다.'
        )
    
    def _extract_date_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """날짜 추출 (여러 방법 시도)"""
        
        import re
        
        methods = []
        
        if preferred_selector:
            methods.append(('structure_selector', preferred_selector))
        
        common_selectors = [
            ('.date', '.date'),
            ('.published', '.published'),
            ('time', 'time'),
            ('.datetime', '.datetime'),
            ('#date', '#date'),
        ]
        
        methods.extend(common_selectors)
        
        # 각 방법 시도
        for method_name, selector in methods:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    text = element.get_text(strip=True)
                    # datetime 속성 확인
                    datetime_attr = element.get('datetime') or element.get('data-date')
                    if datetime_attr:
                        return ExtractionResult(
                            success=True,
                            value=datetime_attr,
                            method=f'{method_name}_attr',
                            confidence=0.95
                        )
                    
                    # 날짜 패턴 확인
                    date_pattern = r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}'
                    match = re.search(date_pattern, text)
                    if match:
                        return ExtractionResult(
                            success=True,
                            value=match.group(),
                            method=method_name,
                            confidence=0.85
                        )
            except:
                continue
        
        # 전체 텍스트에서 날짜 패턴 검색
        text = soup.get_text()
        date_pattern = r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}'
        matches = re.findall(date_pattern, text)
        if matches:
            return ExtractionResult(
                success=True,
                value=matches[0],
                method='text_search',
                confidence=0.5
            )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='날짜를 찾을 수 없습니다.'
        )
    
    def _extract_analyst_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """애널리스트 추출 (여러 방법 시도)"""
        
        methods = []
        
        if preferred_selector:
            methods.append(('structure_selector', preferred_selector))
        
        common_selectors = [
            ('.analyst', '.analyst'),
            ('.author', '.author'),
            ('.writer', '.writer'),
            ('.analyst-info', '.analyst-info'),
        ]
        
        methods.extend(common_selectors)
        
        # 각 방법 시도
        for method_name, selector in methods:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    text = element.get_text(strip=True)
                    # '증권' 또는 '/' 포함 (예: "홍길동 / 삼성증권")
                    if ('증권' in text or '/' in text) and len(text) < 150:
                        return ExtractionResult(
                            success=True,
                            value=text,
                            method=method_name,
                            confidence=0.9 if method_name == 'structure_selector' else 0.7
                        )
            except:
                continue
        
        # 텍스트 검색
        text = soup.get_text()
        analyst_pattern = r'[가-힣\s]+/\s*[가-힣\s]+증권'
        import re
        match = re.search(analyst_pattern, text)
        if match:
            return ExtractionResult(
                success=True,
                value=match.group(),
                method='text_search',
                confidence=0.6
            )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='애널리스트 정보를 찾을 수 없습니다.'
        )
    
    def _extract_stock_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """종목 정보 추출"""
        
        import re
        
        # 6자리 종목 코드 찾기
        text = soup.get_text()
        codes = re.findall(r'\b\d{6}\b', text)
        
        if codes:
            # 가장 많이 나타나는 코드 (종목 코드일 가능성 높음)
            from collections import Counter
            code_counts = Counter(codes)
            most_common = code_counts.most_common(1)[0][0]
            
            return ExtractionResult(
                success=True,
                value=most_common,
                method='code_search',
                confidence=0.7
            )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='종목 코드를 찾을 수 없습니다.'
        )
    
    def _extract_opinion_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """투자의견 추출"""
        
        keywords = {
            '매수': ['매수', 'Buy', 'BUY', '상향'],
            '매도': ['매도', 'Sell', 'SELL', '하향'],
            '중립': ['중립', 'Hold', 'HOLD', '유지', 'Neutral']
        }
        
        # 텍스트 검색
        text = soup.get_text()
        
        for opinion, kw_list in keywords.items():
            for keyword in kw_list:
                if keyword in text:
                    # 주변 컨텍스트 확인
                    idx = text.find(keyword)
                    context = text[max(0, idx-20):idx+20]
                    
                    return ExtractionResult(
                        success=True,
                        value=opinion,
                        method='keyword_search',
                        confidence=0.8
                    )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='투자의견을 찾을 수 없습니다.'
        )
    
    def _extract_target_price_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """목표가 추출"""
        
        import re
        
        # "목표가" 키워드와 숫자 찾기
        text = soup.get_text()
        
        # 패턴 1: "목표가: 75,000원"
        pattern1 = r'목표가[:\s]*([\d,]+)\s*원?'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                price = int(price_str)
                return ExtractionResult(
                    success=True,
                    value=price,
                    method='pattern_search',
                    confidence=0.9
                )
            except:
                pass
        
        # 패턴 2: 숫자만 (주변에 "목표" 키워드)
        pattern2 = r'목표[가]?\s*([\d,]+)\s*원?'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                price = int(price_str)
                return ExtractionResult(
                    success=True,
                    value=price,
                    method='pattern_search2',
                    confidence=0.7
                )
            except:
                pass
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='목표가를 찾을 수 없습니다.'
        )
    
    def _extract_content_multiple(self, soup: BeautifulSoup, preferred_selector: str = None) -> ExtractionResult:
        """본문 추출"""
        
        methods = []
        
        if preferred_selector:
            methods.append(('structure_selector', preferred_selector))
        
        common_selectors = [
            ('.content', '.content'),
            ('.article', '.article'),
            ('.body', '.body'),
            ('#content', '#content'),
            ('main', 'main'),
            ('article', 'article'),
        ]
        
        methods.extend(common_selectors)
        
        # 각 방법 시도
        for method_name, selector in methods:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    # 스크립트, 스타일 제거
                    for script in element(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    
                    text = element.get_text(separator='\n', strip=True)
                    if text and len(text) > 100:  # 충분한 길이
                        return ExtractionResult(
                            success=True,
                            value=text,
                            method=method_name,
                            confidence=0.9 if method_name == 'structure_selector' else 0.7
                        )
            except:
                continue
        
        # body 태그 전체
        body = soup.find('body')
        if body:
            for script in body(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            text = body.get_text(separator='\n', strip=True)
            if text and len(text) > 100:
                return ExtractionResult(
                    success=True,
                    value=text,
                    method='body_tag',
                    confidence=0.5
                )
        
        return ExtractionResult(
            success=False,
            value=None,
            method='none',
            confidence=0.0,
            error='본문을 찾을 수 없습니다.'
        )

# ============================================================
# 구조 변경 대응 시스템
# ============================================================

class StructureChangeHandler:
    """구조 변경 처리기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = AdaptiveParser()
    
    def handle_structure_change(
        self,
        old_structure: SiteStructure,
        new_structure: SiteStructure,
        test_urls: List[str]
    ) -> Dict[str, Any]:
        """구조 변경 처리"""
        
        self.logger.info("구조 변경 감지 - 대응 시작")
        
        # 1. 변경 사항 분석
        from site_structure_analyzer import StructureChangeDetector
        detector = StructureChangeDetector()
        changes = detector.detect_changes(new_structure, old_structure)
        
        # 2. 테스트 URL로 파싱 테스트
        test_results = []
        for url in test_urls:
            result = self._test_parsing(url)
            test_results.append(result)
        
        # 3. 추천 조치
        recommendations = self._generate_recommendations(changes, test_results)
        
        return {
            'changes': changes,
            'test_results': test_results,
            'recommendations': recommendations
        }
    
    def _test_parsing(self, url: str) -> Dict[str, Any]:
        """파싱 테스트"""
        
        import requests
        
        try:
            response = requests.get(url, timeout=10, verify=False)
            response.encoding = response.apparent_encoding
            html = response.text
            
            results = self.parser.parse(html)
            
            # 성공률 계산
            success_count = sum(1 for r in results.values() if r.success)
            success_rate = success_count / len(results) if results else 0
            
            return {
                'url': url,
                'success': success_rate > 0.5,
                'success_rate': success_rate,
                'results': {k: {'success': v.success, 'method': v.method} for k, v in results.items()}
            }
            
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def _generate_recommendations(
        self,
        changes: Dict,
        test_results: List[Dict]
    ) -> List[str]:
        """추천 조치 생성"""
        
        recommendations = []
        
        # 구조 변경이 있으면
        if changes.get('has_changes'):
            recommendations.append("⚠️  사이트 구조가 변경되었습니다.")
            
            # 메뉴 변경
            if changes.get('menu_changes'):
                recommendations.append("  - 메뉴 구조가 변경되었습니다. 링크 추출 로직 확인 필요")
            
            # 선택자 변경
            if changes.get('data_structure_changes'):
                recommendations.append("  - 데이터 구조 선택자가 변경되었습니다. 파서 업데이트 필요")
            
            # 테스트 결과가 나쁘면
            failed_tests = [t for t in test_results if not t.get('success', False)]
            if failed_tests:
                recommendations.append(f"  - {len(failed_tests)}개 테스트 URL에서 파싱 실패")
                recommendations.append("  - 적응형 파서가 자동으로 대응하지만, 수동 확인 권장")
        
        # 성공률이 낮으면
        avg_success = sum(t.get('success_rate', 0) for t in test_results) / len(test_results) if test_results else 0
        if avg_success < 0.7:
            recommendations.append(f"⚠️  평균 파싱 성공률이 낮습니다 ({avg_success:.1%})")
            recommendations.append("  - 사이트 구조를 다시 분석하고 파서를 업데이트하세요")
        
        if not recommendations:
            recommendations.append("✅ 구조 변경이 감지되었지만 파싱은 정상 작동 중입니다.")
        
        return recommendations

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("적응형 파서 테스트")
    print("="*60)
    print()
    
    # 파서 생성
    parser = AdaptiveParser()
    
    # 테스트 HTML (간단한 예시)
    test_html = """
    <html>
    <head><title>삼성전자 4Q24 Preview</title></head>
    <body>
        <h1>삼성전자 4Q24 Preview 및 2025년 전망</h1>
        <div class="date">2024.12.30</div>
        <div class="analyst">홍길동 / 삼성증권</div>
        <div class="content">
            <p>투자의견: 매수</p>
            <p>목표가: 75,000원</p>
            <p>종목코드: 005930</p>
            <p>본문 내용입니다...</p>
        </div>
    </body>
    </html>
    """
    
    # 파싱
    results = parser.parse(test_html)
    
    # 결과 출력
    print("파싱 결과:")
    print("-" * 60)
    for field, result in results.items():
        if result.success:
            print(f"✅ {field}: {result.value} (방법: {result.method}, 신뢰도: {result.confidence:.1%})")
        else:
            print(f"❌ {field}: {result.error}")
    
    print("\n✅ 테스트 완료!")




