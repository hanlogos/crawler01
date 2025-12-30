# site_structure_analyzer.py
"""
사이트 구조 분석기

메뉴, 링크 패턴, 데이터 구조 등을 분석하여
구조 변경을 감지하고 대응할 수 있도록 함
"""

import sys
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
import logging
from collections import defaultdict

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class MenuItem:
    """메뉴 항목"""
    text: str
    url: str
    level: int  # 메뉴 깊이 (1, 2, 3...)
    parent: Optional[str] = None
    children: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class LinkPattern:
    """링크 패턴"""
    pattern: str  # 정규식 패턴 또는 키워드
    url_type: str  # 'report_detail', 'report_list', 'category' 등
    confidence: float  # 패턴 신뢰도 (0.0 ~ 1.0)
    examples: List[str] = None  # 예시 URL들
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []

@dataclass
class DataStructure:
    """데이터 구조"""
    page_type: str  # 'list', 'detail', 'category' 등
    title_selector: str  # 제목 선택자
    date_selector: str  # 날짜 선택자
    content_selector: str  # 본문 선택자
    metadata: Dict = None  # 추가 메타데이터
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SiteStructure:
    """사이트 구조 스냅샷"""
    domain: str
    timestamp: datetime
    base_url: str
    menus: List[MenuItem]
    link_patterns: List[LinkPattern]
    data_structures: Dict[str, DataStructure]  # page_type -> DataStructure
    checksum: str  # 구조 체크섬 (변경 감지용)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def calculate_checksum(self) -> str:
        """구조 체크섬 계산"""
        content = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content.encode()).hexdigest()

class SiteStructureAnalyzer:
    """사이트 구조 분석기"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze(self) -> SiteStructure:
        """전체 사이트 구조 분석"""
        
        self.logger.info(f"🔍 사이트 구조 분석 시작: {self.base_url}")
        
        # 1. 메뉴 구조 분석
        menus = self._analyze_menus()
        self.logger.info(f"✅ 메뉴 {len(menus)}개 발견")
        
        # 2. 링크 패턴 분석
        link_patterns = self._analyze_link_patterns()
        self.logger.info(f"✅ 링크 패턴 {len(link_patterns)}개 발견")
        
        # 3. 데이터 구조 분석
        data_structures = self._analyze_data_structures()
        self.logger.info(f"✅ 데이터 구조 {len(data_structures)}개 분석")
        
        # 구조 생성
        structure = SiteStructure(
            domain=self.domain,
            timestamp=datetime.now(),
            base_url=self.base_url,
            menus=menus,
            link_patterns=link_patterns,
            data_structures=data_structures,
            checksum=""
        )
        
        # 체크섬 계산
        structure.checksum = structure.calculate_checksum()
        
        self.logger.info(f"✅ 구조 분석 완료 (체크섬: {structure.checksum[:8]}...)")
        
        return structure
    
    def _analyze_menus(self) -> List[MenuItem]:
        """메뉴 구조 분석"""
        
        menus = []
        
        try:
            html = self._fetch(self.base_url)
            if not html:
                return menus
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 메뉴 찾기 (여러 패턴 시도)
            menu_selectors = [
                'nav', 'nav ul', 'nav li',
                '.menu', '.navigation', '.nav',
                '#menu', '#navigation', '#nav',
                'ul.menu', 'ul.nav', 'div.menu'
            ]
            
            menu_elements = []
            for selector in menu_selectors:
                elements = soup.select(selector)
                if elements:
                    menu_elements.extend(elements)
                    break
            
            # 링크 추출
            links = soup.find_all('a', href=True)
            
            menu_map = {}  # url -> MenuItem
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if not text or not href:
                    continue
                
                # 절대 URL로 변환
                full_url = urljoin(self.base_url, href)
                
                # 메뉴 키워드 확인
                menu_keywords = ['리포트', 'report', 'research', '분석', 'news', '뉴스', 'fund', '펀드']
                if any(keyword in href.lower() or keyword in text.lower() for keyword in menu_keywords):
                    level = self._determine_menu_level(link)
                    
                    menu_item = MenuItem(
                        text=text,
                        url=full_url,
                        level=level
                    )
                    
                    menus.append(menu_item)
                    menu_map[full_url] = menu_item
            
            # 부모-자식 관계 설정
            self._build_menu_hierarchy(menus, menu_map)
            
        except Exception as e:
            self.logger.error(f"메뉴 분석 오류: {e}")
        
        return menus
    
    def _determine_menu_level(self, element) -> int:
        """메뉴 레벨 결정"""
        
        level = 1
        parent = element.parent
        
        while parent:
            if parent.name in ['ul', 'nav', 'div']:
                if 'menu' in parent.get('class', []) or 'nav' in parent.get('class', []):
                    level += 1
            parent = parent.parent
            if level > 5:  # 최대 깊이 제한
                break
        
        return min(level, 5)
    
    def _build_menu_hierarchy(self, menus: List[MenuItem], menu_map: Dict):
        """메뉴 계층 구조 구축"""
        
        # URL 경로 기반으로 부모 찾기
        for menu in menus:
            parsed = urlparse(menu.url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if len(path_parts) > 1:
                # 부모 경로 찾기
                parent_path = '/'.join(path_parts[:-1])
                parent_url = f"{parsed.scheme}://{parsed.netloc}/{parent_path}"
                
                # 부모 메뉴 찾기
                for other_menu in menus:
                    if other_menu.url == parent_url or parent_url in other_menu.url:
                        menu.parent = other_menu.url
                        if menu.url not in other_menu.children:
                            other_menu.children.append(menu.url)
                        break
    
    def _analyze_link_patterns(self) -> List[LinkPattern]:
        """링크 패턴 분석"""
        
        patterns = []
        
        try:
            html = self._fetch(self.base_url)
            if not html:
                return patterns
            
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)
            
            # URL 그룹화
            url_groups = defaultdict(list)
            
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                full_url = urljoin(self.base_url, href)
                parsed = urlparse(full_url)
                
                # URL 패턴 분류
                url_type = self._classify_url_type(full_url, link)
                url_groups[url_type].append(full_url)
            
            # 패턴 생성
            for url_type, urls in url_groups.items():
                if not urls:
                    continue
                
                # 공통 패턴 추출
                pattern = self._extract_common_pattern(urls)
                
                if pattern:
                    patterns.append(LinkPattern(
                        pattern=pattern,
                        url_type=url_type,
                        confidence=0.8,  # 기본 신뢰도
                        examples=urls[:5]  # 최대 5개 예시
                    ))
            
        except Exception as e:
            self.logger.error(f"링크 패턴 분석 오류: {e}")
        
        return patterns
    
    def _classify_url_type(self, url: str, element) -> str:
        """URL 타입 분류"""
        
        url_lower = url.lower()
        text = element.get_text(strip=True).lower()
        
        # 리포트 상세 페이지
        if any(x in url_lower for x in ['o=v', 'view', 'detail', 'read']):
            if 'report' in url_lower or '리포트' in text:
                return 'report_detail'
        
        # 리포트 목록 페이지
        if any(x in url_lower for x in ['report', 'research', '리포트', '분석']):
            if 'list' in url_lower or '목록' in text:
                return 'report_list'
            return 'report_list'  # 기본값
        
        # 카테고리 페이지
        if any(x in url_lower for x in ['category', 'cat', '카테고리', '분류']):
            return 'category'
        
        # 뉴스 페이지
        if 'news' in url_lower or '뉴스' in text:
            return 'news'
        
        # 기타
        return 'other'
    
    def _extract_common_pattern(self, urls: List[str]) -> str:
        """공통 패턴 추출"""
        
        if not urls:
            return ""
        
        if len(urls) == 1:
            return urls[0]
        
        # URL 파싱
        parsed_urls = [urlparse(url) for url in urls]
        
        # 공통 경로 찾기
        common_path = ""
        path_parts_list = [url.path.split('/') for url in parsed_urls]
        
        if path_parts_list:
            min_length = min(len(parts) for parts in path_parts_list)
            
            for i in range(min_length):
                parts = [parts[i] for parts in path_parts_list]
                if len(set(parts)) == 1:  # 모두 같음
                    common_path += "/" + parts[0]
                else:
                    # 파라미터 패턴 찾기
                    if '=' in parts[0] or '?' in parts[0]:
                        # 쿼리 파라미터 패턴
                        common_path += "/*"
                    break
        
        # 쿼리 파라미터 패턴
        if parsed_urls[0].query:
            common_path += "?" + parsed_urls[0].query.split('&')[0] + "=*"
        
        return common_path or urls[0]
    
    def _analyze_data_structures(self) -> Dict[str, DataStructure]:
        """데이터 구조 분석"""
        
        structures = {}
        
        try:
            # 목록 페이지 분석
            list_structure = self._analyze_list_page()
            if list_structure:
                structures['list'] = list_structure
            
            # 상세 페이지 분석
            detail_structure = self._analyze_detail_page()
            if detail_structure:
                structures['detail'] = detail_structure
            
        except Exception as e:
            self.logger.error(f"데이터 구조 분석 오류: {e}")
        
        return structures
    
    def _analyze_list_page(self) -> Optional[DataStructure]:
        """목록 페이지 구조 분석"""
        
        # 리포트 목록 URL 시도
        test_urls = [
            f"{self.base_url}/html/news/?m=kosdaq&nkey=report",
            f"{self.base_url}/html/fund/",
            f"{self.base_url}/html/news/",
        ]
        
        for url in test_urls:
            try:
                html = self._fetch(url)
                if not html or len(html) < 1000:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # 제목 선택자 찾기
                title_selectors = self._find_selectors_for_text(soup, ['제목', 'title', 'subject'])
                
                # 날짜 선택자 찾기
                date_selectors = self._find_selectors_for_text(soup, ['날짜', 'date', '작성일'])
                
                return DataStructure(
                    page_type='list',
                    title_selector=title_selectors[0] if title_selectors else 'a',
                    date_selector=date_selectors[0] if date_selectors else '.date',
                    content_selector='.list, .item, tr, li',
                    metadata={'test_url': url}
                )
                
            except Exception as e:
                continue
        
        return None
    
    def _analyze_detail_page(self) -> Optional[DataStructure]:
        """상세 페이지 구조 분석"""
        
        # 리포트 상세 URL 시도 (예시)
        # 실제로는 목록에서 링크를 찾아서 분석해야 함
        
        return DataStructure(
            page_type='detail',
            title_selector='h1, .title, .subject',
            date_selector='.date, .published, time',
            content_selector='.content, .article, .body, #content',
            metadata={}
        )
    
    def _find_selectors_for_text(self, soup: BeautifulSoup, keywords: List[str]) -> List[str]:
        """특정 텍스트를 포함하는 요소의 선택자 찾기"""
        
        selectors = []
        
        for keyword in keywords:
            # 텍스트로 검색
            elements = soup.find_all(string=lambda text: text and keyword in text)
            
            for element in elements[:3]:  # 최대 3개
                parent = element.parent
                if parent:
                    # 선택자 생성
                    selector = self._generate_selector(parent)
                    if selector and selector not in selectors:
                        selectors.append(selector)
        
        return selectors
    
    def _generate_selector(self, element) -> str:
        """요소의 CSS 선택자 생성"""
        
        if element.name:
            selector = element.name
            
            # ID가 있으면 추가
            if element.get('id'):
                return f"#{element.get('id')}"
            
            # 클래스가 있으면 추가
            classes = element.get('class', [])
            if classes:
                class_str = '.'.join(classes)
                return f".{class_str}"
            
            return selector
        
        return ""
    
    def _fetch(self, url: str) -> Optional[str]:
        """URL 가져오기"""
        
        try:
            response = self.session.get(url, timeout=10, verify=False)
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            self.logger.error(f"URL 가져오기 실패: {url} - {e}")
            return None

# ============================================================
# 구조 변경 감지기
# ============================================================

class StructureChangeDetector:
    """구조 변경 감지기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.structure_history: List[SiteStructure] = []
    
    def detect_changes(
        self,
        current: SiteStructure,
        previous: Optional[SiteStructure] = None
    ) -> Dict[str, any]:
        """구조 변경 감지"""
        
        if not previous:
            return {
                'has_changes': False,
                'message': '이전 구조가 없어 비교할 수 없습니다.'
            }
        
        changes = {
            'has_changes': False,
            'checksum_changed': current.checksum != previous.checksum,
            'menu_changes': [],
            'link_pattern_changes': [],
            'data_structure_changes': [],
            'timestamp': current.timestamp.isoformat()
        }
        
        # 메뉴 변경 감지
        menu_changes = self._detect_menu_changes(current.menus, previous.menus)
        if menu_changes:
            changes['has_changes'] = True
            changes['menu_changes'] = menu_changes
        
        # 링크 패턴 변경 감지
        pattern_changes = self._detect_pattern_changes(
            current.link_patterns,
            previous.link_patterns
        )
        if pattern_changes:
            changes['has_changes'] = True
            changes['link_pattern_changes'] = pattern_changes
        
        # 데이터 구조 변경 감지
        structure_changes = self._detect_structure_changes(
            current.data_structures,
            previous.data_structures
        )
        if structure_changes:
            changes['has_changes'] = True
            changes['data_structure_changes'] = structure_changes
        
        if changes['checksum_changed']:
            changes['has_changes'] = True
        
        return changes
    
    def _detect_menu_changes(
        self,
        current: List[MenuItem],
        previous: List[MenuItem]
    ) -> List[Dict]:
        """메뉴 변경 감지"""
        
        changes = []
        
        current_urls = {m.url for m in current}
        previous_urls = {m.url for m in previous}
        
        # 추가된 메뉴
        added = current_urls - previous_urls
        if added:
            changes.append({
                'type': 'added',
                'count': len(added),
                'urls': list(added)[:5]  # 최대 5개
            })
        
        # 삭제된 메뉴
        removed = previous_urls - current_urls
        if removed:
            changes.append({
                'type': 'removed',
                'count': len(removed),
                'urls': list(removed)[:5]
            })
        
        return changes
    
    def _detect_pattern_changes(
        self,
        current: List[LinkPattern],
        previous: List[LinkPattern]
    ) -> List[Dict]:
        """링크 패턴 변경 감지"""
        
        changes = []
        
        current_types = {p.url_type for p in current}
        previous_types = {p.url_type for p in previous}
        
        # 새로운 패턴 타입
        added_types = current_types - previous_types
        if added_types:
            changes.append({
                'type': 'new_pattern_type',
                'types': list(added_types)
            })
        
        # 사라진 패턴 타입
        removed_types = previous_types - current_types
        if removed_types:
            changes.append({
                'type': 'removed_pattern_type',
                'types': list(removed_types)
            })
        
        return changes
    
    def _detect_structure_changes(
        self,
        current: Dict[str, DataStructure],
        previous: Dict[str, DataStructure]
    ) -> List[Dict]:
        """데이터 구조 변경 감지"""
        
        changes = []
        
        # 새로운 페이지 타입
        added_types = set(current.keys()) - set(previous.keys())
        if added_types:
            changes.append({
                'type': 'new_page_type',
                'types': list(added_types)
            })
        
        # 사라진 페이지 타입
        removed_types = set(previous.keys()) - set(current.keys())
        if removed_types:
            changes.append({
                'type': 'removed_page_type',
                'types': list(removed_types)
            })
        
        # 선택자 변경
        for page_type in set(current.keys()) & set(previous.keys()):
            curr = current[page_type]
            prev = previous[page_type]
            
            if curr.title_selector != prev.title_selector:
                changes.append({
                    'type': 'selector_changed',
                    'page_type': page_type,
                    'field': 'title_selector',
                    'old': prev.title_selector,
                    'new': curr.title_selector
                })
        
        return changes
    
    def save_structure(self, structure: SiteStructure, filename: str = None):
        """구조 저장"""
        
        if filename is None:
            filename = f"structure_{structure.domain}_{structure.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(structure.to_dict(), f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"구조 저장: {filename}")
        self.structure_history.append(structure)
    
    def load_structure(self, filename: str) -> Optional[SiteStructure]:
        """구조 로드"""
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # SiteStructure 재구성
            menus = [MenuItem(**m) for m in data['menus']]
            link_patterns = [LinkPattern(**p) for p in data['link_patterns']]
            data_structures = {
                k: DataStructure(**v)
                for k, v in data['data_structures'].items()
            }
            
            structure = SiteStructure(
                domain=data['domain'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                base_url=data['base_url'],
                menus=menus,
                link_patterns=link_patterns,
                data_structures=data_structures,
                checksum=data['checksum']
            )
            
            return structure
            
        except Exception as e:
            self.logger.error(f"구조 로드 실패: {e}")
            return None

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("사이트 구조 분석기")
    print("="*60)
    print()
    
    # 분석기 생성
    analyzer = SiteStructureAnalyzer("http://www.38.co.kr")
    
    # 구조 분석
    structure = analyzer.analyze()
    
    # 결과 출력
    print("\n" + "="*60)
    print("분석 결과")
    print("="*60)
    print(f"도메인: {structure.domain}")
    print(f"메뉴 수: {len(structure.menus)}개")
    print(f"링크 패턴: {len(structure.link_patterns)}개")
    print(f"데이터 구조: {len(structure.data_structures)}개")
    print(f"체크섬: {structure.checksum[:16]}...")
    
    # 메뉴 출력
    if structure.menus:
        print("\n메뉴 목록:")
        for menu in structure.menus[:10]:  # 최대 10개
            indent = "  " * (menu.level - 1)
            print(f"{indent}- {menu.text} ({menu.url[:60]}...)")
    
    # 링크 패턴 출력
    if structure.link_patterns:
        print("\n링크 패턴:")
        for pattern in structure.link_patterns:
            print(f"  [{pattern.url_type}] {pattern.pattern}")
            print(f"    예시: {pattern.examples[0] if pattern.examples else 'N/A'}")
    
    # 구조 저장
    detector = StructureChangeDetector()
    detector.save_structure(structure)
    
    print(f"\n✅ 구조 저장 완료: structure_*.json")


