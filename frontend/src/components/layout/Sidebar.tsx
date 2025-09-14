import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAppContext } from "@/contexts/AppContext";
import { 
  LayoutDashboard, 
  Ticket, 
  BookOpen, 
  BarChart3, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Wifi,
  WifiOff,
  Bot,
  FileText,
  Zap
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'Tickets',
    href: '/tickets',
    icon: Ticket,
  },
  {
    name: 'Live Processing',
    href: '/processing',
    icon: Bot,
  },
  {
    name: 'Knowledge Base',
    href: '/knowledge-base',
    icon: BookOpen,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: FileText,
  },
  {
    name: 'Integrations',
    href: '/integrations',
    icon: Zap,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export const Sidebar = () => {
  const { 
    sidebarCollapsed, 
    setSidebarCollapsed, 
    connectionStatus, 
    metrics,
    connectWebSocket 
  } = useAppContext();
  const location = useLocation();

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <Wifi className="w-4 h-4 text-yellow-500 animate-pulse" />;
      case 'error':
        return <WifiOff className="w-4 h-4 text-red-500" />;
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />;
    }
  };

  const getConnectionText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className={cn(
      "flex flex-col h-full bg-white border-r border-gray-200 transition-all duration-300",
      sidebarCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">TicketFlow</h1>
              <p className="text-xs text-gray-500">AI Agent</p>
            </div>
          </div>
        )}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="p-1"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link key={item.name} to={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={cn(
                    "w-full justify-start",
                    sidebarCollapsed && "px-2",
                    isActive && "bg-blue-600 text-white hover:bg-blue-700"
                  )}
                >
                  <Icon className={cn("w-4 h-4", !sidebarCollapsed && "mr-2")} />
                  {!sidebarCollapsed && item.name}
                </Button>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Connection Status & Quick Stats */}
      <div className="p-4 border-t border-gray-200">
        {/* Connection Status */}
        <div className={cn(
          "flex items-center gap-2 mb-4",
          sidebarCollapsed && "justify-center"
        )}>
          {getConnectionIcon()}
          {!sidebarCollapsed && (
            <div className="flex-1">
              <p className="text-xs font-medium">{getConnectionText()}</p>
              {connectionStatus === 'disconnected' && (
                <Button
                  variant="link"
                  size="sm"
                  onClick={connectWebSocket}
                  className="p-0 h-auto text-xs text-blue-600"
                >
                  Reconnect
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        {!sidebarCollapsed && metrics && (
          <div className="bg-gray-50 rounded-lg p-3">
            <h3 className="text-xs font-semibold text-gray-700 mb-2">Quick Stats</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Total Tickets</span>
                <Badge variant="secondary" className="text-xs">
                  {metrics.total_tickets}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Auto-Resolved</span>
                <Badge variant="secondary" className="text-xs">
                  {(metrics.success_rate * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Today</span>
                <Badge variant="secondary" className="text-xs">
                  {metrics.tickets_today}
                </Badge>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};