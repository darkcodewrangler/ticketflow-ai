
-- ============================================================================
-- SAMPLE CONFIGURATION DATA
-- ============================================================================

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description, category) VALUES
('agent.confidence_threshold', '0.85', 'number', 'Minimum confidence score for auto-resolution', 'agent'),
('agent.max_similar_cases', '10', 'number', 'Maximum number of similar cases to analyze', 'agent'),
('agent.max_processing_time_ms', '30000', 'number', 'Maximum processing time before timeout', 'agent'),
('search.vector_similarity_threshold', '0.75', 'number', 'Minimum vector similarity for case matching', 'search'),
('search.hybrid_weight_vector', '0.7', 'number', 'Weight for vector search in hybrid search', 'search'),
('search.hybrid_weight_text', '0.3', 'number', 'Weight for text search in hybrid search', 'search'),
('integrations.slack.enabled', 'true', 'boolean', 'Enable Slack notifications', 'integrations'),
('integrations.slack.default_channel', '"#support-alerts"', 'string', 'Default Slack channel for notifications', 'integrations'),
('integrations.email.enabled', 'true', 'boolean', 'Enable email notifications', 'integrations');
