-- ================================================================
-- Phase A-1: 긴급 뉴스 알림 + 팩트 체크 시스템
-- PostgreSQL Schema
-- ================================================================

-- 1. 뉴스 메인 테이블
CREATE TABLE IF NOT EXISTS news_articles (
    article_id SERIAL PRIMARY KEY,
    
    -- 기본 정보
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT NOT NULL,
    
    -- 출처 정보
    source VARCHAR(100) NOT NULL,
    source_tier INT CHECK(source_tier IN (1, 2, 3)),
    author VARCHAR(200),
    
    -- 시간 정보
    published_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    
    -- 분류
    category VARCHAR(50),  -- 정치, 경제, 기업, 산업 등
    urgency_level INT CHECK(urgency_level BETWEEN 1 AND 5),  -- 1:일반 ~ 5:긴급
    
    -- 관련 정보
    stock_codes TEXT[],  -- 관련 종목 코드 배열
    sectors TEXT[],      -- 관련 섹터
    keywords TEXT[],     -- 키워드
    
    -- 감성 분석
    sentiment VARCHAR(20) CHECK(sentiment IN ('positive', 'negative', 'neutral')),
    sentiment_score DECIMAL(3, 2),  -- -1.0 ~ +1.0
    
    -- 신뢰도
    credibility_score DECIMAL(3, 2),  -- 0.0 ~ 1.0
    is_verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(50),
    
    -- 중복 방지
    content_hash VARCHAR(64) UNIQUE,  -- SHA256 해시
    
    -- 임베딩 (벡터 검색용) - pgvector 확장 필요
    -- embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    
    -- 메타데이터
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_news_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_source ON news_articles(source);
CREATE INDEX idx_news_urgency ON news_articles(urgency_level DESC);
CREATE INDEX idx_news_stock_codes ON news_articles USING GIN(stock_codes);
CREATE INDEX idx_news_sectors ON news_articles USING GIN(sectors);
CREATE INDEX idx_news_keywords ON news_articles USING GIN(keywords);
CREATE INDEX idx_news_hash ON news_articles(content_hash);

-- 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_news_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER news_update_timestamp
BEFORE UPDATE ON news_articles
FOR EACH ROW
EXECUTE FUNCTION update_news_timestamp();


-- 2. 팩트 체크 테이블
CREATE TABLE IF NOT EXISTS fact_checks (
    check_id SERIAL PRIMARY KEY,
    article_id INT REFERENCES news_articles(article_id),
    
    -- 검증 결과
    verification_status VARCHAR(20) CHECK(verification_status IN ('verified', 'disputed', 'false', 'unverified')),
    confidence_score DECIMAL(3, 2),  -- 0.0 ~ 1.0
    
    -- 검증 근거
    supporting_sources TEXT[],  -- 지지 소스
    contradicting_sources TEXT[],  -- 반박 소스
    
    -- LLM 분석
    llm_analysis TEXT,
    llm_reasoning TEXT,
    
    -- 교차 검증
    cross_verified_count INT DEFAULT 0,
    total_sources_checked INT DEFAULT 0,
    
    -- 과거 이력
    similar_past_events JSONB,  -- 유사 과거 사례
    past_accuracy_rate DECIMAL(3, 2),  -- 해당 소스의 과거 정확도
    
    -- 타이밍
    checked_at TIMESTAMP DEFAULT NOW(),
    rechecked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fact_article ON fact_checks(article_id);
CREATE INDEX idx_fact_status ON fact_checks(verification_status);


-- 3. 뉴스 소스 신뢰도 테이블
CREATE TABLE IF NOT EXISTS news_sources (
    source_id SERIAL PRIMARY KEY,
    
    source_name VARCHAR(100) UNIQUE NOT NULL,
    source_url TEXT,
    source_tier INT CHECK(source_tier IN (1, 2, 3)),
    
    -- 통계
    total_articles INT DEFAULT 0,
    verified_articles INT DEFAULT 0,
    false_articles INT DEFAULT 0,
    
    -- 신뢰도 지표
    accuracy_rate DECIMAL(5, 2),  -- 정확도
    speed_score DECIMAL(5, 2),    -- 속도 점수
    credibility_score DECIMAL(5, 2),  -- 종합 신뢰도
    
    -- 특성
    bias_score DECIMAL(3, 2),  -- -1.0(부정 편향) ~ +1.0(긍정 편향)
    specialization TEXT[],     -- 전문 분야
    
    -- 상태
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sources_tier ON news_sources(source_tier);
CREATE INDEX idx_sources_credibility ON news_sources(credibility_score DESC);


-- 4. 긴급 알림 로그
CREATE TABLE IF NOT EXISTS alert_logs (
    alert_id SERIAL PRIMARY KEY,
    article_id INT REFERENCES news_articles(article_id),
    
    -- 알림 정보
    alert_type VARCHAR(50),  -- 'urgent', 'breaking', 'update'
    alert_level INT CHECK(alert_level BETWEEN 1 AND 5),
    
    -- 수신자
    recipient_type VARCHAR(50),  -- 'all', 'portfolio', 'sector'
    recipient_filter JSONB,
    
    -- 전송 정보
    channels TEXT[],  -- ['websocket', 'slack', 'telegram']
    sent_at TIMESTAMP DEFAULT NOW(),
    
    -- 사용자 반응
    viewed_count INT DEFAULT 0,
    clicked_count INT DEFAULT 0,
    dismissed_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alert_article ON alert_logs(article_id);
CREATE INDEX idx_alert_sent ON alert_logs(sent_at DESC);


-- 5. 크롤링 작업 로그
CREATE TABLE IF NOT EXISTS crawl_jobs (
    job_id SERIAL PRIMARY KEY,
    
    source_name VARCHAR(100),
    job_type VARCHAR(50),  -- 'rss', 'html', 'api'
    
    -- 상태
    status VARCHAR(20) CHECK(status IN ('running', 'completed', 'failed', 'paused')),
    
    -- 통계
    items_found INT DEFAULT 0,
    items_new INT DEFAULT 0,
    items_duplicate INT DEFAULT 0,
    items_failed INT DEFAULT 0,
    
    -- 시간
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INT,
    
    -- 오류
    error_message TEXT,
    error_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crawl_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_started ON crawl_jobs(started_at DESC);


-- 6. 뉴스 클러스터 (유사 뉴스 그룹화)
CREATE TABLE IF NOT EXISTS news_clusters (
    cluster_id SERIAL PRIMARY KEY,
    
    -- 클러스터 정보
    cluster_topic VARCHAR(200),
    cluster_summary TEXT,
    
    -- 대표 뉴스
    representative_article_id INT REFERENCES news_articles(article_id),
    
    -- 통계
    article_count INT DEFAULT 0,
    source_diversity INT DEFAULT 0,  -- 소스 다양성
    
    -- 신뢰도
    consensus_score DECIMAL(3, 2),  -- 소스 간 일치도
    
    -- 시간
    first_published TIMESTAMP,
    last_updated TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 클러스터-기사 매핑
CREATE TABLE IF NOT EXISTS news_cluster_articles (
    cluster_id INT REFERENCES news_clusters(cluster_id),
    article_id INT REFERENCES news_articles(article_id),
    similarity_score DECIMAL(3, 2),
    
    PRIMARY KEY (cluster_id, article_id)
);

CREATE INDEX idx_cluster_articles ON news_cluster_articles(cluster_id);


-- 7. 실시간 트렌드
CREATE TABLE IF NOT EXISTS news_trends (
    trend_id SERIAL PRIMARY KEY,
    
    keyword VARCHAR(200) NOT NULL,
    
    -- 통계
    mention_count INT DEFAULT 0,
    unique_articles INT DEFAULT 0,
    
    -- 추세
    trend_score DECIMAL(5, 2),  -- 상승세
    velocity DECIMAL(5, 2),     -- 확산 속도
    
    -- 시간대
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    
    -- 관련 정보
    related_stocks TEXT[],
    related_sectors TEXT[],
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trends_keyword ON news_trends(keyword);
CREATE INDEX idx_trends_score ON news_trends(trend_score DESC);
CREATE INDEX idx_trends_window ON news_trends(window_start DESC);


-- ================================================================
-- 뷰 (View) 정의
-- ================================================================

-- 긴급 뉴스 뷰
CREATE OR REPLACE VIEW v_urgent_news AS
SELECT 
    na.article_id,
    na.title,
    na.summary,
    na.source,
    na.source_tier,
    na.published_at,
    na.urgency_level,
    na.stock_codes,
    na.sentiment,
    na.credibility_score,
    fc.verification_status,
    fc.confidence_score,
    ns.credibility_score AS source_credibility
FROM news_articles na
LEFT JOIN fact_checks fc ON na.article_id = fc.article_id
LEFT JOIN news_sources ns ON na.source = ns.source_name
WHERE na.urgency_level >= 4
  AND na.published_at > NOW() - INTERVAL '24 hours'
ORDER BY na.published_at DESC;


-- 소스별 통계 뷰
CREATE OR REPLACE VIEW v_source_statistics AS
SELECT 
    ns.source_name,
    ns.source_tier,
    ns.total_articles,
    ns.accuracy_rate,
    ns.credibility_score,
    COUNT(na.article_id) AS articles_today,
    AVG(na.credibility_score) AS avg_article_credibility
FROM news_sources ns
LEFT JOIN news_articles na ON ns.source_name = na.source 
    AND na.published_at > CURRENT_DATE
GROUP BY ns.source_id, ns.source_name, ns.source_tier, 
         ns.total_articles, ns.accuracy_rate, ns.credibility_score
ORDER BY ns.credibility_score DESC;


-- 종목별 최신 뉴스 뷰
CREATE OR REPLACE VIEW v_stock_latest_news AS
SELECT 
    UNNEST(stock_codes) AS stock_code,
    na.article_id,
    na.title,
    na.summary,
    na.published_at,
    na.sentiment,
    na.credibility_score,
    na.urgency_level
FROM news_articles na
WHERE na.published_at > NOW() - INTERVAL '7 days'
ORDER BY stock_code, na.published_at DESC;


-- ================================================================
-- 초기 데이터 삽입
-- ================================================================

-- 기본 뉴스 소스 등록
INSERT INTO news_sources (source_name, source_url, source_tier, credibility_score, accuracy_rate) VALUES
-- Tier 1: 공식
('한국거래소', 'https://www.krx.co.kr', 1, 0.98, 0.99),
('금융감독원', 'https://www.fss.or.kr', 1, 0.97, 0.99),
('한국은행', 'https://www.bok.or.kr', 1, 0.97, 0.99),

-- Tier 2: 속보
('연합뉴스', 'https://www.yna.co.kr', 2, 0.90, 0.92),
('네이버금융', 'https://finance.naver.com', 2, 0.85, 0.88),
('한국경제', 'https://www.hankyung.com', 2, 0.88, 0.90),
('매일경제', 'https://www.mk.co.kr', 2, 0.87, 0.89),
('38커뮤니케이션', 'http://www.38.co.kr', 2, 0.85, 0.87),

-- Tier 3: 커뮤니티
('팍스넷', 'https://www.paxnet.co.kr', 3, 0.70, 0.75),
('네이버증권토론방', 'https://finance.naver.com', 3, 0.60, 0.65)

ON CONFLICT (source_name) DO NOTHING;


-- ================================================================
-- 함수 정의
-- ================================================================

-- 신뢰도 자동 계산 함수
CREATE OR REPLACE FUNCTION calculate_credibility_score(
    p_article_id INT
) RETURNS DECIMAL(3, 2) AS $$
DECLARE
    v_source_score DECIMAL(3, 2);
    v_fact_check_score DECIMAL(3, 2);
    v_final_score DECIMAL(3, 2);
BEGIN
    -- 소스 신뢰도 가져오기
    SELECT ns.credibility_score INTO v_source_score
    FROM news_articles na
    JOIN news_sources ns ON na.source = ns.source_name
    WHERE na.article_id = p_article_id;
    
    -- 팩트 체크 점수 가져오기
    SELECT fc.confidence_score INTO v_fact_check_score
    FROM fact_checks fc
    WHERE fc.article_id = p_article_id
    ORDER BY fc.checked_at DESC
    LIMIT 1;
    
    -- 최종 점수 계산 (가중 평균)
    IF v_fact_check_score IS NOT NULL THEN
        v_final_score := (v_source_score * 0.4) + (v_fact_check_score * 0.6);
    ELSE
        v_final_score := v_source_score;
    END IF;
    
    RETURN v_final_score;
END;
$$ LANGUAGE plpgsql;


-- 긴급도 자동 판정 함수
CREATE OR REPLACE FUNCTION determine_urgency_level(
    p_title TEXT,
    p_content TEXT,
    p_keywords TEXT[]
) RETURNS INT AS $$
DECLARE
    v_urgency INT := 1;
    urgent_keywords TEXT[] := ARRAY['긴급', '속보', '중단', '급락', '급등', '사고', '화재', '사망', '사임'];
    keyword TEXT;
BEGIN
    -- 제목에 긴급 키워드 포함 여부
    FOREACH keyword IN ARRAY urgent_keywords LOOP
        IF p_title ILIKE '%' || keyword || '%' THEN
            v_urgency := 5;
            EXIT;
        END IF;
    END LOOP;
    
    -- 주가 변동 패턴 감지
    IF p_title ~* '\-[0-9]+\.?[0-9]*%' OR p_title ~* '\+[0-9]+\.?[0-9]*%' THEN
        v_urgency := GREATEST(v_urgency, 4);
    END IF;
    
    RETURN v_urgency;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- 완료 메시지
-- ================================================================

DO $$ 
BEGIN
    RAISE NOTICE 'News Ingestion Schema Created Successfully!';
    RAISE NOTICE 'Tables: 8개 생성';
    RAISE NOTICE 'Views: 3개 생성';
    RAISE NOTICE 'Functions: 2개 생성';
END $$;



