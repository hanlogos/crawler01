# Ollama 연동 가이드

## 1. Ollama 서버 실행

### Windows
1. **방법 1: Ollama 앱 실행**
   - Ollama 앱을 실행하면 자동으로 서버가 시작됩니다.

2. **방법 2: 명령줄 실행**
   ```bash
   ollama serve
   ```
   
   또는 백그라운드에서 실행:
   ```bash
   start ollama serve
   ```

### Linux/Mac
```bash
ollama serve
```

## 2. 모델 다운로드

처음 사용 시 모델을 다운로드해야 합니다:

```bash
# Llama 3 (권장)
ollama pull llama3

# 또는 다른 모델
ollama pull mistral
ollama pull codellama
ollama pull gemma
```

다운로드된 모델 확인:
```bash
ollama list
```

## 3. 연결 테스트

```bash
python test_ollama_integration.py
```

또는 간단한 테스트:
```bash
python ollama_llm.py
```

## 4. 통합 크롤러에서 사용

### 방법 1: 스크립트 실행
```bash
python run_crawler_with_ollama.py
```

### 방법 2: 코드에서 직접 사용
```python
from crawler_with_analysis import IntegratedCrawler

# Ollama 사용
crawler = IntegratedCrawler(
    use_analysis=True,
    use_ollama=True,  # Ollama 사용
    ollama_model="llama3"  # 모델 이름
)

results = crawler.crawl_and_analyze(days=1, max_reports=5)
```

## 5. 문제 해결

### Ollama 서버에 연결할 수 없음
- **해결**: Ollama 서버가 실행 중인지 확인
  ```bash
  # Windows
  tasklist | findstr ollama
  
  # Linux/Mac
  ps aux | grep ollama
  ```

### 모델을 찾을 수 없음
- **해결**: 모델 다운로드
  ```bash
  ollama pull llama3
  ```

### 응답이 너무 느림
- **원인**: 모델이 크거나 컴퓨터 성능이 낮을 수 있음
- **해결**: 더 작은 모델 사용
  ```bash
  ollama pull gemma:2b  # 작은 모델
  ```

### 타임아웃 오류
- **해결**: `ollama_llm.py`에서 `timeout` 값 증가
  ```python
  llm = OllamaLLM(model="llama3", timeout=300)  # 5분
  ```

## 6. 사용 가능한 모델

### 추천 모델
- **llama3**: 범용, 좋은 성능
- **mistral**: 빠르고 효율적
- **codellama**: 코드 생성에 특화

### 작은 모델 (빠르지만 성능 낮음)
- **gemma:2b**: 매우 작고 빠름
- **llama3:8b**: 중간 크기

### 큰 모델 (느리지만 성능 높음)
- **llama3:70b**: 매우 큰 모델 (고성능 PC 필요)

## 7. 성능 최적화

### GPU 사용 (NVIDIA)
Ollama는 자동으로 GPU를 사용합니다. CUDA가 설치되어 있으면 자동으로 활용됩니다.

### 메모리 관리
- 큰 모델은 많은 RAM을 사용합니다
- 8GB RAM: gemma:2b, llama3:8b 권장
- 16GB+ RAM: llama3:70b 가능

## 8. API 엔드포인트

Ollama는 다음 API를 제공합니다:
- **기본 URL**: `http://localhost:11434`
- **모델 목록**: `GET /api/tags`
- **생성**: `POST /api/generate`
- **채팅**: `POST /api/chat`

자세한 내용은 [Ollama 공식 문서](https://github.com/ollama/ollama) 참조




