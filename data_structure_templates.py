# data_structure_templates.py
"""
데이터 구조 템플릿 및 AI 제안 시스템

추출한 데이터의 구조를 정의하고 AI가 제안하는 옵션 제공
"""

import sys
import io
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class FieldDefinition:
    """필드 정의"""
    name: str
    type: str  # 'string', 'number', 'date', 'boolean', 'list', 'dict'
    required: bool
    default_value: Any = None
    description: str = ""
    examples: List[Any] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []

@dataclass
class DataStructureTemplate:
    """데이터 구조 템플릿"""
    name: str
    description: str
    fields: List[FieldDefinition]
    version: str = "1.0"
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """필드 가져오기"""
        return next((f for f in self.fields if f.name == name), None)
    
    def validate(self, data: Dict) -> tuple[bool, List[str]]:
        """데이터 검증"""
        errors = []
        
        for field in self.fields:
            if field.required and field.name not in data:
                errors.append(f"필수 필드 누락: {field.name}")
            elif field.name in data:
                # 타입 검증
                value = data[field.name]
                if not self._check_type(value, field.type):
                    errors.append(f"필드 타입 오류: {field.name} (예상: {field.type}, 실제: {type(value).__name__})")
        
        return len(errors) == 0, errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """타입 확인"""
        type_map = {
            'string': str,
            'number': (int, float),
            'date': (str, datetime),
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        
        if isinstance(expected, tuple):
            return isinstance(value, expected)
        return isinstance(value, expected)

class DataStructureManager:
    """데이터 구조 관리자"""
    
    def __init__(self):
        self.templates: Dict[str, DataStructureTemplate] = {}
        self.logger = logging.getLogger(__name__)
        self._load_default_templates()
    
    def _load_default_templates(self):
        """기본 템플릿 로드"""
        
        # 리포트 메타데이터 템플릿
        report_template = DataStructureTemplate(
            name="report_metadata",
            description="증권 리포트 메타데이터",
            fields=[
                FieldDefinition("report_id", "string", True, "", "보고서 고유 ID"),
                FieldDefinition("title", "string", True, "", "보고서 제목"),
                FieldDefinition("stock_code", "string", True, "", "종목 코드 (6자리)"),
                FieldDefinition("stock_name", "string", True, "", "종목명"),
                FieldDefinition("analyst_name", "string", True, "", "애널리스트 이름"),
                FieldDefinition("firm", "string", True, "", "증권사명"),
                FieldDefinition("published_date", "date", True, None, "발행일"),
                FieldDefinition("source_url", "string", True, "", "원본 URL"),
                FieldDefinition("investment_opinion", "string", False, None, "투자의견 (buy/hold/sell)"),
                FieldDefinition("target_price", "number", False, None, "목표가"),
            ],
            version="1.0"
        )
        self.templates["report_metadata"] = report_template
        
        # 리포트 상세 정보 템플릿
        report_detail_template = DataStructureTemplate(
            name="report_detail",
            description="증권 리포트 상세 정보",
            fields=[
                FieldDefinition("report_id", "string", True, "", "보고서 고유 ID"),
                FieldDefinition("content", "string", True, "", "본문 내용"),
                FieldDefinition("financial_metrics", "dict", False, {}, "재무 지표"),
                FieldDefinition("trading_signals", "dict", False, {}, "매매 신호"),
                FieldDefinition("risks", "list", False, [], "리스크 목록"),
                FieldDefinition("sentiment", "dict", False, {}, "시장 심리"),
                FieldDefinition("events", "list", False, [], "주요 이벤트"),
            ],
            version="1.0"
        )
        self.templates["report_detail"] = report_detail_template
        
        # 종목 정보 템플릿
        stock_template = DataStructureTemplate(
            name="stock_info",
            description="종목 기본 정보",
            fields=[
                FieldDefinition("stock_code", "string", True, "", "종목 코드"),
                FieldDefinition("stock_name", "string", True, "", "종목명"),
                FieldDefinition("market", "string", False, "KOSPI", "시장 (KOSPI/KOSDAQ)"),
                FieldDefinition("sector", "string", False, "", "섹터"),
                FieldDefinition("industry", "string", False, "", "업종"),
            ],
            version="1.0"
        )
        self.templates["stock_info"] = stock_template
    
    def register_template(self, template: DataStructureTemplate):
        """템플릿 등록"""
        self.templates[template.name] = template
        self.logger.info(f"템플릿 등록: {template.name}")
    
    def get_template(self, name: str) -> Optional[DataStructureTemplate]:
        """템플릿 가져오기"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """템플릿 목록"""
        return list(self.templates.keys())
    
    def suggest_fields(self, data: Dict, template_name: Optional[str] = None) -> List[Dict]:
        """필드 제안 (AI 기반)"""
        
        suggestions = []
        
        # 템플릿 기반 제안
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
            
            for field in template.fields:
                if field.name not in data:
                    suggestions.append({
                        'field': field.name,
                        'type': field.type,
                        'required': field.required,
                        'default': field.default_value,
                        'description': field.description,
                        'reason': '템플릿에 정의된 필드' if field.required else '템플릿에 정의된 선택 필드'
                    })
        
        # 데이터 기반 제안 (추가 필드 발견)
        common_fields = {
            'category': {'type': 'string', 'description': '카테고리'},
            'tags': {'type': 'list', 'description': '태그 목록'},
            'summary': {'type': 'string', 'description': '요약'},
            'keywords': {'type': 'list', 'description': '키워드 목록'},
            'related_reports': {'type': 'list', 'description': '관련 보고서 ID 목록'},
        }
        
        for field_name, field_info in common_fields.items():
            if field_name not in data:
                suggestions.append({
                    'field': field_name,
                    'type': field_info['type'],
                    'required': False,
                    'default': None,
                    'description': field_info['description'],
                    'reason': '일반적으로 유용한 필드'
                })
        
        return suggestions
    
    def extract_structure(self, data: Dict) -> Dict:
        """데이터에서 구조 추출"""
        
        structure = {
            'fields': [],
            'nested_structures': {}
        }
        
        for key, value in data.items():
            field_type = self._infer_type(value)
            
            field_info = {
                'name': key,
                'type': field_type,
                'required': value is not None,
                'default': value if value is not None else None
            }
            
            structure['fields'].append(field_info)
            
            # 중첩 구조 처리
            if field_type == 'dict' and isinstance(value, dict):
                structure['nested_structures'][key] = self.extract_structure(value)
            elif field_type == 'list' and isinstance(value, list) and value:
                # 리스트의 첫 번째 요소로 타입 추론
                if isinstance(value[0], dict):
                    structure['nested_structures'][f'{key}_item'] = self.extract_structure(value[0])
        
        return structure
    
    def _infer_type(self, value: Any) -> str:
        """값에서 타입 추론"""
        
        if value is None:
            return 'string'  # 기본값
        
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'number'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            # 날짜 형식 확인
            if self._is_date(value):
                return 'date'
            return 'string'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        
        return 'string'
    
    def _is_date(self, value: str) -> bool:
        """날짜 형식 확인"""
        import re
        date_patterns = [
            r'\d{4}[./-]\d{1,2}[./-]\d{1,2}',
            r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, value):
                return True
        
        return False

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("데이터 구조 템플릿 시스템 테스트")
    print("="*60)
    print()
    
    manager = DataStructureManager()
    
    # 템플릿 목록
    print("등록된 템플릿:")
    for name in manager.list_templates():
        template = manager.get_template(name)
        print(f"  - {name}: {template.description} ({len(template.fields)}개 필드)")
    
    # 템플릿 사용
    print("\n리포트 메타데이터 템플릿:")
    template = manager.get_template("report_metadata")
    
    # 필드 목록
    print("필드 목록:")
    for field in template.fields:
        req = "필수" if field.required else "선택"
        print(f"  - {field.name} ({field.type}, {req}): {field.description}")
    
    # 데이터 검증
    print("\n데이터 검증 테스트:")
    test_data = {
        "report_id": "RPT_001",
        "title": "삼성전자 리포트",
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "analyst_name": "홍길동",
        "firm": "삼성증권",
        "published_date": "2024-12-30",
        "source_url": "http://example.com",
        "investment_opinion": "buy",
        "target_price": 75000
    }
    
    is_valid, errors = template.validate(test_data)
    print(f"검증 결과: {'✅ 통과' if is_valid else '❌ 실패'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # 필드 제안
    print("\n필드 제안:")
    incomplete_data = {
        "report_id": "RPT_002",
        "title": "SK하이닉스 리포트"
    }
    
    suggestions = manager.suggest_fields(incomplete_data, "report_metadata")
    print(f"{len(suggestions)}개 제안:")
    for sug in suggestions[:5]:
        req = "필수" if sug['required'] else "선택"
        print(f"  - {sug['field']} ({sug['type']}, {req}): {sug['description']}")
        print(f"    이유: {sug['reason']}")
    
    # 구조 추출
    print("\n데이터 구조 추출:")
    structure = manager.extract_structure(test_data)
    print(f"필드 수: {len(structure['fields'])}")
    for field in structure['fields'][:5]:
        print(f"  - {field['name']}: {field['type']}")
    
    print("\n✅ 테스트 완료!")


