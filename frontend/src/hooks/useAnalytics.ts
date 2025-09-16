import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

// Query keys
export const analyticsKeys = {
  all: ['analytics'] as const,
  metrics: () => [...analyticsKeys.all, 'metrics'] as const,
  performance: () => [...analyticsKeys.all, 'performance'] as const,
  performanceTrends: (days: number) => [...analyticsKeys.performance(), 'trends', days] as const,
  performanceSummary: () => [...analyticsKeys.performance(), 'summary'] as const,
  categories: () => [...analyticsKeys.all, 'categories'] as const,
};

// Get dashboard metrics
export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: analyticsKeys.metrics(),
    queryFn: () => api.getDashboardMetrics(),
    select: (data) => data.data,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

// Get performance trends
export const usePerformanceTrends = (days: number = 7) => {
  return useQuery({
    queryKey: analyticsKeys.performanceTrends(days),
    queryFn: () => api.getPerformanceTrends(days),
    select: (data) => data.data,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Get performance summary
export const usePerformanceSummary = () => {
  return useQuery({
    queryKey: analyticsKeys.performanceSummary(),
    queryFn: () => api.getPerformanceSummary(),
    select: (data) => data.data,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Get category breakdown
export const useCategoryBreakdown = () => {
  return useQuery({
    queryKey: analyticsKeys.categories(),
    queryFn: () => api.getCategoryBreakdown(),
    select: (data) => data.data,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};