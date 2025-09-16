import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Ticket, TicketCreateRequest, TicketFilters } from "@/types";
import { showSuccess, showError } from "@/utils/toast";

// Query keys
export const ticketKeys = {
  all: ['tickets'] as const,
  lists: () => [...ticketKeys.all, 'list'] as const,
  list: (filters?: TicketFilters) => [...ticketKeys.lists(), { filters }] as const,
  details: () => [...ticketKeys.all, 'detail'] as const,
  detail: (id: number) => [...ticketKeys.details(), id] as const,
  recent: () => [...ticketKeys.all, 'recent'] as const,
  workflows: (ticketId: number) => [...ticketKeys.all, 'workflows', ticketId] as const,
};

// Get all tickets with optional filters
export const useTickets = (filters?: TicketFilters) => {
  return useQuery({
    queryKey: ticketKeys.list(filters),
    queryFn: () => api.getTickets(filters),
    select: (data) => data.data,
  });
};

// Get recent tickets
export const useRecentTickets = () => {
  return useQuery({
    queryKey: ticketKeys.recent(),
    queryFn: () => api.getRecentTickets(),
    select: (data) => data.data,
  });
};

// Get single ticket
export const useTicket = (id: number) => {
  return useQuery({
    queryKey: ticketKeys.detail(id),
    queryFn: () => api.getTicket(id),
    select: (data) => data.data,
    enabled: !!id,
  });
};

// Get ticket workflows
export const useTicketWorkflows = (ticketId: number) => {
  return useQuery({
    queryKey: ticketKeys.workflows(ticketId),
    queryFn: () => api.getTicketWorkflows(ticketId),
    select: (data) => data.data,
    enabled: !!ticketId,
  });
};

// Create ticket mutation
export const useCreateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TicketCreateRequest) => api.createTicket(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ticketKeys.recent() });
      showSuccess("Ticket created successfully");
      return response.data;
    },
    onError: (error: any) => {
      showError(error.message || "Failed to create ticket");
    },
  });
};

// Update ticket mutation
export const useUpdateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Ticket> }) =>
      api.updateTicket(id, data),
    onSuccess: (response, { id }) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ticketKeys.recent() });
      showSuccess("Ticket updated successfully");
      return response.data;
    },
    onError: (error: any) => {
      showError(error.message || "Failed to update ticket");
    },
  });
};

// Delete ticket mutation
export const useDeleteTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteTicket(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: ticketKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ticketKeys.recent() });
      showSuccess("Ticket deleted successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to delete ticket");
    },
  });
};

// Process ticket with AI
export const useProcessTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, config }: { ticketId: number; config?: any }) =>
      api.processTicket(ticketId, config),
    onSuccess: (response, { ticketId }) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(ticketId) });
      queryClient.invalidateQueries({ queryKey: ticketKeys.workflows(ticketId) });
      showSuccess("AI processing started for ticket");
      return response.data;
    },
    onError: (error: any) => {
      showError(error.message || "Failed to process ticket");
    },
  });
};