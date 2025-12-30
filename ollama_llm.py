# ollama_llm.py
"""
Ollama LLM 프로세서

로컬 Ollama 서버와 연동하여 LLM 사용
"""

import requests
import json
import time
import logging
from typing import Optional

class OllamaLLM:
    """Ollama LLM 프로세서"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 120
    ):
        """
        초기화
        
        Args:
            base_url: Ollama 서버 URL
            model: 사용할 모델 이름 (llama3, mistral, codellama 등)
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # 연결 테스트
        self._test_connection()
    
    def _test_connection(self):
        """Ollama 서버 연결 테스트"""
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                self.logger.info(f"✅ Ollama 서버 연결 성공")
                self.logger.info(f"   사용 가능한 모델: {', '.join(model_names[:5])}")
                
                # 지정된 모델이 있는지 확인
                if not any(self.model in name for name in model_names):
                    self.logger.warning(
                        f"⚠️  모델 '{self.model}'을 찾을 수 없습니다. "
                        f"사용 가능한 모델 중 하나를 사용하거나 'ollama pull {self.model}'로 다운로드하세요."
                    )
                    if model_names:
                        self.logger.info(f"   대신 '{model_names[0]}' 모델을 사용합니다.")
                        self.model = model_names[0].split(':')[0]  # 태그 제거
            else:
                self.logger.error(f"❌ Ollama 서버 응답 오류: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.logger.error(
                f"❌ Ollama 서버에 연결할 수 없습니다.\n"
                f"   서버가 실행 중인지 확인하세요: 'ollama serve' 또는 Ollama 앱 실행"
            )
        except Exception as e:
            self.logger.error(f"❌ 연결 테스트 실패: {e}")
    
    def process(self, prompt: str) -> str:
        """
        프롬프트 처리
        
        Args:
            prompt: 입력 프롬프트
        
        Returns:
            LLM 응답 텍스트
        """
        
        self.logger.info(f"🤖 Ollama LLM 처리 시작 (모델: {self.model})...")
        start_time = time.time()
        
        try:
            # Ollama API 호출
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,  # 스트리밍 비활성화 (전체 응답 한번에 받기)
                    "options": {
                        "temperature": 0.3,  # 일관성 있는 응답을 위해 낮은 temperature
                        "top_p": 0.9,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API 오류: {response.status_code}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            result = response.json()
            
            # 응답 추출
            if 'response' in result:
                output = result['response']
            else:
                output = str(result)
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ LLM 처리 완료 ({elapsed:.2f}초)")
            
            return output
            
        except requests.exceptions.Timeout:
            error_msg = f"요청 타임아웃 ({self.timeout}초 초과)"
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = "Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            self.logger.error(f"❌ LLM 처리 실패: {e}")
            raise
    
    def list_models(self) -> list:
        """사용 가능한 모델 목록 조회"""
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m.get('name', '') for m in models]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"모델 목록 조회 실패: {e}")
            return []

# ============================================================
# 사용 예제
# ============================================================

if __name__ == "__main__":
    import sys
    import io
    
    # Windows 콘솔 인코딩 설정
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Ollama LLM 테스트")
    print("="*60)
    print()
    
    # Ollama LLM 초기화
    try:
        llm = OllamaLLM(model="llama3")
        
        # 사용 가능한 모델 확인
        models = llm.list_models()
        if models:
            print(f"\n📋 사용 가능한 모델: {len(models)}개")
            for model in models[:5]:
                print(f"   - {model}")
        
        # 간단한 테스트
        print("\n🤖 테스트 프롬프트 처리 중...")
        test_prompt = "안녕하세요. 간단히 자기소개 해주세요."
        response = llm.process(test_prompt)
        
        print(f"\n✅ 응답:")
        print(f"{response}")
        
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        print("\n💡 해결 방법:")
        print("   1. Ollama 서버가 실행 중인지 확인: 'ollama serve'")
        print("   2. 모델이 설치되어 있는지 확인: 'ollama list'")
        print("   3. 모델이 없다면 다운로드: 'ollama pull llama3'")

