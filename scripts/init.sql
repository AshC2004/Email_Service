-- Email Delivery Service Database Schema
-- Run on initial setup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_prefix VARCHAR(12) NOT NULL,
    key_hash VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rate_limit_per_minute INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(32) UNIQUE NOT NULL,
    api_key_id UUID REFERENCES api_keys(id),
    
    -- Email fields
    to_email VARCHAR(255) NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    body_html TEXT,
    body_text TEXT,
    reply_to VARCHAR(255),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'queued',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    last_error TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    queued_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

-- Email events table (for tracking history)
CREATE TABLE IF NOT EXISTS email_events (
    id BIGSERIAL PRIMARY KEY,
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_api_key ON emails(api_key_id);
CREATE INDEX IF NOT EXISTS idx_emails_created ON emails(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id);
CREATE INDEX IF NOT EXISTS idx_events_email_id ON email_events(email_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON email_events(created_at DESC);

-- Insert a test API key (key: sk_test_demo123456789)
-- Hash is SHA256 of the full key with salt
INSERT INTO api_keys (key_prefix, key_hash, name, rate_limit_per_minute)
VALUES (
    'sk_test_demo',
    'a]demo_hash_replace_with_real_hash',
    'Test API Key',
    100
) ON CONFLICT DO NOTHING;
