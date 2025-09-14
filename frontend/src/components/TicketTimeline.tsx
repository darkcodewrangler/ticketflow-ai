import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  Clock, 
  User, 
  Bot, 
  MessageSquare, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  Edit,
  Mail,
  Phone,
  ExternalLink
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { cn } from "@/lib/utils";

interface TimelineEvent {
  id: string;
  type: 'created' | 'updated' | 'comment' | 'status_change' | 'assignment' | 'resolution' | 'escalation' | 'ai_processing';
  title: string;
  description?: string;
  timestamp: string;
  actor: {
    type: 'user' | 'ai' | 'system';
    name: string;
    avatar?: string;
  };
  metadata?: Record<string, any>;
}

interface TicketTimelineProps {
  ticketId: number;
  events?: TimelineEvent[];
  showFilters?: boolean;
  maxEvents?: number;
  className?: string;
}

const eventIcons = {
  created: FileText,
  updated: Edit,
  comment: MessageSquare,
  status_change: AlertTriangle,
  assignment: User,
  resolution: CheckCircle,
  escalation: AlertTriangle,
  ai_processing: Bot
};

const eventColors = {
  created: 'text-blue-600 bg-blue-50 border-blue-200',
  updated: 'text-gray-600 bg-gray-50 border-gray-200',
  comment: 'text-purple-600 bg-purple-50 border-purple-200',
  status_change: 'text-orange-600 bg-orange-50 border-orange-200',
  assignment: 'text-green-600 bg-green-50 border-green-200',
  resolution: 'text-green-600 bg-green-50 border-green-200',
  escalation: 'text-red-600 bg-red-50 border-red-200',
  ai_processing: 'text-blue-600 bg-blue-50 border-blue-200'
};

// Mock timeline events
const mockEvents: TimelineEvent[] = [
  {
    id: '1',
    type: 'created',
    title: 'Ticket Created',
    description: 'New support ticket submitted via web form',
    timestamp: '2024-01-15T10:30:00Z',
    actor: { type: 'user', name: 'John Doe', avatar: '/placeholder.svg' },
    metadata: { source: 'web', ip: '192.168.1.100' }
  },
  {
    id: '2',
    type: 'ai_processing',
    title: 'AI Analysis Started',
    description: 'Ticket automatically queued for AI agent processing',
    timestamp: '2024-01-15T10:30:15Z',
    actor: { type: 'ai', name: 'TicketFlow AI' }
  },
  {
    id: '3',
    type: 'ai_processing',
    title: 'Knowledge Base Search',
    description: 'Found 3 relevant articles with 87% relevance score',
    timestamp: '2024-01-15T10:30:45Z',
    actor: { type: 'ai', name: 'TicketFlow AI' },
    metadata: { articles_found: 3, relevance_score: 0.87 }
  },
  {
    id: '4',
    type: 'ai_processing',
    title: 'Similar Cases Analysis',
    description: 'Analyzed 15 similar cases, found 2 with high similarity',
    timestamp: '2024-01-15T10:31:20Z',
    actor: { type: 'ai', name: 'TicketFlow AI' },
    metadata: { cases_analyzed: 15, similar_found: 2 }
  },
  {
    id: '5',
    type: 'status_change',
    title: 'Status Changed to Processing',
    description: 'AI agent confidence: 85%',
    timestamp: '2024-01-15T10:31:45Z',
    actor: { type: 'ai', name: 'TicketFlow AI' },
    metadata: { from_status: 'new', to_status: 'processing', confidence: 0.85 }
  },
  {
    id: '6',
    type: 'resolution',
    title: 'Ticket Resolved',
    description: 'Solution generated and applied successfully',
    timestamp: '2024-01-15T10:32:30Z',
    actor: { type: 'ai', name: 'TicketFlow AI' },
    metadata: { resolution_confidence: 0.92, auto_resolved: true }
  }
];

export const TicketTimeline: React.FC<TicketTimelineProps> = ({
  ticketId,
  events = mockEvents,
  showFilters = true,
  maxEvents = 50,
  className = ""
}) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [showOnlyAI, setShowOnlyAI] = useState(false);

  const filteredEvents = events
    .filter(event => {
      if (filterType !== 'all' && event.type !== filterType) return false;
      if (showOnlyAI && event.actor.type !== 'ai') return false;
      return true;
    })
    .slice(0, maxEvents);

  const getActorAvatar = (actor: TimelineEvent['actor']) => {
    if (actor.type === 'ai') {
      return (
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
      );
    }
    
    if (actor.type === 'system') {
      return (
        <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
          <Clock className="w-4 h-4 text-white" />
        </div>
      );
    }

    return (
      <Avatar className="w-8 h-8">
        <AvatarImage src={actor.avatar} alt={actor.name} />
        <AvatarFallback>{actor.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
      </Avatar>
    );
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Activity Timeline</CardTitle>
          {showFilters && (
            <div className="flex items-center gap-2">
              <Button
                variant={showOnlyAI ? "default" : "outline"}
                size="sm"
                onClick={() => setShowOnlyAI(!showOnlyAI)}
              >
                <Bot className="w-4 h-4 mr-1" />
                AI Only
              </Button>
              <Button variant="outline" size="sm">
                <FileText className="w-4 h-4 mr-1" />
                Export
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No timeline events found</p>
            </div>
          ) : (
            filteredEvents.map((event, index) => {
              const EventIcon = eventIcons[event.type];
              const isLast = index === filteredEvents.length - 1;
              const eventStyle = eventColors[event.type];
              
              return (
                <div key={event.id} className="relative">
                  {/* Timeline line */}
                  {!isLast && (
                    <div className="absolute left-4 top-12 w-0.5 h-16 bg-gray-200"></div>
                  )}
                  
                  <div className="flex items-start gap-3">
                    {/* Actor avatar */}
                    {getActorAvatar(event.actor)}
                    
                    {/* Event content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className={cn(
                          "flex items-center justify-center w-6 h-6 rounded-full border",
                          eventStyle
                        )}>
                          <EventIcon className="w-3 h-3" />
                        </div>
                        <h4 className="font-medium text-gray-900">{event.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          {event.actor.name}
                        </Badge>
                      </div>
                      
                      {event.description && (
                        <p className="text-sm text-gray-600 mb-2 ml-8">
                          {event.description}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500 ml-8">
                        <span>
                          {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                        </span>
                        <span>
                          {format(new Date(event.timestamp), 'MMM d, HH:mm')}
                        </span>
                      </div>
                      
                      {/* Event metadata */}
                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div className="mt-2 ml-8 p-2 bg-gray-50 rounded text-xs">
                          <div className="grid grid-cols-2 gap-1">
                            {Object.entries(event.metadata).map(([key, value]) => (
                              <div key={key} className="flex justify-between">
                                <span className="text-gray-600">{key}:</span>
                                <span className="font-medium">
                                  {typeof value === 'number' && key.includes('score') 
                                    ? `${(value * 100).toFixed(0)}%`
                                    : String(value)
                                  }
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};