import { create } from 'zustand';
import { Ticket, TicketCreateRequest } from '../types';
import { ticketApi } from '../api';

interface TicketState {
  tickets: Ticket[];
  currentTicket: Ticket | null;
  loading: boolean;
  error: string | null;
  filters: Record<string, any>;
  
  // Actions
  setTickets: (tickets: Ticket[]) => void;
  setCurrentTicket: (ticket: Ticket | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Record<string, any>) => void;
  
  // Async actions
  fetchTickets: (filters?: Record<string, any>) => Promise<void>;
  fetchTicket: (id: number) => Promise<void>;
  createTicket: (data: TicketCreateRequest) => Promise<Ticket>;
  updateTicket: (id: number, data: Partial<Ticket>) => Promise<void>;
  processTicket: (ticketId: number) => Promise<void>;
  
  // Utility actions
  addTicket: (ticket: Ticket) => void;
  updateTicketInList: (updatedTicket: Ticket) => void;
  clearError: () => void;
}

export const useTicketStore = create<TicketState>((set, get) => ({
  tickets: [],
  currentTicket: null,
  loading: false,
  error: null,
  filters: {},
  
  setTickets: (tickets) => set({ tickets }),
  setCurrentTicket: (ticket) => set({ currentTicket: ticket }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilters: (filters) => set({ filters }),
  
  fetchTickets: async (filters) => {
    set({ loading: true, error: null });
    try {
      const response = await ticketApi.getTickets(filters);
      set({ tickets: response.tickets, loading: false });
      if (filters) {
        set({ filters });
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch tickets',
        loading: false 
      });
    }
  },
  
  fetchTicket: async (id) => {
    set({ loading: true, error: null });
    try {
      const ticket = await ticketApi.getTicket(id);
      set({ currentTicket: ticket, loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch ticket',
        loading: false 
      });
    }
  },
  
  createTicket: async (data) => {
    set({ loading: true, error: null });
    try {
      const newTicket = await ticketApi.createTicket(data);
      const { tickets } = get();
      set({ 
        tickets: [newTicket, ...tickets],
        loading: false 
      });
      return newTicket;
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to create ticket',
        loading: false 
      });
      throw error;
    }
  },
  
  updateTicket: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const updatedTicket = await ticketApi.updateTicket(id, data);
      const { tickets, currentTicket } = get();
      
      set({
        tickets: tickets.map(t => t.id === id ? updatedTicket : t),
        currentTicket: currentTicket?.id === id ? updatedTicket : currentTicket,
        loading: false
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update ticket',
        loading: false 
      });
    }
  },
  
  processTicket: async (ticketId) => {
    set({ loading: true, error: null });
    try {
      await ticketApi.processTicket(ticketId);
      // Update ticket status to processing
      const { tickets, currentTicket } = get();
      const updatedTickets = tickets.map(t => 
        t.id === ticketId ? { ...t, status: 'processing' as const } : t
      );
      
      set({
        tickets: updatedTickets,
        currentTicket: currentTicket?.id === ticketId 
          ? { ...currentTicket, status: 'processing' as const }
          : currentTicket,
        loading: false
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to process ticket',
        loading: false 
      });
    }
  },
  
  addTicket: (ticket) => {
    const { tickets } = get();
    set({ tickets: [ticket, ...tickets] });
  },
  
  updateTicketInList: (updatedTicket) => {
    const { tickets, currentTicket } = get();
    set({
      tickets: tickets.map(t => t.id === updatedTicket.id ? updatedTicket : t),
      currentTicket: currentTicket?.id === updatedTicket.id ? updatedTicket : currentTicket
    });
  },
  
  clearError: () => set({ error: null })
}));