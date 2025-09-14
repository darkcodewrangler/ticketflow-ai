import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { ActivityItem } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { 
  Ticket, 
  Bot, 
  CheckCircle, 
  AlertTriangle,
  Clock
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ActivityFeedProps {
  items: ActivityItem[];
  maxItems?: number;
  autoScroll?: boolean;
  className?: string;
}

const getActivityIcon = (type: ActivityItem['type']) => {
  switch (type) {
    case 'ticket_created':
      return <Ticket className="w-4 h-4" />;
    case 'agent_update':
      return <Bot className="w-4 h-4" />;
    case 'resolution':
      return <CheckCircle className="w-4 h-4" />;
    case 'escalation':
      return <AlertTriangle className="w-4 h-4" />;
    default:
      return <Clock className="w-4 h-4" />;
  }
};

const getActivityColor = (type: ActivityItem['type']) => {
  switch (type) {
    case 'ticket_created':
      return 'text-blue-600 bg-blue-50';
    case 'agent_update':
      return 'text-purple-600 bg-purple-50';
    case 'resolution':
      return 'text-green-600 bg-green-50';
    case 'escalation':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

const getActivityLabel = (type: ActivityItem['type']) => {
  switch (type) {
    case 'ticket_created':
      return 'New Ticket';
    case 'agent_update':
      return 'AI Agent';
    case 'resolution':
      return 'Resolved';
    case 'escalation':
      return 'Escalated';
    default:
      return 'Activity';
  }
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  items,
  maxItems = 50,
  autoScroll = true,
  className,
}) => {
  const displayItems = items.slice(0, maxItems);

  return (
    <Card className={cn("h-full", className)}>
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          Live Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[400px] px-6">
          {displayItems.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <div className="text-center">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No recent activity</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4 pb-4">
              {displayItems.map((item, index) => (
                <div
                  key={item.id}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg transition-all duration-200",
                    index === 0 && "bg-blue-50 border border-blue-200",
                    index > 0 && "hover:bg-gray-50"
                  )}
                >
                  <div className={cn(
                    "flex items-center justify-center w-8 h-8 rounded-full",
                    getActivityColor(item.type)
                  )}>
                    {getActivityIcon(item.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        {getActivityLabel(item.type)}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-900 leading-relaxed">
                      {item.message}
                    </p>
                    
                    {item.metadata && (
                      <div className="mt-2 text-xs text-gray-500">
                        {item.metadata.ticket_id && (
                          <span>Ticket #{item.metadata.ticket_id}</span>
                        )}
                        {item.metadata.step && (
                          <span className="ml-2">Step: {item.metadata.step}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};