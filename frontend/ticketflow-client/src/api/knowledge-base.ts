import { API_BASE_URL } from './config';
import { KnowledgeBaseArticle, KnowledgeBaseCreateRequest } from '../types';

class KnowledgeBaseApi {
  private baseUrl = `${API_BASE_URL}/api/kb`;

  async getArticles(filters?: Record<string, any>): Promise<KnowledgeBaseArticle[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value));
        }
      });
    }
    
    const url = params.toString() ? `${this.baseUrl}/articles?${params}` : `${this.baseUrl}/articles`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch articles: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getArticle(id: number): Promise<KnowledgeBaseArticle> {
    const response = await fetch(`${this.baseUrl}/articles/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch article: ${response.statusText}`);
    }
    
    return response.json();
  }

  async createArticle(data: KnowledgeBaseCreateRequest): Promise<KnowledgeBaseArticle> {
    const response = await fetch(`${this.baseUrl}/articles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create article: ${response.statusText}`);
    }
    
    return response.json();
  }

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }
    
    return response.json();
  }

  async crawlUrl(url: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/crawl-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to crawl URL: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getProcessingStatus(taskId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/processing-status/task_id=${taskId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get processing status: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const knowledgeBaseApi = new KnowledgeBaseApi();