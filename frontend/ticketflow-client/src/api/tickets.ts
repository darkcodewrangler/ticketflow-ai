import { API_BASE_URL } from './config';
import { Ticket, TicketCreateRequest } from '../types';

class TicketApi {
  private baseUrl = `${API_BASE_URL}/api/tickets`;

  async getTickets(filters?: Record<string, any>): Promise<{ tickets: Ticket[] }> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value));
        }
      });
    }
    
    const url = params.toString() ? `${this.baseUrl}/?${params}` : `${this.baseUrl}/`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch tickets: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getTicket(id: number): Promise<Ticket> {
    const response = await fetch(`${this.baseUrl}/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch ticket: ${response.statusText}`);
    }
    
    return response.json();
  }

  async createTicket(data: TicketCreateRequest): Promise<Ticket> {
    const response = await fetch(`${this.baseUrl}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create ticket: ${response.statusText}`);
    }
    
    return response.json();
  }

  async updateTicket(id: number, data: Partial<Ticket>): Promise<Ticket> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update ticket: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getRecentTickets(): Promise<Ticket[]> {
    const response = await fetch(`${this.baseUrl}/recent`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recent tickets: ${response.statusText}`);
    }
    
    return response.json();
  }

  async processTicket(ticketId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/agent/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ticket_id: ticketId }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to process ticket: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const ticketApi = new TicketApi();