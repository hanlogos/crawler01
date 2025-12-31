# 🗄️ PostgreSQL DB 설정 가이드

## 📋 개요

통합 검색 시스템 (a+b+c)을 사용하려면 PostgreSQL 데이터베이스가 필요합니다.

---

## 🚀 빠른 설정

### 1. PostgreSQL 설치 확인

```bash
# Windows (PowerShell)
Get-Service -Name postgresql*

# Linux/Mac
sudo systemctl status postgresql
```

### 2. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE abiseu;

# 접속 확인
\c abiseu
```

### 3. 스키마 적용

```bash
# 스키마 파일 실행
psql -U postgres -d abiseu -f news_ingestion_schema.sql
```

또는 psql 내에서:
```sql
\c abiseu
\i news_ingestion_schema.sql
```

### 4. 환경변수 설정

**Windows (PowerShell):**
```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "abiseu"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "your_password"
```

**Linux/Mac:**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=abiseu
export DB_USER=postgres
export DB_PASSWORD=your_password
```

**영구 설정 (Windows):**
```powershell
[System.Environment]::SetEnvironmentVariable('DB_PASSWORD', 'your_password', 'User')
```

---

## 🔧 대시보드에서 사용

### 방법 1: 환경변수 사용 (권장)

```powershell
# PowerShell에서 실행
$env:DB_PASSWORD = "your_password"
python enhanced_crawling_dashboard.py
```

### 방법 2: 코드에서 직접 설정

`enhanced_crawling_dashboard.py` 파일 수정:

```python
# 720번째 줄 근처
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'abiseu',
    'user': 'postgres',
    'password': 'your_password'  # 여기에 비밀번호 입력
}
```

---

## ✅ 확인 방법

### 1. DB 연결 테스트

```python
import psycopg2

DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'abiseu',
    'user': 'postgres',
    'password': 'your_password'
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    print("✅ DB 연결 성공!")
    conn.close()
except Exception as e:
    print(f"❌ DB 연결 실패: {e}")
```

### 2. 대시보드에서 확인

1. 대시보드 실행
2. "🔍 키워드 검색" 탭 선택
3. "검색 모드" 드롭다운 확인
   - "통합 검색 (a+b+c)" 옵션이 활성화되어 있으면 ✅
   - 비활성화되어 있으면 DB 연결 필요

---

## 📊 데이터 수집

DB가 설정되면 뉴스 수집 서비스를 실행하여 데이터를 수집합니다:

```bash
# 뉴스 수집 서비스 실행
python news_ingestion_service.py
```

이 서비스는:
- 뉴스를 크롤링하여 DB에 저장
- 팩트 체크 수행
- 긴급 뉴스 알림

---

## 🐛 트러블슈팅

### 1. "connection refused" 오류

```bash
# PostgreSQL 서비스 시작
# Windows
net start postgresql-x64-14

# Linux
sudo systemctl start postgresql
```

### 2. "password authentication failed"

- 비밀번호 확인
- `pg_hba.conf` 설정 확인

### 3. "database does not exist"

```sql
CREATE DATABASE abiseu;
```

### 4. "relation does not exist"

스키마가 적용되지 않음:
```bash
psql -U postgres -d abiseu -f news_ingestion_schema.sql
```

---

## 📝 요약

1. ✅ PostgreSQL 설치 및 실행
2. ✅ `abiseu` 데이터베이스 생성
3. ✅ `news_ingestion_schema.sql` 스키마 적용
4. ✅ 환경변수 `DB_PASSWORD` 설정
5. ✅ 대시보드 실행 → "통합 검색" 모드 선택

**완료되면 a+b+c 모든 기능 사용 가능!**


