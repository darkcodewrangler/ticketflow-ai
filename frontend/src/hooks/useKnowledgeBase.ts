import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { KBArticle } from "@/types";
import { showSuccess, showError } from "@/utils/toast";

// Query keys
export const kbKeys = {
  all: ['kb'] as const,
  articles: () => [...kbKeys.all, 'articles'] as const,
  search: (query: string, limit?: number, category?: string) => 
    [...kbKeys.all, 'search', { query, limit, category }] as const,
};

// Get all KB articles
export const useKBArticles = () => {
  return useQuery({
    queryKey: kbKeys.articles(),
    queryFn: () => api.getKBArticles(),
    select: (data) => data.data,
  });
};

// Search KB articles
export const useSearchKB = (query: string, limit: number = 10, category?: string) => {
  return useQuery({
    queryKey: kbKeys.search(query, limit, category),
    queryFn: () => api.searchKB(query, limit, category),
    select: (data) => data.data,
    enabled: query.length > 2, // Only search if query is longer than 2 characters
  });
};

// Create KB article mutation
export const useCreateKBArticle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<KBArticle, "id">) => api.createKBArticle(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: kbKeys.articles() });
      showSuccess("Knowledge base article created successfully");
      return response.data;
    },
    onError: (error: any) => {
      showError(error.message || "Failed to create KB article");
    },
  });
};

// Upload KB file mutation
export const useUploadKBFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, category, metadata }: { 
      file: File; 
      category: string; 
      metadata?: Record<string, any> 
    }) => api.uploadKBFile(file, category, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.articles() });
      showSuccess("File uploaded and processed successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to upload file");
    },
  });
};

// Crawl URL mutation
export const useCrawlURL = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ url, category, maxDepth, metadata }: {
      url: string;
      category: string;
      maxDepth?: number;
      metadata?: Record<string, any>;
    }) => api.crawlURL(url, category, maxDepth, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.articles() });
      showSuccess("URL crawled and content added to knowledge base");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to crawl URL");
    },
  });
};