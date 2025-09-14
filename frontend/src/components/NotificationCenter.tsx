import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Bell, 
  X, 
  Check, 
  AlertTriangle, 
  Info, 
  CheckCircle,
  Clock,
  Bot,
  User,
  Settings,
  MarkAsRead
} from "lucide-react";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'ai_update';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
  metadata?: Record<string, any>;
}

interface NotificationCenterProps {
  notifications?: Notification[];
  onNotificationRead?: (id: string) => void;
  onNotificationDismiss?: (id: string) => void;
  onMarkAllRead?: () => void;
  maxNotifications?: number;
  className?: string;
}

const notificationIcons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertTriangle,
  ai_update: Bot
};

const notificationColors = {
  info: 'text-blue-600 bg-blue-50 border-blue-200',
  success: 'text-green-600 bg-green-50 border-green-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  error: 'text-red-600 bg-red-50 border-red-200',
  ai_update: 'text-purple-600 bg-purple-50 border-purple-200'
};

// Mock notifications
const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'ai_update',
    title: 'Ticket #123 Resolved',
    message: 'AI agent successfully resolved email integration issue with 92% confidence',
    timestamp: '2024-01-15T12:30:00Z',
    read: false,
    actionUrl: '/tickets/123',
    metadata: { ticket_id: 123, confidence: 0.92 }
  },
  {
    id: '2',
    type: 'warning',
    title: 'High Priority Ticket',
    message: 'Ticket #124 marked as urgent - requires immediate attention',
    timestamp: '2024-01-15T12:15:00Z',
    read: false,
    actionUrl: '/tickets/124',
    metadata: { ticket_id: 124, priority: 'urgent' }
  },
  {
    id: '3',
    type: 'success',
    title: 'Knowledge Base Updated',
    message: '5 new articles added to the knowledge base from documentation crawl',
    timestamp: '2024-01-15T11:45:00Z',
    read: true,
    actionUrl: '/knowledge-base',
    metadata: { articles_added: 5 }
  },
  {
    id: '4',
    type: 'info',
    title: 'System Maintenance',
    message: 'Scheduled maintenance window: Jan 16, 2:00 AM - 4:00 AM UTC',
    timestamp: '2024-01-15T10:30:00Z',
    read: true,
    metadata: { maintenance_window: '2024-01-16T02:00:00Z' }
  },
  {
    id: '5',
    type: 'error',
    title: 'Integration Error',
    message: 'Slack integration connection failed - please check configuration',
    timestamp: '2024-01-15T09:15:00Z',
    read: false,
    actionUrl: '/settings',
    metadata: { integration: 'slack', error_code: 'AUTH_FAILED' }
  }
];

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications = mockNotifications,
  onNotificationRead,
  onNotificationDismiss,
  onMarkAllRead,
  maxNotifications = 20,
  className = ""
}) => {
  const [localNotifications, setLocalNotifications] = useState(notifications);

  useEffect(() => {
    setLocalNotifications(notifications);
  }, [notifications]);

  const unreadCount = localNotifications.filter(n => !n.read).length;
  const displayNotifications = localNotifications.slice(0, maxNotifications);

  const handleMarkAsRead = (id: string) => {
    setLocalNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ));
    onNotificationRead?.(id);
  };

  const handleDismiss = (id: string) => {
    setLocalNotifications(prev => prev.filter(n => n.id !== id));
    onNotificationDismiss?.(id);
  };

  const handleMarkAllRead = () => {
    setLocalNotifications(prev => prev.map(n => ({ ...n, read: true })));
    onMarkAllRead?.();
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-600" />
            Notifications
            {unreadCount > 0 && (
              <Badge variant="destructive" className="text-xs">
                {unreadCount}
              </Badge>
            )}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
                <Check className="w-4 h-4 mr-1" />
                Mark All Read
              </Button>
            )}
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <ScrollArea className="h-[400px]">
          {displayNotifications.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-gray-500 px-6">
              <div className="text-center">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No notifications</p>
              </div>
            </div>
          ) : (
            <div className="space-y-1 p-4">
              {displayNotifications.map((notification) => {
                const Icon = notificationIcons[notification.type];
                const colorClass = notificationColors[notification.type];
                
                return (
                  <div
                    key={notification.id}
                    className={cn(
                      "flex items-start gap-3 p-3 rounded-lg transition-all duration-200 cursor-pointer",
                      !notification.read && "bg-blue-50 border border-blue-100",
                      notification.read && "hover:bg-gray-50"
                    )}
                    onClick={() => !notification.read && handleMarkAsRead(notification.id)}
                  >
                    <div className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full border",
                      colorClass
                    )}>
                      <Icon className="w-4 h-4" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={cn(
                          "font-medium text-sm",
                          !notification.read && "text-gray-900",
                          notification.read && "text-gray-700"
                        )}>
                          {notification.title}
                        </h4>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        )}
                      </div>
                      
                      <p className={cn(
                        "text-sm leading-relaxed",
                        !notification.read && "text-gray-700",
                        notification.read && "text-gray-600"
                      )}>
                        {notification.message}
                      </p>
                      
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                        </span>
                        
                        {notification.actionUrl && (
                          <Link to={notification.actionUrl}>
                            <Button variant="ghost" size="sm" className="text-xs h-6">
                              View Details
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-1">
                      {!notification.read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleMarkAsRead(notification.id);
                          }}
                          className="h-6 w-6 p-0"
                        >
                          <Check className="w-3 h-3" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDismiss(notification.id);
                        }}
                        className="h-6 w-6 p-0 text-gray-400 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};