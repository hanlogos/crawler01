-- ================================================================
-- 애널리스트 리포트 스냅샷 저장 테이블
-- KoreaAnalystSnapshot v1 형식 데이터 저장
-- ================================================================

-- 애널리스트 리포트 테이블
CREATE TABLE IF NOT EXISTS analyst_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 기본 정보
    source VARCHAR(50) NOT NULL,  -- '38com', 'hankyung', 'naver', 'finnhub', 'fmp' 등
    source_url TEXT UNIQUE,  -- 중복 방지용 (unique key)
    
    -- 종목 정보
    stock_code VARCHAR(10) NOT NULL,  -- 6자리 종목 코드 또는 심볼
    stock_name VARCHAR(200),
    market VARCHAR(20),  -- 'KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE' 등
    
    -- 리포트 정보
    published_at DATE NOT NULL,  -- 리포트 발행일
    title TEXT,  -- 리포트 제목
    
    -- 투자 의견
    opinion VARCHAR(50),  -- 'Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell'
    target_price DECIMAL(15, 2),  -- 목표주가
    
    -- 애널리스트 정보
    analyst_name VARCHAR(100),
    analyst_firm VARCHAR(100),
    
    -- 신뢰도
    trust_score DECIMAL(3, 2),  -- 0.0 ~ 1.0 (source_quality)
    
    -- 구조화된 데이터 (JSONB)
    structured_data JSONB,  -- KoreaAnalystSnapshot v1 전체 데이터
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_analyst_stock_code ON analyst_reports(stock_code);
CREATE INDEX IF NOT EXISTS idx_analyst_published ON analyst_reports(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyst_source ON analyst_reports(source);
CREATE INDEX IF NOT EXISTS idx_analyst_opinion ON analyst_reports(opinion);
CREATE INDEX IF NOT EXISTS idx_analyst_firm ON analyst_reports(analyst_firm);
CREATE INDEX IF NOT EXISTS idx_analyst_url ON analyst_reports(source_url);

-- JSONB 인덱스 (structured_data 내부 필드 검색용)
CREATE INDEX IF NOT EXISTS idx_analyst_structured_recommendation 
    ON analyst_reports USING GIN ((structured_data->'recommendation'));
CREATE INDEX IF NOT EXISTS idx_analyst_structured_price_target 
    ON analyst_reports USING GIN ((structured_data->'price_target'));

-- 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_analyst_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER analyst_update_timestamp
BEFORE UPDATE ON analyst_reports
FOR EACH ROW
EXECUTE FUNCTION update_analyst_timestamp();

-- 컨센서스 조회 뷰 (최근 N일 리포트 집계)
CREATE OR REPLACE VIEW v_analyst_consensus AS
SELECT 
    stock_code,
    stock_name,
    COUNT(*) as total_reports,
    AVG(target_price) as avg_target_price,
    MIN(target_price) as min_target_price,
    MAX(target_price) as max_target_price,
    AVG(trust_score) as avg_trust_score,
    MAX(published_at) as latest_date,
    -- 의견 분포
    COUNT(*) FILTER (WHERE opinion = 'Strong Buy') as strong_buy_count,
    COUNT(*) FILTER (WHERE opinion = 'Buy') as buy_count,
    COUNT(*) FILTER (WHERE opinion = 'Hold') as hold_count,
    COUNT(*) FILTER (WHERE opinion = 'Sell') as sell_count,
    COUNT(*) FILTER (WHERE opinion = 'Strong Sell') as strong_sell_count
FROM analyst_reports
WHERE published_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY stock_code, stock_name;

