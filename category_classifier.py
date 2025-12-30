# category_classifier.py
"""
메뉴/카테고리 분류 시스템

보고서를 자동으로 분류하고 메뉴 구조 파악
"""

import sys
import io
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import logging
import re

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from site_structure_analyzer import MenuItem, SiteStructure

@dataclass
class Category:
    """카테고리"""
    name: str
    keywords: List[str]  # 카테고리 식별 키워드
    url_patterns: List[str]  # URL 패턴
    parent: Optional[str] = None
    level: int = 1

@dataclass
class ReportCategory:
    """보고서 카테고리 분류 결과"""
    primary_category: str
    sub_categories: List[str]
    confidence: float
    url: str
    menu_path: List[str]  # 메뉴 경로

class CategoryClassifier:
    """카테고리 분류기"""
    
    def __init__(self, structure: Optional[SiteStructure] = None):
        self.structure = structure
        self.logger = logging.getLogger(__name__)
        
        # 기본 카테고리 정의
        self.categories = self._initialize_categories()
        
        # 메뉴 기반 카테고리 매핑
        if structure:
            self._build_menu_categories()
    
    def _initialize_categories(self) -> Dict[str, Category]:
        """기본 카테고리 초기화"""
        
        categories = {
            '리포트': Category(
                name='리포트',
                keywords=['리포트', 'report', 'research', '분석', 'research_sec'],
                url_patterns=['report', 'research', '리포트'],
                level=1
            ),
            '뉴스': Category(
                name='뉴스',
                keywords=['뉴스', 'news', 'newsletter'],
                url_patterns=['news', '뉴스'],
                level=1
            ),
            '공시': Category(
                name='공시',
                keywords=['공시', 'gongsi', '공시자료', 'disclosure'],
                url_patterns=['gongsi', '공시'],
                level=1
            ),
            '펀드': Category(
                name='펀드',
                keywords=['펀드', 'fund', 'ir', '기업ir'],
                url_patterns=['fund', '펀드'],
                level=1
            ),
            'KOSPI': Category(
                name='KOSPI',
                keywords=['kospi', '코스피', '유가증권'],
                url_patterns=['kospi', '코스피'],
                parent='리포트',
                level=2
            ),
            'KOSDAQ': Category(
                name='KOSDAQ',
                keywords=['kosdaq', '코스닥', '중소형주'],
                url_patterns=['kosdaq', '코스닥'],
                parent='리포트',
                level=2
            ),
            '비상장': Category(
                name='비상장',
                keywords=['nostock', '비상장', '장외'],
                url_patterns=['nostock', '비상장'],
                parent='뉴스',
                level=2
            ),
        }
        
        return categories
    
    def _build_menu_categories(self):
        """메뉴 기반 카테고리 구축"""
        
        if not self.structure:
            return
        
        # 메뉴를 카테고리로 매핑
        for menu in self.structure.menus:
            menu_text = menu.text.lower()
            menu_url = menu.url.lower()
            
            # 카테고리 매칭
            for cat_name, category in self.categories.items():
                # 키워드 매칭
                if any(kw in menu_text or kw in menu_url for kw in category.keywords):
                    # 메뉴를 서브카테고리로 추가
                    if cat_name not in self.categories:
                        continue
                    
                    # URL 패턴도 추가
                    if menu_url not in category.url_patterns:
                        category.url_patterns.append(menu_url)
    
    def classify(self, url: str, title: str = "", content: str = "") -> ReportCategory:
        """보고서 분류"""
        
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 카테고리 점수 계산
        category_scores = defaultdict(float)
        sub_category_scores = defaultdict(float)
        
        # URL 기반 분류
        for cat_name, category in self.categories.items():
            # URL 패턴 매칭
            url_match = sum(1 for pattern in category.url_patterns if pattern in url_lower)
            if url_match > 0:
                category_scores[cat_name] += url_match * 2.0  # URL 매칭은 높은 가중치
            
            # 키워드 매칭
            keyword_match = sum(1 for kw in category.keywords if kw in url_lower or kw in title_lower)
            if keyword_match > 0:
                category_scores[cat_name] += keyword_match * 1.0
        
        # 메뉴 경로 찾기
        menu_path = self._find_menu_path(url)
        
        # 최고 점수 카테고리
        if category_scores:
            primary_category = max(category_scores.items(), key=lambda x: x[1])[0]
            max_score = category_scores[primary_category]
            total_score = sum(category_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.0
        else:
            primary_category = "기타"
            confidence = 0.0
        
        # 서브 카테고리
        sub_categories = []
        if primary_category in self.categories:
            parent_cat = self.categories[primary_category]
            if parent_cat.parent:
                sub_categories.append(parent_cat.parent)
        
        # KOSPI/KOSDAQ 구분
        if 'kospi' in url_lower or '코스피' in url_lower:
            sub_categories.append('KOSPI')
        elif 'kosdaq' in url_lower or '코스닥' in url_lower:
            sub_categories.append('KOSDAQ')
        
        return ReportCategory(
            primary_category=primary_category,
            sub_categories=sub_categories,
            confidence=confidence,
            url=url,
            menu_path=menu_path
        )
    
    def _find_menu_path(self, url: str) -> List[str]:
        """메뉴 경로 찾기"""
        
        if not self.structure:
            return []
        
        url_lower = url.lower()
        path = []
        
        # URL과 일치하는 메뉴 찾기
        for menu in self.structure.menus:
            if menu.url.lower() in url_lower or url_lower in menu.url.lower():
                # 부모 메뉴 추적
                current = menu
                menu_chain = []
                
                while current:
                    menu_chain.insert(0, current.text)
                    # 부모 찾기
                    if current.parent:
                        parent_menu = next(
                            (m for m in self.structure.menus if m.url == current.parent),
                            None
                        )
                        current = parent_menu
                    else:
                        current = None
                
                if menu_chain:
                    path = menu_chain
                    break
        
        return path
    
    def get_category_tree(self) -> Dict:
        """카테고리 트리 구조 반환"""
        
        tree = {}
        
        # 레벨 1 카테고리
        level1 = {name: cat for name, cat in self.categories.items() if cat.level == 1}
        
        for name, category in level1.items():
            # 자식 카테고리 찾기
            children = [
                child_name for child_name, child_cat in self.categories.items()
                if child_cat.parent == name
            ]
            
            tree[name] = {
                'keywords': category.keywords,
                'url_patterns': category.url_patterns,
                'children': children
            }
        
        return tree

# ============================================================
# 통합 분류 시스템
# ============================================================

class IntegratedClassifier:
    """통합 분류 시스템"""
    
    def __init__(self, structure: Optional[SiteStructure] = None):
        self.classifier = CategoryClassifier(structure)
        self.logger = logging.getLogger(__name__)
    
    def classify_report(
        self,
        url: str,
        title: str = "",
        content: str = "",
        metadata: Dict = None
    ) -> Dict:
        """보고서 종합 분류"""
        
        # 카테고리 분류
        category = self.classifier.classify(url, title, content)
        
        # 추가 메타데이터 분석
        additional_info = {}
        
        if metadata:
            # 종목 정보
            if 'stock_code' in metadata:
                additional_info['stock_code'] = metadata['stock_code']
            
            # 애널리스트 정보
            if 'analyst' in metadata:
                additional_info['analyst'] = metadata['analyst']
            
            # 날짜 정보
            if 'date' in metadata:
                additional_info['date'] = metadata['date']
        
        return {
            'category': category.primary_category,
            'sub_categories': category.sub_categories,
            'confidence': category.confidence,
            'menu_path': category.menu_path,
            'url': url,
            'additional_info': additional_info
        }
    
    def get_statistics(self, reports: List[Dict]) -> Dict:
        """분류 통계"""
        
        stats = {
            'total': len(reports),
            'by_category': defaultdict(int),
            'by_sub_category': defaultdict(int),
            'confidence_distribution': {
                'high': 0,  # > 0.7
                'medium': 0,  # 0.4-0.7
                'low': 0  # < 0.4
            }
        }
        
        for report in reports:
            if 'category' in report:
                stats['by_category'][report['category']] += 1
            
            if 'sub_categories' in report:
                for sub_cat in report['sub_categories']:
                    stats['by_sub_category'][sub_cat] += 1
            
            if 'confidence' in report:
                conf = report['confidence']
                if conf > 0.7:
                    stats['confidence_distribution']['high'] += 1
                elif conf > 0.4:
                    stats['confidence_distribution']['medium'] += 1
                else:
                    stats['confidence_distribution']['low'] += 1
        
        return stats

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("카테고리 분류 시스템 테스트")
    print("="*60)
    print()
    
    # 분류기 생성
    classifier = CategoryClassifier()
    
    # 테스트 URL들
    test_urls = [
        ("http://www.38.co.kr/html/news/?m=kosdaq&nkey=report", "KOSDAQ 리포트"),
        ("http://www.38.co.kr/html/news/?m=kospi&nkey=report", "KOSPI 리포트"),
        ("http://www.38.co.kr/html/news/?m=nostock", "비상장 뉴스"),
        ("http://www.38.co.kr/html/fund/", "펀드 정보"),
    ]
    
    print("분류 테스트:")
    print("-" * 60)
    
    for url, title in test_urls:
        result = classifier.classify(url, title)
        print(f"\nURL: {url}")
        print(f"제목: {title}")
        print(f"주 카테고리: {result.primary_category}")
        print(f"서브 카테고리: {', '.join(result.sub_categories) if result.sub_categories else '없음'}")
        print(f"신뢰도: {result.confidence:.1%}")
        if result.menu_path:
            print(f"메뉴 경로: {' > '.join(result.menu_path)}")
    
    # 카테고리 트리
    print("\n" + "="*60)
    print("카테고리 트리")
    print("="*60)
    tree = classifier.get_category_tree()
    for cat_name, cat_info in tree.items():
        print(f"\n{cat_name}:")
        print(f"  키워드: {', '.join(cat_info['keywords'][:5])}")
        if cat_info['children']:
            print(f"  하위 카테고리: {', '.join(cat_info['children'])}")
    
    print("\n✅ 테스트 완료!")


