import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { StatusBadge } from "@/components/StatusBadge";
import { PriorityBadge } from "@/components/PriorityBadge";
import { TicketTimeline } from "@/components/TicketTimeline";
import { WorkflowVisualizer } from "@/components/WorkflowVisualizer";
import {
  ArrowLeft,
  Bot,
  Clock,
  User,
  Mail,
  Calendar,
  Edit,
  Save,
  X,
  CheckCircle,
  AlertTriangle,
  FileText,
  ExternalLink,
  Activity,
  MessageSquare,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import type { Ticket, WorkflowResponse, SimilarCase, KBArticle } from "@/types";
import { showSuccess, showError } from "@/utils/toast";
// Import React Query hooks
import { useTicket, useProcessTicket, useUpdateTicket, useTicketWorkflows } from "@/hooks/useTickets";
import { useKBArticles } from "@/hooks/useKnowledgeBase";

// Mock data for demonstration - kept as backup
const mockTicket: Ticket = {
  id: 1,
  title: "Email integration not working properly",
  description:
    "Users are unable to receive email notifications from the system. The SMTP configuration seems to be failing intermittently. This started happening after the recent server update on January 10th. Multiple users have reported the issue across different departments.",
  status: "processing",
  priority: "high",
  category: "Integration",
  user_email: "user@company.com",
  created_at: "2024-01-15T10:30:00Z",
  updated_at: "2024-01-15T11:45:00Z",
  resolved_at: null,
  resolution: null,
  agent_confidence: 0.85,
  metadata: {
    source: "web",
    department: "IT",
    affected_users: 25,
    server_version: "2.1.3",
    error_code: "SMTP_TIMEOUT",
  },
};

const mockWorkflow: WorkflowResponse = {
  workflow_id: "wf_001",
  ticket_id: 1,
  status: "processing",
  steps: [
    {
      step: "ticket_analysis",
      status: "completed",
      message: "Analyzed ticket content and extracted key information",
      timestamp: "2024-01-15T10:30:00Z",
      duration_ms: 1200,
      data: { confidence: 0.95, category: "Integration", priority: "high" },
    },
    {
      step: "knowledge_search",
      status: "completed",
      message: "Found 3 relevant knowledge base articles",
      timestamp: "2024-01-15T10:30:05Z",
      duration_ms: 2800,
      data: { articles_found: 3, relevance_score: 0.87 },
    },
    {
      step: "similar_cases",
      status: "processing",
      message: "Searching for similar resolved cases...",
      timestamp: "2024-01-15T10:30:08Z",
      data: { cases_analyzed: 15, similarity_threshold: 0.8 },
    },
    {
      step: "solution_generation",
      status: "pending",
      message: "Waiting to generate solution",
      timestamp: "2024-01-15T10:30:08Z",
    },
    {
      step: "confidence_check",
      status: "pending",
      message: "Waiting for confidence validation",
      timestamp: "2024-01-15T10:30:08Z",
    },
  ],
};

const mockSimilarCases: SimilarCase[] = [
  {
    id: 156,
    title: "SMTP timeout errors after server update",
    similarity_score: 0.92,
    resolution:
      "Updated SMTP configuration timeout values from 30s to 60s in server.config. Restarted email service.",
  },
  {
    id: 143,
    title: "Email notifications failing intermittently",
    similarity_score: 0.87,
    resolution:
      "Fixed by updating email queue processing to handle connection pooling properly.",
  },
];

const mockKBArticles: KBArticle[] = [
  {
    id: 1,
    title: "Troubleshooting SMTP Configuration Issues",
    content: "This guide covers common SMTP configuration problems...",
    category: "Email",
    tags: ["smtp", "email", "configuration"],
    relevance_score: 0.95,
    content_preview:
      "Step-by-step guide to diagnose and fix SMTP timeout issues, including configuration examples and common pitfalls.",
  },
  {
    id: 2,
    title: "Email Service Restart Procedures",
    content: "How to safely restart email services...",
    category: "Operations",
    tags: ["email", "restart", "maintenance"],
    relevance_score: 0.78,
    content_preview:
      "Safe procedures for restarting email services without losing queued messages.",
  },
];

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const ticketId = id ? parseInt(id) : 1;

  // React Query hooks for API data
  const { 
    data: apiTicket, 
    isLoading: ticketLoading, 
    error: ticketError 
  } = useTicket(ticketId);
  
  const { 
    data: apiWorkflow, 
    isLoading: workflowLoading 
  } = useTicketWorkflows(ticketId);
  
  const { 
    data: apiKBArticles, 
    isLoading: kbLoading 
  } = useKBArticles();
  
  const processTicketMutation = useProcessTicket();
  const updateTicketMutation = useUpdateTicket();

  // Local state for UI
  const [isEditing, setIsEditing] = useState(false);
  const [editedResolution, setEditedResolution] = useState("");
  const [activeTab, setActiveTab] = useState("details");

  // Use API data if available, fallback to mock data
  const displayTicket = apiTicket || mockTicket;
  const displayWorkflow = apiWorkflow || mockWorkflow;
  const displayKBArticles = apiKBArticles || mockKBArticles;
  
  const isLoading = ticketLoading || workflowLoading || kbLoading || 
                   processTicketMutation.isPending || updateTicketMutation.isPending;

  const handleProcessTicket = async () => {
    try {
      await processTicketMutation.mutateAsync(ticketId);
    } catch (error) {
      // Error handling is done in the mutation
    }
  };

  const handleSaveResolution = async () => {
    try {
      await updateTicketMutation.mutateAsync({
        id: ticketId,
        updates: {
          status: "resolved",
          resolution: editedResolution,
          resolved_at: new Date().toISOString(),
        }
      });

      setIsEditing(false);
      setEditedResolution("");
    } catch (error) {
      // Error handling is done in the mutation
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/tickets">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tickets
          </Button>
        </Link>

        <div className="flex-1">
           <div className="flex items-center gap-3">
             <h1 className="text-2xl font-bold text-gray-900">
               Ticket #{displayTicket.id}
             </h1>
             <StatusBadge
               status={displayTicket.status}
               pulse={displayTicket.status === "processing"}
             />
             <PriorityBadge priority={displayTicket.priority} showIcon />
           </div>
           <p className="text-gray-600 mt-1">{displayTicket.title}</p>
         </div>

         <div className="flex items-center gap-2">
           {displayTicket.status === "new" && (
             <Button onClick={handleProcessTicket} disabled={isLoading}>
               <Bot className="w-4 h-4 mr-2" />
               Process with AI
             </Button>
           )}
           {displayTicket.status !== "resolved" && !isEditing && (
             <Button variant="outline" onClick={() => setIsEditing(true)}>
               <Edit className="w-4 h-4 mr-2" />
               Add Resolution
             </Button>
           )}
         </div>
      </div>

      {/* Tab Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-2">
            <Button
              variant={activeTab === "details" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("details")}
            >
              <FileText className="w-4 h-4 mr-1" />
              Details
            </Button>
            <Button
              variant={activeTab === "workflow" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("workflow")}
            >
              <Bot className="w-4 h-4 mr-1" />
              AI Workflow
            </Button>
            <Button
              variant={activeTab === "timeline" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("timeline")}
            >
              <Activity className="w-4 h-4 mr-1" />
              Timeline
            </Button>
            <Button
              variant={activeTab === "comments" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("comments")}
            >
              <MessageSquare className="w-4 h-4 mr-1" />
              Comments
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === "details" && (
            <>
              {/* Ticket Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Ticket Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">
                       Description
                     </h3>
                     <p className="text-gray-700 leading-relaxed">
                       {displayTicket.description}
                     </p>
                   </div>

                   {displayTicket.metadata &&
                     Object.keys(displayTicket.metadata).length > 0 && (
                       <div>
                         <h3 className="font-medium text-gray-900 mb-2">
                           Additional Information
                         </h3>
                         <div className="grid grid-cols-2 gap-4 text-sm">
                           {Object.entries(displayTicket.metadata).map(
                             ([key, value]) => (
                               <div key={key} className="flex justify-between">
                                 <span className="text-gray-600 capitalize">
                                   {key.replace(/_/g, " ")}:
                                 </span>
                                 <span className="font-medium">
                                   {String(value)}
                                 </span>
                               </div>
                             )
                           )}
                         </div>
                       </div>
                     )}
                </CardContent>
              </Card>

              {/* AI Analysis */}
               {displayTicket.agent_confidence && (
                 <Card>
                   <CardHeader>
                     <CardTitle className="flex items-center gap-2">
                       <Bot className="w-5 h-5 text-blue-600" />
                       AI Analysis
                     </CardTitle>
                   </CardHeader>
                   <CardContent>
                     <div className="space-y-4">
                       <div className="flex items-center justify-between">
                         <span className="text-sm font-medium">
                           Confidence Score
                         </span>
                         <Badge
                           variant="outline"
                           className="text-blue-700 border-blue-200"
                         >
                           {(displayTicket.agent_confidence * 100).toFixed(0)}%
                         </Badge>
                       </div>

                      <div className="p-4 bg-blue-50 rounded-lg">
                        <h4 className="font-medium text-blue-900 mb-2">
                          Recommended Action
                        </h4>
                        <p className="text-sm text-blue-800">
                          Based on similar cases, this appears to be an SMTP
                          timeout configuration issue. Recommend updating
                          timeout values and restarting the email service.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Resolution */}
              <Card>
                <CardHeader>
                   <CardTitle className="flex items-center justify-between">
                     Resolution
                     {displayTicket.status === "resolved" && (
                       <CheckCircle className="w-5 h-5 text-green-600" />
                     )}
                   </CardTitle>
                 </CardHeader>
                 <CardContent>
                   {isEditing ? (
                     <div className="space-y-4">
                       <Textarea
                         placeholder="Enter the resolution details..."
                         value={editedResolution}
                         onChange={(e) => setEditedResolution(e.target.value)}
                         rows={6}
                       />
                       <div className="flex gap-2">
                         <Button
                           onClick={handleSaveResolution}
                           disabled={!editedResolution.trim() || isLoading}
                         >
                           <Save className="w-4 h-4 mr-2" />
                           Save Resolution
                         </Button>
                         <Button
                           variant="outline"
                           onClick={() => setIsEditing(false)}
                         >
                           <X className="w-4 h-4 mr-2" />
                           Cancel
                         </Button>
                       </div>
                     </div>
                   ) : displayTicket.resolution ? (
                     <div className="space-y-3">
                       <p className="text-gray-700 leading-relaxed">
                         {displayTicket.resolution}
                       </p>
                       {displayTicket.resolved_at && (
                         <p className="text-sm text-gray-500">
                           Resolved{" "}
                           {formatDistanceToNow(new Date(displayTicket.resolved_at), {
                             addSuffix: true,
                           })}
                         </p>
                       )}
                     </div>
                   ) : (
                     <div className="text-center py-8 text-gray-500">
                       <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                       <p>No resolution provided yet</p>
                       {displayTicket.status !== "resolved" && (
                         <Button
                           variant="outline"
                           size="sm"
                           className="mt-2"
                           onClick={() => setIsEditing(true)}
                         >
                           Add Resolution
                         </Button>
                       )}
                     </div>
                   )}
                </CardContent>
              </Card>

              {/* Similar Cases */}
              <Card>
                <CardHeader>
                  <CardTitle>Similar Resolved Cases</CardTitle>
                </CardHeader>
                <CardContent>
                   <div className="space-y-4">
                     {mockSimilarCases.map((case_) => (
                       <div
                         key={case_.id}
                         className="p-4 border border-gray-200 rounded-lg"
                       >
                         <div className="flex items-center justify-between mb-2">
                           <Link
                             to={`/tickets/${case_.id}`}
                             className="font-medium text-blue-600 hover:text-blue-800"
                           >
                             #{case_.id} {case_.title}
                           </Link>
                           <Badge
                             variant="outline"
                             className="text-green-700 border-green-200"
                           >
                             {(case_.similarity_score * 100).toFixed(0)}% match
                           </Badge>
                         </div>
                         <p className="text-sm text-gray-700">
                           {case_.resolution}
                         </p>
                       </div>
                     ))}
                   </div>
                 </CardContent>
               </Card>
             </>
           )}

           {activeTab === "workflow" && (
             <WorkflowVisualizer workflow={displayWorkflow} showDetails />
           )}

           {activeTab === "timeline" && (
             <TicketTimeline ticketId={displayTicket.id} showFilters />
           )}

          {activeTab === "comments" && (
            <Card>
              <CardHeader>
                <CardTitle>Comments & Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No comments yet</p>
                  <Button variant="outline" size="sm" className="mt-2">
                    Add Comment
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Ticket Info */}
          <Card>
            <CardHeader>
              <CardTitle>Ticket Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                 <User className="w-4 h-4 text-gray-400" />
                 <div>
                   <p className="text-sm font-medium">Customer</p>
                   <p className="text-sm text-gray-600">{displayTicket.user_email}</p>
                 </div>
               </div>

               <div className="flex items-center gap-3">
                 <FileText className="w-4 h-4 text-gray-400" />
                 <div>
                   <p className="text-sm font-medium">Category</p>
                   <Badge variant="outline">{displayTicket.category}</Badge>
                 </div>
               </div>

               <div className="flex items-center gap-3">
                 <Calendar className="w-4 h-4 text-gray-400" />
                 <div>
                   <p className="text-sm font-medium">Created</p>
                   <p className="text-sm text-gray-600">
                     {format(new Date(displayTicket.created_at), "MMM d, yyyy HH:mm")}
                   </p>
                 </div>
               </div>

               <div className="flex items-center gap-3">
                 <Clock className="w-4 h-4 text-gray-400" />
                 <div>
                   <p className="text-sm font-medium">Last Updated</p>
                   <p className="text-sm text-gray-600">
                     {formatDistanceToNow(new Date(displayTicket.updated_at), {
                       addSuffix: true,
                     })}
                   </p>
                 </div>
               </div>
            </CardContent>
          </Card>

          {/* Knowledge Base Articles */}
          <Card>
            <CardHeader>
              <CardTitle>Related Articles</CardTitle>
            </CardHeader>
            <CardContent>
               <div className="space-y-3">
                 {displayKBArticles.map((article) => (
                   <div
                     key={article.id}
                     className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                   >
                     <div className="flex items-start justify-between mb-2">
                       <h4 className="font-medium text-sm text-gray-900">
                         {article.title}
                       </h4>
                       <Badge variant="outline" className="text-xs">
                         {(article.relevance_score! * 100).toFixed(0)}%
                       </Badge>
                     </div>
                     <p className="text-xs text-gray-600 mb-2">
                       {article.content_preview}
                     </p>
                     <div className="flex items-center gap-1">
                       {article.tags.map((tag) => (
                         <Badge
                           key={tag}
                           variant="secondary"
                           className="text-xs"
                         >
                           {tag}
                         </Badge>
                       ))}
                     </div>
                   </div>
                 ))}
               </div>
             </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
              >
                <Bot className="w-4 h-4 mr-2" />
                Reprocess with AI
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
              >
                <User className="w-4 h-4 mr-2" />
                Assign to Human
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
              >
                <Mail className="w-4 h-4 mr-2" />
                Send Update Email
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View in External System
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
