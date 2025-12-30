# crawler_38com_adaptive.py
"""
적응형 38커뮤니케이션 크롤러

사이트 구조 변경에 자동 대응하는 크롤러
"""

import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 기존 크롤러 임포트
from typing import Optional
from crawler_38com import ThirtyEightComCrawler, ReportMetadata
from structure_monitor import AdaptiveCrawler38Com
from adaptive_parser import AdaptiveParser, ExtractionResult
from category_classifier import IntegratedClassifier
import logging

class AdaptiveThirtyEightComCrawler(ThirtyEightComCrawler):
    """적응형 38커뮤니케이션 크롤러"""
    
    def __init__(self, *args, use_adaptive_parsing: bool = True, **kwargs):
        """
        초기화
        
        Args:
            use_adaptive_parsing: 적응형 파싱 사용 여부
            *args, **kwargs: 부모 클래스 인자
        """
        super().__init__(*args, **kwargs)
        
        self.use_adaptive_parsing = use_adaptive_parsing
        
        if self.use_adaptive_parsing:
            # 적응형 파싱 시스템 초기화 (크롤러와는 별개)
            self.structure_handler = AdaptiveCrawler38Com()
            self.parser = self.structure_handler.parser
            self.classifier = IntegratedClassifier(self.structure_handler.current_structure)
            
            self.logger.info("✅ 적응형 파싱 활성화")
        else:
            self.structure_handler = None
            self.parser = None
            self.classifier = None
    
    def _crawl_report_detail(self, url: str) -> Optional[ReportMetadata]:
        """보고서 상세 페이지 크롤링 (적응형)"""
        
        html = self._fetch(url)
        
        if not html:
            return None
        
        try:
            # 적응형 파싱 사용
            if self.use_adaptive_parsing and self.parser:
                parsed = self.parser.parse(html, page_type='detail')
                
                # 파싱 결과를 ReportMetadata로 변환
                title_result = parsed.get('title', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                date_result = parsed.get('date', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                analyst_result = parsed.get('analyst', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                stock_result = parsed.get('stock', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                opinion_result = parsed.get('opinion', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                target_price_result = parsed.get('target_price', ExtractionResult(success=False, value=None, method='', confidence=0.0))
                
                # 기본값 설정
                title = title_result.value if title_result.success else "UNKNOWN"
                date_str = date_result.value if date_result.success else ""
                analyst_text = analyst_result.value if analyst_result.success else "UNKNOWN"
                stock_code = stock_result.value if stock_result.success else "UNKNOWN"
                opinion = opinion_result.value if opinion_result.success else None
                target_price = target_price_result.value if target_price_result.success else None
                
                # 날짜 파싱
                from datetime import datetime
                published_date = self._parse_date(date_str) if date_str else datetime.now()
                
                # 애널리스트 파싱
                analyst_name, firm = self._parse_analyst(analyst_text)
                
                # 종목명 (코드만 있으면 이름은 UNKNOWN)
                stock_name = "UNKNOWN"
                
                # 보고서 ID 생성
                report_id = self._generate_report_id(url, title)
                
                # 카테고리 분류
                category_info = None
                if self.classifier:
                    category_info = self.classifier.classify_report(
                        url=url,
                        title=title,
                        metadata={
                            'stock_code': stock_code,
                            'analyst': analyst_name,
                            'date': date_str
                        }
                    )
                
                metadata = ReportMetadata(
                    report_id=report_id,
                    title=title,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    analyst_name=analyst_name,
                    firm=firm,
                    published_date=published_date,
                    source_url=url,
                    investment_opinion=opinion,
                    target_price=str(target_price) if target_price else None
                )
                
                # 카테고리 정보 추가 (메타데이터로)
                if category_info:
                    self.logger.info(f"카테고리: {category_info['category']} (신뢰도: {category_info['confidence']:.1%})")
                
                return metadata
            else:
                # 기존 방식 사용
                return super()._crawl_report_detail(url)
                
        except Exception as e:
            self.logger.error(f"적응형 파싱 오류: {e}")
            # 폴백: 기존 방식 사용
            return super()._crawl_report_detail(url)
    
    def _parse_date(self, date_str: str):
        """날짜 문자열 파싱"""
        
        from datetime import datetime
        import re
        
        # 다양한 형식 시도
        formats = [
            '%Y.%m.%d',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d %H:%M',
        ]
        
        # 숫자만 추출
        date_match = re.search(r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}', date_str)
        if date_match:
            date_str = date_match.group()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return datetime.now()
    
    def _parse_analyst(self, analyst_text: str) -> tuple:
        """애널리스트 텍스트 파싱"""
        
        if not analyst_text or analyst_text == "UNKNOWN":
            return "UNKNOWN", "UNKNOWN"
        
        # "이름 / 회사" 형식
        if '/' in analyst_text:
            parts = analyst_text.split('/')
            name = parts[0].strip()
            firm = parts[1].strip() if len(parts) > 1 else "UNKNOWN"
            return name, firm
        
        return analyst_text, "UNKNOWN"
    
    def update_structure(self):
        """구조 업데이트"""
        
        if self.structure_handler:
            return self.structure_handler.update_structure()
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
    print("적응형 38커뮤니케이션 크롤러 테스트")
    print("="*60)
    print()
    
    # 적응형 크롤러 생성
    crawler = AdaptiveThirtyEightComCrawler(
        delay=3.0,
        use_adaptive=True,
        use_adaptive_parsing=True
    )
    
    # 구조 업데이트 (선택적)
    print("구조 확인 중...")
    structure_result = crawler.update_structure()
    
    if structure_result and structure_result['changes'].get('has_changes'):
        print("⚠️  구조 변경이 감지되었습니다.")
    else:
        print("✅ 구조 변경 없음")
    
    print("\n크롤링 시작...")
    
    # 크롤링 (최근 7일, 최대 3개)
    reports = crawler.crawl_recent_reports(
        days=7,
        max_reports=3
    )
    
    print(f"\n✅ {len(reports)}개 보고서 수집 완료")
    
    if reports:
        print("\n수집된 보고서:")
        for i, report in enumerate(reports, 1):
            print(f"\n{i}. {report.title}")
            print(f"   종목: {report.stock_name} ({report.stock_code})")
            print(f"   애널리스트: {report.analyst_name} ({report.firm})")
            print(f"   날짜: {report.published_date.strftime('%Y-%m-%d')}")
            if report.investment_opinion:
                print(f"   의견: {report.investment_opinion}")
            if report.target_price:
                print(f"   목표가: {report.target_price}")

