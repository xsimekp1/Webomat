-- Migration 003: Create version_comments and preview_share_links tables
-- Enables client feedback on website previews

-- Version Comments table
CREATE TABLE IF NOT EXISTS version_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES website_versions(id) ON DELETE CASCADE,
    author_type VARCHAR(20) NOT NULL CHECK (author_type IN ('client', 'internal')),
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    access_token VARCHAR(64), -- Token used when submitting (for client comments)
    content TEXT NOT NULL,
    -- Anchor information for positioning comments on the page
    anchor_type VARCHAR(20) CHECK (anchor_type IN ('element', 'coordinates', 'general')),
    anchor_selector TEXT, -- CSS selector for element-based anchoring
    anchor_x DECIMAL(10,2), -- X coordinate (percentage or pixels)
    anchor_y DECIMAL(10,2), -- Y coordinate (percentage or pixels)
    -- Status tracking
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'acknowledged', 'resolved', 'rejected')),
    resolved_by UUID REFERENCES sellers(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Preview Share Links table
CREATE TABLE IF NOT EXISTS preview_share_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES website_versions(id) ON DELETE CASCADE,
    token VARCHAR(64) NOT NULL UNIQUE, -- Secure random token
    expires_at TIMESTAMP WITH TIME ZONE,
    view_count INTEGER DEFAULT 0,
    max_views INTEGER, -- NULL means unlimited
    is_active BOOLEAN DEFAULT TRUE,
    -- Metadata
    created_by UUID REFERENCES sellers(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_viewed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_version_comments_version ON version_comments(version_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_version_comments_status ON version_comments(status);
CREATE INDEX IF NOT EXISTS idx_version_comments_author_type ON version_comments(author_type);

CREATE INDEX IF NOT EXISTS idx_preview_share_links_token ON preview_share_links(token);
CREATE INDEX IF NOT EXISTS idx_preview_share_links_version ON preview_share_links(version_id);
CREATE INDEX IF NOT EXISTS idx_preview_share_links_active ON preview_share_links(is_active, expires_at);

-- Function to increment view count and update last_viewed_at
CREATE OR REPLACE FUNCTION increment_preview_view_count(link_token VARCHAR(64))
RETURNS BOOLEAN AS $$
DECLARE
    link_record RECORD;
BEGIN
    SELECT * INTO link_record
    FROM preview_share_links
    WHERE token = link_token
      AND is_active = TRUE
      AND (expires_at IS NULL OR expires_at > NOW())
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Check max views
    IF link_record.max_views IS NOT NULL AND link_record.view_count >= link_record.max_views THEN
        RETURN FALSE;
    END IF;

    -- Update view count
    UPDATE preview_share_links
    SET view_count = view_count + 1,
        last_viewed_at = NOW()
    WHERE id = link_record.id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE version_comments IS 'Comments/feedback on website versions from clients or internal team';
COMMENT ON TABLE preview_share_links IS 'Shareable links for client preview access';
COMMENT ON COLUMN version_comments.anchor_type IS 'How the comment is anchored: element (CSS selector), coordinates (x/y), or general';
COMMENT ON COLUMN preview_share_links.token IS 'Secure 64-character token for URL access';
