import { create } from 'zustand';
import { DashboardMetrics, PerformanceMetrics } from '../types';
import { analyticsApi } from '../api';

interface AnalyticsState {
  dashboardMetrics: DashboardMetrics | null;
  performanceMetrics: PerformanceMetrics[];
  categoryBreakdown: Record<string, number>;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Actions
  setDashboardMetrics: (metrics: DashboardMetrics) => void;
  setPerformanceMetrics: (metrics: PerformanceMetrics[]) => void;
  setCategoryBreakdown: (breakdown: Record<string, number>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Async actions
  fetchDashboardMetrics: () => Promise<void>;
  fetchPerformanceMetrics: (days?: number) => Promise<void>;
  fetchCategoryBreakdown: () => Promise<void>;
  fetchAllAnalytics: () => Promise<void>;
  
  // Utility actions
  updateMetricsFromWebSocket: (metrics: DashboardMetrics) => void;
  clearError: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  dashboardMetrics: null,
  performanceMetrics: [],
  categoryBreakdown: {},
  loading: false,
  error: null,
  lastUpdated: null,
  
  setDashboardMetrics: (metrics) => set({ 
    dashboardMetrics: metrics,
    lastUpdated: new Date()
  }),
  
  setPerformanceMetrics: (metrics) => set({ performanceMetrics: metrics }),
  setCategoryBreakdown: (breakdown) => set({ categoryBreakdown: breakdown }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  fetchDashboardMetrics: async () => {
    set({ loading: true, error: null });
    try {
      const metrics = await analyticsApi.getDashboardMetrics();
      set({ 
        dashboardMetrics: metrics,
        loading: false,
        lastUpdated: new Date()
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch dashboard metrics',
        loading: false 
      });
    }
  },
  
  fetchPerformanceMetrics: async (days = 7) => {
    set({ loading: true, error: null });
    try {
      const metrics = await analyticsApi.getPerformanceMetrics(days);
      set({ 
        performanceMetrics: metrics,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch performance metrics',
        loading: false 
      });
    }
  },
  
  fetchCategoryBreakdown: async () => {
    set({ loading: true, error: null });
    try {
      const breakdown = await analyticsApi.getCategoryBreakdown();
      set({ 
        categoryBreakdown: breakdown,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch category breakdown',
        loading: false 
      });
    }
  },
  
  fetchAllAnalytics: async () => {
    set({ loading: true, error: null });
    try {
      const [dashboardMetrics, performanceMetrics, categoryBreakdown] = await Promise.all([
        analyticsApi.getDashboardMetrics(),
        analyticsApi.getPerformanceMetrics(7),
        analyticsApi.getCategoryBreakdown()
      ]);
      
      set({ 
        dashboardMetrics,
        performanceMetrics,
        categoryBreakdown,
        loading: false,
        lastUpdated: new Date()
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch analytics data',
        loading: false 
      });
    }
  },
  
  updateMetricsFromWebSocket: (metrics) => {
    set({ 
      dashboardMetrics: metrics,
      lastUpdated: new Date()
    });
  },
  
  clearError: () => set({ error: null })
}));