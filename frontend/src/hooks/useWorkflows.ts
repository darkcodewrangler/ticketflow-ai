import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

// Query keys
export const workflowKeys = {
  all: ['workflows'] as const,
  status: () => [...workflowKeys.all, 'status'] as const,
  detail: (workflowId: string) => [...workflowKeys.all, 'detail', workflowId] as const,
  ticket: (ticketId: number) => [...workflowKeys.all, 'ticket', ticketId] as const,
};

// Get workflow status
export const useWorkflowStatus = (workflowId: string) => {
  return useQuery({
    queryKey: workflowKeys.status(),
    queryFn: () => api.getWorkflowStatus(workflowId),
    select: (data) => data.data,
    refetchInterval: (data) => {
      // Stop polling if workflow is completed or failed
      const status = data?.data?.status;
      return status === 'completed' || status === 'failed' ? false : 2000;
    },
    enabled: !!workflowId,
  });
};

// Get specific workflow
export const useWorkflow = (workflowId: string) => {
  return useQuery({
    queryKey: workflowKeys.detail(workflowId),
    queryFn: () => api.getWorkflow(workflowId),
    select: (data) => data.data,
    enabled: !!workflowId,
  });
};

// Get workflows for a ticket
export const useTicketWorkflows = (ticketId: number) => {
  return useQuery({
    queryKey: workflowKeys.ticket(ticketId),
    queryFn: () => api.getTicketWorkflows(ticketId),
    select: (data) => data.data,
    enabled: !!ticketId,
  });
};