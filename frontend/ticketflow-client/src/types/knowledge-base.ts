export interface KnowledgeBaseArticle {
  id: number;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  source_url: string;
  source_type: "manual" | "crawled" | "imported";
  author: string;
  view_count: number;
  helpful_votes: number;
  unhelpful_votes: number;
  usage_in_resolutions: number;
  helpfulness_score: number;
  created_at: string;
  updated_at: string;
  last_accessed?: string;
}

export interface KnowledgeBaseCreateRequest {
  title: string;
  content: string;
  summary?: string;
  category: string;
  tags?: string[];
  source_url?: string;
  source_type?: string;
  author?: string;
}