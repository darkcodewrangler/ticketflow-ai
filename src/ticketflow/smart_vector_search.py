class SmartVectorSearch:
    async def contextual_search(self, ticket: Ticket, context: Dict) -> List[SimilarCase]:
        """Search with additional context weighting"""
        
        # Create enhanced query with context
        enhanced_query = f"""
        Issue: {ticket.description}
        Category: {ticket.category}
        Priority: {ticket.priority}
        User Type: {context.get('user_type', 'unknown')}
        Previous Issues: {context.get('user_history', [])}
        """
        
        query_vector = await self.generate_embedding(enhanced_query)
        
        # Search with category weighting
        sql = """
        SELECT 
            *,
            VEC_COSINE_DISTANCE(description_vector, %s) as similarity,
            -- Boost score for same category
            CASE WHEN category = %s THEN similarity * 1.2 ELSE similarity END as weighted_similarity,
            -- Boost for same priority level
            CASE WHEN priority = %s THEN weighted_similarity * 1.1 ELSE weighted_similarity END as final_score
        FROM tickets 
        WHERE status = 'resolved'
          AND VEC_COSINE_DISTANCE(description_vector, %s) > 0.7
        ORDER BY final_score DESC
        LIMIT 15
        """
        
        return await self.execute_search(sql, [query_vector, ticket.category, ticket.priority, query_vector])
    
    async def temporal_search(self, ticket: Ticket, time_window_days: int = 90) -> List[SimilarCase]:
        """Find similar cases within a time window"""
        
        sql = """
        SELECT *,
            VEC_COSINE_DISTANCE(description_vector, %s) as similarity,
            -- Time decay factor (more recent = higher score)
            EXP(-DATEDIFF(NOW(), resolved_at) / %s) as time_factor,
            similarity * time_factor as time_weighted_score
        FROM tickets
        WHERE status = 'resolved' 
          AND resolved_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
          AND VEC_COSINE_DISTANCE(description_vector, %s) > 0.7
        ORDER BY time_weighted_score DESC
        LIMIT 10
        """
        
        query_vector = await self.generate_embedding(ticket.description)
        return await self.execute_search(sql, [query_vector, time_window_days, time_window_days, query_vector])
