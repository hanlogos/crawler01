# report_title_manager.py
"""
보고서 제목 관리 시스템

원본 제목 보존 + AI 요약 제목 생성
"""

import sys
import io
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
import hashlib

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class ReportTitle:
    """보고서 제목 정보"""
    report_id: str
    original_title: str  # 원본 제목
    ai_summary_title: Optional[str] = None  # AI 요약 제목
    keywords: List[str] = None  # 키워드
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    def get_display_title(self) -> str:
        """표시용 제목 (AI 요약이 있으면 그것, 없으면 원본)"""
        return self.ai_summary_title or self.original_title
    
    def get_filename(self, use_ai_title: bool = False) -> str:
        """파일명 생성"""
        
        title = self.ai_summary_title if use_ai_title and self.ai_summary_title else self.original_title
        
        # 파일명에 사용할 수 없는 문자 제거
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '', title)
        filename = filename.replace(' ', '_')
        filename = filename[:100]  # 길이 제한
        
        return f"{self.report_id}_{filename}"

class ReportTitleManager:
    """보고서 제목 관리자"""
    
    def __init__(self, llm_processor=None):
        self.titles: Dict[str, ReportTitle] = {}
        self.llm_processor = llm_processor
        self.logger = logging.getLogger(__name__)
        
        # 저장 파일
        self.storage_file = "report_titles.json"
        self._load_titles()
    
    def register_report(
        self,
        report_id: str,
        original_title: str,
        keywords: List[str] = None
    ) -> ReportTitle:
        """보고서 등록"""
        
        if report_id in self.titles:
            # 업데이트
            title_obj = self.titles[report_id]
            title_obj.original_title = original_title
            if keywords:
                title_obj.keywords = keywords
            title_obj.updated_at = datetime.now()
        else:
            # 새로 생성
            title_obj = ReportTitle(
                report_id=report_id,
                original_title=original_title,
                keywords=keywords or []
            )
            self.titles[report_id] = title_obj
        
        self._save_titles()
        return title_obj
    
    def generate_ai_title(
        self,
        report_id: str,
        content: str = None,
        metadata: Dict = None
    ) -> Optional[str]:
        """AI 요약 제목 생성"""
        
        title_obj = self.titles.get(report_id)
        if not title_obj:
            self.logger.warning(f"보고서를 찾을 수 없습니다: {report_id}")
            return None
        
        # LLM이 있으면 사용
        if self.llm_processor:
            try:
                prompt = self._create_title_prompt(title_obj, content, metadata)
                ai_title = self.llm_processor.process(prompt)
                
                # 결과 정리
                ai_title = ai_title.strip()
                if ai_title.startswith('"') and ai_title.endswith('"'):
                    ai_title = ai_title[1:-1]
                
                title_obj.ai_summary_title = ai_title
                title_obj.updated_at = datetime.now()
                self._save_titles()
                
                self.logger.info(f"AI 제목 생성 완료: {report_id}")
                return ai_title
            
            except Exception as e:
                self.logger.error(f"AI 제목 생성 실패: {e}")
                return None
        
        # LLM이 없으면 키워드 기반 간단한 요약
        return self._generate_simple_title(title_obj, metadata)
    
    def _create_title_prompt(
        self,
        title_obj: ReportTitle,
        content: str = None,
        metadata: Dict = None
    ) -> str:
        """제목 생성 프롬프트"""
        
        prompt = f"""
다음 보고서의 원본 제목을 바탕으로, 더 간결하고 명확한 요약 제목을 생성하세요.

원본 제목: {title_obj.original_title}
"""
        
        if metadata:
            if 'stock_name' in metadata:
                prompt += f"종목: {metadata['stock_name']}\n"
            if 'analyst' in metadata:
                prompt += f"애널리스트: {metadata['analyst']}\n"
            if 'investment_opinion' in metadata:
                prompt += f"투자의견: {metadata['investment_opinion']}\n"
        
        if content:
            prompt += f"\n내용 요약:\n{content[:500]}...\n"
        
        prompt += """
요구사항:
- 50자 이내로 간결하게
- 핵심 정보 포함 (종목, 의견, 주요 내용)
- 파일명으로 사용 가능한 형식
- 따옴표 없이 제목만 반환

요약 제목:
"""
        
        return prompt
    
    def _generate_simple_title(
        self,
        title_obj: ReportTitle,
        metadata: Dict = None
    ) -> str:
        """간단한 제목 생성 (LLM 없이)"""
        
        parts = []
        
        if metadata:
            if 'stock_name' in metadata:
                parts.append(metadata['stock_name'])
            if 'investment_opinion' in metadata:
                parts.append(f"[{metadata['investment_opinion']}]")
        
        if title_obj.keywords:
            parts.extend(title_obj.keywords[:2])
        
        if parts:
            simple_title = " ".join(parts)
            if len(simple_title) > 50:
                simple_title = simple_title[:47] + "..."
        else:
            # 원본 제목에서 앞부분만
            simple_title = title_obj.original_title[:50]
        
        title_obj.ai_summary_title = simple_title
        title_obj.updated_at = datetime.now()
        self._save_titles()
        
        return simple_title
    
    def get_title(self, report_id: str) -> Optional[ReportTitle]:
        """제목 가져오기"""
        return self.titles.get(report_id)
    
    def list_titles(self, limit: int = 100) -> List[ReportTitle]:
        """제목 목록"""
        return list(self.titles.values())[:limit]
    
    def search_titles(self, keyword: str) -> List[ReportTitle]:
        """제목 검색"""
        
        keyword_lower = keyword.lower()
        results = []
        
        for title_obj in self.titles.values():
            if (keyword_lower in title_obj.original_title.lower() or
                (title_obj.ai_summary_title and keyword_lower in title_obj.ai_summary_title.lower()) or
                any(keyword_lower in kw.lower() for kw in title_obj.keywords)):
                results.append(title_obj)
        
        return results
    
    def _load_titles(self):
        """제목 로드"""
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for title_data in data.get('titles', []):
                title_obj = ReportTitle(**title_data)
                # datetime 변환
                if isinstance(title_obj.created_at, str):
                    title_obj.created_at = datetime.fromisoformat(title_obj.created_at)
                if isinstance(title_obj.updated_at, str):
                    title_obj.updated_at = datetime.fromisoformat(title_obj.updated_at)
                
                self.titles[title_obj.report_id] = title_obj
            
            self.logger.info(f"제목 로드 완료: {len(self.titles)}개")
        
        except FileNotFoundError:
            self.logger.info("제목 파일이 없습니다.")
        except Exception as e:
            self.logger.error(f"제목 로드 실패: {e}")
    
    def _save_titles(self):
        """제목 저장"""
        
        try:
            data = {
                'titles': [title.to_dict() for title in self.titles.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"제목 저장 실패: {e}")

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("보고서 제목 관리 시스템 테스트")
    print("="*60)
    print()
    
    manager = ReportTitleManager()
    
    # 보고서 등록
    title1 = manager.register_report(
        report_id="RPT_001",
        original_title="삼성전자 4Q24 Preview 및 2025년 전망 - HBM 매출 본격화로 실적 호조 예상",
        keywords=["삼성전자", "4Q24", "HBM"]
    )
    
    print(f"원본 제목: {title1.original_title}")
    
    # AI 제목 생성 (간단한 버전)
    ai_title = manager.generate_ai_title(
        "RPT_001",
        metadata={
            'stock_name': '삼성전자',
            'investment_opinion': '매수'
        }
    )
    
    print(f"AI 요약 제목: {ai_title}")
    print(f"표시 제목: {title1.get_display_title()}")
    print(f"파일명 (원본): {title1.get_filename(use_ai_title=False)}")
    print(f"파일명 (AI): {title1.get_filename(use_ai_title=True)}")
    
    print("\n✅ 테스트 완료!")




