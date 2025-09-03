-- ============================================================================
-- SMARTSUPPORT AGENT DATABASE SCHEMA FOR TiDB SERVERLESS
-- Optimized for vector search, analytics, and multi-step agent workflows
-- ============================================================================

-- Main tickets table with vector embeddings
CREATE TABLE tickets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Basic ticket information
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium',
    status ENUM('new', 'processing', 'resolved', 'escalated', 'closed') NOT NULL DEFAULT 'new',
    
    -- User information
    user_id VARCHAR(100),
    user_email VARCHAR(255),
    user_type ENUM('customer', 'internal', 'partner') DEFAULT 'customer',
    
    -- Resolution information
    resolution TEXT,
    resolved_by VARCHAR(100), -- agent name or 'smartsupport_agent'
    resolution_type ENUM('automated', 'human', 'escalated') DEFAULT 'automated',
    
    -- Agent processing metadata
    agent_confidence DECIMAL(5,4), -- 0.0000 to 1.0000
    processing_duration_ms INT,
    similar_cases_found INT DEFAULT 0,
    kb_articles_used INT DEFAULT 0,
    
    -- Vector embeddings (OpenAI text-embedding-3-large = 3072 dimensions)
    title_vector VECTOR(3072) COMMENT 'Vector embedding of ticket title',
    description_vector VECTOR(3072) COMMENT 'Vector embedding of ticket description',
    combined_vector VECTOR(3072) COMMENT 'Combined title+description embedding',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    -- Indexes for performance
    INDEX idx_status_priority (status, priority),
    INDEX idx_category_status (category, status),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    INDEX idx_resolution_type (resolution_type),
    
    -- Vector search indexes (TiDB's specialized vector indexes)
    VECTOR INDEX vector_idx_title (title_vector),
    VECTOR INDEX vector_idx_description (description_vector), 
    VECTOR INDEX vector_idx_combined (combined_vector)
);

-- Knowledge base articles with vector embeddings
CREATE TABLE kb_articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Article content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category VARCHAR(100) NOT NULL,
    tags JSON, -- Array of tags for flexible categorization
    
    -- Source information
    source_url VARCHAR(1000),
    source_type ENUM('manual', 'crawled', 'imported') NOT NULL,
    author VARCHAR(255),
    
    -- Usage analytics
    view_count INT DEFAULT 0,
    helpful_votes INT DEFAULT 0,
    unhelpful_votes INT DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Vector embeddings
    title_vector VECTOR(3072),
    content_vector VECTOR(3072),
    summary_vector VECTOR(3072),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_category (category),
    INDEX idx_source_type (source_type),
    INDEX idx_updated_at (updated_at),
    FULLTEXT INDEX ft_content (title, content, summary),
    
    -- Vector indexes
    VECTOR INDEX vector_idx_kb_title (title_vector),
    VECTOR INDEX vector_idx_kb_content (content_vector),
    VECTOR INDEX vector_idx_kb_summary (summary_vector)
);

-- Agent workflow execution logs
CREATE TABLE agent_workflows (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticket_id BIGINT NOT NULL,
    
    -- Workflow execution data
    workflow_steps JSON NOT NULL, -- Array of step objects with timing/results
    total_duration_ms INT NOT NULL,
    final_confidence DECIMAL(5,4),
    
    -- Results
    similar_cases_found JSON, -- Array of similar case IDs and scores
    kb_articles_used JSON, -- Array of KB article IDs and relevance scores
    actions_executed JSON, -- Array of executed actions and results
    
    -- Status
    status ENUM('running', 'completed', 'failed', 'cancelled') NOT NULL,
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    -- Foreign key
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    
    -- Indexes
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- Similar cases mapping (for caching and analytics)
CREATE TABLE similar_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_ticket_id BIGINT NOT NULL,
    similar_ticket_id BIGINT NOT NULL,
    
    -- Similarity metrics
    vector_similarity DECIMAL(6,5) NOT NULL, -- Cosine similarity score
    text_similarity DECIMAL(6,5), -- Full-text search score
    combined_score DECIMAL(6,5) NOT NULL, -- Weighted combination
    
    -- Context
    search_context VARCHAR(100), -- 'initial', 'contextual', 'temporal', etc.
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (source_ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (similar_ticket_id) REFERENCES tickets(id),
    
    -- Indexes
    INDEX idx_source_ticket (source_ticket_id),
    INDEX idx_similarity_score (combined_score DESC),
    INDEX idx_search_context (search_context)
);

-- External tool integrations and results
CREATE TABLE external_actions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workflow_id BIGINT NOT NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL, -- 'slack_notify', 'email_send', 'ticket_resolve', etc.
    action_parameters JSON NOT NULL,
    
    -- Execution results
    status ENUM('pending', 'success', 'failed', 'cancelled') NOT NULL,
    result_data JSON,
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    duration_ms INT,
    
    -- Foreign key
    FOREIGN KEY (workflow_id) REFERENCES agent_workflows(id),
    
    -- Indexes
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_action_type (action_type),
    INDEX idx_status (status)
);

-- User interaction history (for personalization)
CREATE TABLE user_interactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- User identification
    user_id VARCHAR(100) NOT NULL,
    user_email VARCHAR(255),
    
    -- Interaction details
    interaction_type ENUM('ticket_created', 'resolution_feedback', 'kb_access', 'agent_rating') NOT NULL,
    ticket_id BIGINT,
    kb_article_id BIGINT,
    
    -- Interaction data
    feedback_score INT, -- 1-5 rating
    feedback_text TEXT,
    interaction_data JSON, -- Flexible data storage
    
    -- Context
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    session_id VARCHAR(100),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (kb_article_id) REFERENCES kb_articles(id),
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_interaction_type (interaction_type),
    INDEX idx_created_at (created_at),
    INDEX idx_ticket_id (ticket_id)
);

-- Performance metrics and analytics (pre-computed for dashboard)
CREATE TABLE performance_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Time period
    metric_date DATE NOT NULL,
    metric_hour TINYINT, -- NULL for daily metrics, 0-23 for hourly
    
    -- Metrics
    tickets_processed INT DEFAULT 0,
    tickets_auto_resolved INT DEFAULT 0,
    tickets_escalated INT DEFAULT 0,
    avg_confidence_score DECIMAL(5,4),
    avg_processing_time_ms INT,
    avg_resolution_time_hours DECIMAL(8,2),
    
    -- Quality metrics
    customer_satisfaction_avg DECIMAL(3,2), -- 1.00 to 5.00
    resolution_accuracy_rate DECIMAL(5,4), -- Percentage of correct auto-resolutions
    
    -- Category breakdown (JSON for flexibility)
    category_breakdown JSON, -- {"technical": 45, "billing": 23, "general": 12}
    priority_breakdown JSON, -- {"high": 5, "medium": 30, "low": 65}
    
    -- Cost savings
    estimated_time_saved_hours DECIMAL(8,2),
    estimated_cost_saved DECIMAL(10,2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE KEY unique_metric_period (metric_date, metric_hour),
    
    -- Indexes
    INDEX idx_metric_date (metric_date),
    INDEX idx_metric_hour (metric_hour)
);

-- System configuration and feature flags
CREATE TABLE system_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Configuration
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSON NOT NULL,
    config_type ENUM('string', 'number', 'boolean', 'object', 'array') NOT NULL,
    
    -- Metadata
    description TEXT,
    category VARCHAR(50), -- 'agent', 'search', 'integrations', etc.
    is_sensitive BOOLEAN DEFAULT FALSE, -- For passwords, API keys, etc.
    
    -- Versioning
    version INT DEFAULT 1,
    previous_value JSON,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_category (category),
    INDEX idx_updated_at (updated_at)
);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Dashboard metrics view (real-time)
CREATE VIEW dashboard_metrics AS
SELECT 
    -- Today's metrics
    COUNT(CASE WHEN DATE(created_at) = CURDATE() THEN 1 END) as tickets_today,
    COUNT(CASE WHEN DATE(resolved_at) = CURDATE() AND resolution_type = 'automated' THEN 1 END) as auto_resolved_today,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as currently_processing,
    
    -- Overall performance
    AVG(CASE WHEN status = 'resolved' THEN agent_confidence END) as avg_confidence,
    AVG(CASE WHEN status = 'resolved' THEN processing_duration_ms END) as avg_processing_time_ms,
    AVG(CASE WHEN status = 'resolved' THEN TIMESTAMPDIFF(HOUR, created_at, resolved_at) END) as avg_resolution_hours,
    
    -- Success rates
    COUNT(CASE WHEN resolution_type = 'automated' THEN 1 END) * 100.0 / COUNT(*) as automation_rate,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) * 100.0 / COUNT(*) as resolution_rate
FROM tickets
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Active tickets requiring attention
CREATE VIEW active_tickets AS
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority,
    t.status,
    t.created_at,
    t.agent_confidence,
    aw.status as workflow_status,
    aw.error_message,
    -- Time since creation
    TIMESTAMPDIFF(MINUTE, t.created_at, NOW()) as age_minutes,
    -- SLA breach indicator
    CASE 
        WHEN t.priority = 'urgent' AND TIMESTAMPDIFF(HOUR, t.created_at, NOW()) > 1 THEN 'BREACH'
        WHEN t.priority = 'high' AND TIMESTAMPDIFF(HOUR, t.created_at, NOW()) > 4 THEN 'BREACH'
        WHEN t.priority = 'medium' AND TIMESTAMPDIFF(HOUR, t.created_at, NOW()) > 24 THEN 'BREACH'
        WHEN t.priority = 'low' AND TIMESTAMPDIFF(HOUR, t.created_at, NOW()) > 72 THEN 'BREACH'
        ELSE 'OK'
    END as sla_status
FROM tickets t
LEFT JOIN agent_workflows aw ON t.id = aw.ticket_id
WHERE t.status IN ('new', 'processing', 'escalated')
ORDER BY 
    FIELD(t.priority, 'urgent', 'high', 'medium', 'low'),
    t.created_at ASC;

-- Knowledge base effectiveness view
CREATE VIEW kb_effectiveness AS
SELECT 
    kb.id,
    kb.title,
    kb.category,
    kb.view_count,
    kb.helpful_votes,
    kb.unhelpful_votes,
    -- Helpfulness ratio
    CASE WHEN (kb.helpful_votes + kb.unhelpful_votes) > 0 
         THEN kb.helpful_votes * 100.0 / (kb.helpful_votes + kb.unhelpful_votes)
         ELSE 0 
    END as helpfulness_percentage,
    -- Usage in ticket resolutions
    COUNT(sc.id) as times_used_in_resolutions,
    AVG(sc.combined_score) as avg_relevance_score,
    kb.updated_at,
    kb.last_accessed
FROM kb_articles kb
LEFT JOIN similar_cases sc ON JSON_CONTAINS(
    (SELECT actions_executed FROM agent_workflows aw 
     JOIN tickets t ON aw.ticket_id = t.id 
     WHERE JSON_EXTRACT(aw.actions_executed, '$[*].kb_article_id') = kb.id),
    CAST(kb.id AS JSON)
)
GROUP BY kb.id, kb.title, kb.category, kb.view_count, kb.helpful_votes, kb.unhelpful_votes, kb.updated_at, kb.last_accessed
ORDER BY times_used_in_resolutions DESC, helpfulness_percentage DESC;

-- ============================================================================
-- STORED PROCEDURES FOR COMPLEX OPERATIONS
-- ============================================================================

-- Procedure to process a new ticket through the agent workflow
DELIMITER //
CREATE PROCEDURE ProcessTicketWithAgent(
    IN p_ticket_id BIGINT,
    OUT p_workflow_id BIGINT,
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE v_error_count INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_success = FALSE;
        ROLLBACK;
    END;
    
    START TRANSACTION;
    
    -- Create new workflow record
    INSERT INTO agent_workflows (ticket_id, workflow_steps, status, total_duration_ms)
    VALUES (p_ticket_id, JSON_ARRAY(), 'running', 0);
    
    SET p_workflow_id = LAST_INSERT_ID();
    
    -- Update ticket status
    UPDATE tickets 
    SET status = 'processing', updated_at = NOW()
    WHERE id = p_ticket_id;
    
    SET p_success = TRUE;
    COMMIT;
END //

-- Procedure to find similar tickets using vector search
CREATE PROCEDURE FindSimilarTickets(
    IN p_ticket_id BIGINT,
    IN p_limit INT DEFAULT 10,
    IN p_min_similarity DECIMAL(5,4) DEFAULT 0.7
)
BEGIN
    DECLARE v_query_vector VECTOR(3072);
    
    -- Get the query ticket's vector
    SELECT combined_vector INTO v_query_vector
    FROM tickets 
    WHERE id = p_ticket_id;
    
    -- Find similar resolved tickets
    SELECT 
        t.id,
        t.title,
        t.description,
        t.resolution,
        t.category,
        t.priority,
        VEC_COSINE_DISTANCE(t.combined_vector, v_query_vector) as similarity_score,
        t.resolved_at,
        t.resolution_type
    FROM tickets t
    WHERE t.status = 'resolved' 
      AND t.id != p_ticket_id
      AND VEC_COSINE_DISTANCE(t.combined_vector, v_query_vector) >= p_min_similarity
    ORDER BY similarity_score DESC
    LIMIT p_limit;
END //

-- Procedure to update performance metrics
CREATE PROCEDURE UpdatePerformanceMetrics(
    IN p_date DATE DEFAULT NULL
)
BEGIN
    DECLARE v_target_date DATE;
    SET v_target_date = COALESCE(p_date, CURDATE());
    
    -- Insert or update daily metrics
    INSERT INTO performance_metrics (
        metric_date,
        tickets_processed,
        tickets_auto_resolved,
        tickets_escalated,
        avg_confidence_score,
        avg_processing_time_ms,
        avg_resolution_time_hours,
        category_breakdown,
        priority_breakdown,
        estimated_time_saved_hours
    )
    SELECT 
        v_target_date,
        COUNT(*) as tickets_processed,
        COUNT(CASE WHEN resolution_type = 'automated' THEN 1 END) as tickets_auto_resolved,
        COUNT(CASE WHEN status = 'escalated' THEN 1 END) as tickets_escalated,
        AVG(agent_confidence) as avg_confidence_score,
        AVG(processing_duration_ms) as avg_processing_time_ms,
        AVG(TIMESTAMPDIFF(MINUTE, created_at, resolved_at) / 60.0) as avg_resolution_time_hours,
        JSON_OBJECT(
            'technical', COUNT(CASE WHEN category = 'technical' THEN 1 END),
            'billing', COUNT(CASE WHEN category = 'billing' THEN 1 END),
            'general', COUNT(CASE WHEN category = 'general' THEN 1 END),
            'account', COUNT(CASE WHEN category = 'account' THEN 1 END)
        ) as category_breakdown,
        JSON_OBJECT(
            'urgent', COUNT(CASE WHEN priority = 'urgent' THEN 1 END),
            'high', COUNT(CASE WHEN priority = 'high' THEN 1 END),
            'medium', COUNT(CASE WHEN priority = 'medium' THEN 1 END),
            'low', COUNT(CASE WHEN priority = 'low' THEN 1 END)
        ) as priority_breakdown,
        -- Estimate 15 minutes saved per auto-resolved ticket
        COUNT(CASE WHEN resolution_type = 'automated' THEN 1 END) * 0.25 as estimated_time_saved_hours
    FROM tickets
    WHERE DATE(created_at) = v_target_date
    ON DUPLICATE KEY UPDATE
        tickets_processed = VALUES(tickets_processed),
        tickets_auto_resolved = VALUES(tickets_auto_resolved),
        tickets_escalated = VALUES(tickets_escalated),
        avg_confidence_score = VALUES(avg_confidence_score),
        avg_processing_time_ms = VALUES(avg_processing_time_ms),
        avg_resolution_time_hours = VALUES(avg_resolution_time_hours),
        category_breakdown = VALUES(category_breakdown),
        priority_breakdown = VALUES(priority_breakdown),
        estimated_time_saved_hours = VALUES(estimated_time_saved_hours),
        updated_at = NOW();
END //

DELIMITER ;