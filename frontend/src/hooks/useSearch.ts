import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

// Query keys
export const searchKeys = {
  all: ['search'] as const,
  tickets: (query: string, limit?: number, category?: string) => 
    [...searchKeys.all, 'tickets', { query, limit, category }] as const,
  kb: (query: string, limit?: number, category?: string) => 
    [...searchKeys.all, 'kb', { query, limit, category }] as const,
  unified: (query: string, limit?: number) => 
    [...searchKeys.all, 'unified', { query, limit }] as const,
};

// Search tickets
export const useSearchTickets = (query: string, limit: number = 10, category?: string) => {
  return useQuery({
    queryKey: searchKeys.tickets(query, limit, category),
    queryFn: () => api.searchTickets(query, limit, category),
    select: (data) => data.data,
    enabled: query.length > 2, // Only search if query is longer than 2 characters
    staleTime: 30000, // 30 seconds
  });
};

// Search knowledge base
export const useSearchKB = (query: string, limit: number = 10, category?: string) => {
  return useQuery({
    queryKey: searchKeys.kb(query, limit, category),
    queryFn: () => api.searchKB(query, limit, category),
    select: (data) => data.data,
    enabled: query.length > 2, // Only search if query is longer than 2 characters
    staleTime: 30000, // 30 seconds
  });
};

// Unified search (tickets + KB)
export const useUnifiedSearch = (query: string, limit: number = 10) => {
  return useQuery({
    queryKey: searchKeys.unified(query, limit),
    queryFn: () => api.searchUnified(query, limit),
    select: (data) => data.data,
    enabled: query.length > 2, // Only search if query is longer than 2 characters
    staleTime: 30000, // 30 seconds
  });
};