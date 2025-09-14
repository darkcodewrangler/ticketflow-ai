import { API_BASE_URL } from './config';
import { DashboardMetrics, PerformanceMetrics } from '../types';

class AnalyticsApi {
  private baseUrl = `${API_BASE_URL}/api/analytics`;

  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await fetch(`${this.baseUrl}/dashboard`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard metrics: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPerformanceMetrics(days: number = 7): Promise<PerformanceMetrics[]> {
    const response = await fetch(`${this.baseUrl}/performance/daily?days=${days}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch performance metrics: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPerformanceSummary(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/performance/summary`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch performance summary: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getCategoryBreakdown(): Promise<Record<string, number>> {
    const response = await fetch(`${this.baseUrl}/categories`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch category breakdown: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getBasicStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/stats`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch basic stats: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const analyticsApi = new AnalyticsApi();