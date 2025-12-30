# enhanced_bot_evasion.py
"""
향상된 봇 탐지 회피

참고 파일의 BotEvasion 기능 통합
- User-Agent 로테이션
- Referer 관리
- 헤더 랜덤화
"""

import random
from typing import Optional

class EnhancedBotEvasion:
    """
    향상된 봇 탐지 회피
    
    - User-Agent 로테이션
    - Referer 추가
    - 쿠키 관리
    - 헤더 랜덤화
    """
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, site_url: str):
        self.site_url = site_url
        self.current_ua_index = 0
        self.last_url: Optional[str] = None
    
    def get_headers(self) -> dict:
        """요청 헤더 생성"""
        
        # User-Agent 로테이션
        user_agent = self.USER_AGENTS[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.USER_AGENTS)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Referer 추가 (두 번째 요청부터)
        if self.last_url:
            headers['Referer'] = self.last_url
        
        return headers
    
    def record_url(self, url: str):
        """URL 기록 (다음 요청의 Referer로 사용)"""
        self.last_url = url


