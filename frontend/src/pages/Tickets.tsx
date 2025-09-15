import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { PriorityBadge } from "@/components/PriorityBadge";
import {
  Search,
  Filter,
  Plus,
  Eye,
  Bot,
  MoreHorizontal,
  Calendar,
  Download,
  RefreshCw,
  Ticket,
} from "lucide-react";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import type { Ticket as TicketType, TicketFilters } from "@/types";
import { api } from "@/services/api";
import { useAppContext } from "@/contexts/AppContext";
import { showError, showSuccess } from "@/utils/toast";

// Mock tickets data for demonstration
const mockTickets: TicketType[] = [
  {
    id: 1,
    title: "Email integration not working properly",
    description:
      "Users are unable to receive email notifications from the system. The SMTP configuration seems to be failing.",
    status: "processing",
    priority: "high",
    category: "Integration",
    user_email: "user@company.com",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-15T11:45:00Z",
    resolved_at: null,
    resolution: null,
    agent_confidence: 0.85,
    metadata: { source: "web", department: "IT" },
  },
  {
    id: 2,
    title: "Password reset functionality broken",
    description:
      "The password reset link in emails is not working. Users click the link but get a 404 error.",
    status: "resolved",
    priority: "medium",
    category: "Authentication",
    user_email: "admin@company.com",
    created_at: "2024-01-15T09:15:00Z",
    updated_at: "2024-01-15T10:30:00Z",
    resolved_at: "2024-01-15T10:30:00Z",
    resolution:
      "Fixed broken URL routing in password reset controller. Updated email templates with correct links.",
    agent_confidence: 0.95,
    metadata: { source: "email", department: "Security" },
  },
  {
    id: 3,
    title: "Dashboard loading slowly",
    description:
      "The main dashboard takes over 10 seconds to load. This is affecting user productivity.",
    status: "new",
    priority: "low",
    category: "Performance",
    user_email: "support@company.com",
    created_at: "2024-01-15T08:45:00Z",
    updated_at: "2024-01-15T08:45:00Z",
    resolved_at: null,
    resolution: null,
    agent_confidence: null,
    metadata: { source: "phone", department: "Operations" },
  },
  {
    id: 4,
    title: "Critical security vulnerability detected",
    description:
      "Automated security scan detected a potential SQL injection vulnerability in the user management module.",
    status: "escalated",
    priority: "urgent",
    category: "Security",
    user_email: "security@company.com",
    created_at: "2024-01-15T07:20:00Z",
    updated_at: "2024-01-15T07:25:00Z",
    resolved_at: null,
    resolution: null,
    agent_confidence: 0.98,
    metadata: {
      source: "automated",
      department: "Security",
      severity: "critical",
    },
  },
  {
    id: 5,
    title: "Mobile app crashes on startup",
    description:
      "iOS app version 2.1.3 crashes immediately after opening. Affects approximately 15% of users.",
    status: "processing",
    priority: "high",
    category: "Mobile",
    user_email: "mobile@company.com",
    created_at: "2024-01-14T16:30:00Z",
    updated_at: "2024-01-15T09:00:00Z",
    resolved_at: null,
    resolution: null,
    agent_confidence: 0.72,
    metadata: { source: "app_store", department: "Mobile", platform: "iOS" },
  },
];

export default function Tickets() {
  const [tickets, setTickets] = useState<TicketType[]>(mockTickets);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<TicketFilters>({});
  const [selectedTickets, setSelectedTickets] = useState<number[]>([]);

  const { addLiveUpdate } = useAppContext();

  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      !searchQuery ||
      ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ticket.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ticket.user_email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      !filters.status?.length || filters.status.includes(ticket.status);
    const matchesPriority =
      !filters.priority?.length || filters.priority.includes(ticket.priority);
    const matchesCategory =
      !filters.category?.length || filters.category.includes(ticket.category);

    return matchesSearch && matchesStatus && matchesPriority && matchesCategory;
  });

  const handleProcessTicket = async (ticketId: number) => {
    try {
      setLoading(true);
      const response = await api.processTicket(ticketId);

      // // Simulate processing
      // setTickets((prev) =>
      //   prev.map((ticket) =>
      //     ticket.id === ticketId
      //       ? {
      //           ...ticket,
      //           status: "processing" as const,
      //           updated_at: new Date().toISOString(),
      //         }
      //       : ticket
      //   )
      // );

      addLiveUpdate({
        id: `process-${ticketId}-${Date.now()}`,
        type: "agent_update",
        message: `Started AI processing for ticket #${ticketId}`,
        timestamp: new Date().toISOString(),
        metadata: { ticket_id: ticketId },
      });

      showSuccess(`Started AI processing for ticket #${ticketId}`);
    } catch (error) {
      showError("Failed to process ticket");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    const fetchTickets = async () => {
      const tickets = await api.getTickets();
      setTickets(tickets.data);
    };
    fetchTickets();
  }, []);
  const handleBulkAction = (action: string) => {
    if (selectedTickets.length === 0) return;

    switch (action) {
      case "process":
        selectedTickets.forEach((id) => handleProcessTicket(id));
        break;
      case "export":
        showSuccess(`Exported ${selectedTickets.length} tickets`);
        break;
      default:
        break;
    }
    setSelectedTickets([]);
  };

  const getConfidenceColor = (confidence: number | null) => {
    if (!confidence) return "text-gray-400";
    if (confidence >= 0.9) return "text-green-600";
    if (confidence >= 0.7) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tickets</h1>
          <p className="text-gray-600 mt-1">
            Manage and monitor support tickets with AI automation
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>

          <Link to="/tickets/new">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Ticket
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search tickets by title, description, or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex gap-3">
              <Select
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    status: value ? [value] : undefined,
                  }))
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="escalated">Escalated</SelectItem>
                </SelectContent>
              </Select>

              <Select
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    priority: value ? [value] : undefined,
                  }))
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>

              <Select
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    category: value ? [value] : undefined,
                  }))
                }
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Integration">Integration</SelectItem>
                  <SelectItem value="Authentication">Authentication</SelectItem>
                  <SelectItem value="Performance">Performance</SelectItem>
                  <SelectItem value="Security">Security</SelectItem>
                  <SelectItem value="Mobile">Mobile</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="icon">
                <Filter className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedTickets.length > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-900">
                {selectedTickets.length} ticket
                {selectedTickets.length > 1 ? "s" : ""} selected
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("process")}
                  className="border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  <Bot className="w-4 h-4 mr-1" />
                  Process with AI
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("export")}
                  className="border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  <Download className="w-4 h-4 mr-1" />
                  Export
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Tickets ({filteredTickets.length})</CardTitle>
            <Button variant="outline" size="sm" disabled={loading}>
              <RefreshCw
                className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={
                        selectedTickets.length === filteredTickets.length
                      }
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedTickets(filteredTickets.map((t) => t.id));
                        } else {
                          setSelectedTickets([]);
                        }
                      }}
                      className="rounded"
                    />
                  </TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>AI Confidence</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTickets.map((ticket) => (
                  <TableRow key={ticket.id} className="hover:bg-gray-50">
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedTickets.includes(ticket.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTickets((prev) => [...prev, ticket.id]);
                          } else {
                            setSelectedTickets((prev) =>
                              prev.filter((id) => id !== ticket.id)
                            );
                          }
                        }}
                        className="rounded"
                      />
                    </TableCell>
                    <TableCell className="font-medium">#{ticket.id}</TableCell>
                    <TableCell>
                      <div className="max-w-xs">
                        <p className="font-medium text-gray-900 truncate">
                          {ticket.title}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {ticket.description}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge
                        status={ticket.status}
                        pulse={ticket.status === "processing"}
                      />
                    </TableCell>
                    <TableCell>
                      <PriorityBadge priority={ticket.priority} showIcon />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{ticket.category}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-gray-600">
                      {ticket.user_email}
                    </TableCell>
                    <TableCell>
                      {ticket.agent_confidence ? (
                        <span
                          className={`text-sm font-medium ${getConfidenceColor(
                            ticket.agent_confidence
                          )}`}
                        >
                          {(ticket.agent_confidence * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-600">
                      {formatDistanceToNow(new Date(ticket.created_at), {
                        addSuffix: true,
                      })}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Link to={`/tickets/${ticket.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </Link>
                        {ticket.status === "new" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleProcessTicket(ticket.id)}
                            disabled={loading}
                          >
                            <Bot className="w-4 h-4" />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {filteredTickets.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500">
                <Ticket className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No tickets found</p>
                <p className="text-sm">Try adjusting your search or filters</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
