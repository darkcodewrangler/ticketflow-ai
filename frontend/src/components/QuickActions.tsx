import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  Bot, 
  Search, 
  Settings, 
  Download,
  Upload,
  RefreshCw,
  Zap,
  FileText,
  BarChart3,
  Users,
  Globe
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAppContext } from "@/contexts/AppContext";
import { showSuccess, showError, showLoading } from "@/utils/toast";
import { cn } from "@/lib/utils";

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => void | Promise<void>;
  variant?: 'default' | 'outline' | 'secondary';
  badge?: string;
  disabled?: boolean;
  href?: string;
}

interface QuickActionsProps {
  className?: string;
  showTitle?: boolean;
  maxActions?: number;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  className = "",
  showTitle = true,
  maxActions = 8
}) => {
  const [loading, setLoading] = useState<string | null>(null);
  const { refreshMetrics, connectWebSocket, connectionStatus } = useAppContext();

  const handleRefreshMetrics = async () => {
    try {
      setLoading('refresh');
      await refreshMetrics();
      showSuccess('Metrics refreshed successfully');
    } catch (error) {
      showError('Failed to refresh metrics');
    } finally {
      setLoading(null);
    }
  };

  const handleConnectWebSocket = async () => {
    try {
      setLoading('connect');
      connectWebSocket();
      showSuccess('Connecting to AI agent...');
    } catch (error) {
      showError('Failed to connect to AI agent');
    } finally {
      setLoading(null);
    }
  };

  const handleBulkProcess = async () => {
    try {
      setLoading('bulk');
      const loadingToast = showLoading('Processing all new tickets...');
      
      // Simulate bulk processing
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      showSuccess('Started AI processing for 5 new tickets');
    } catch (error) {
      showError('Failed to start bulk processing');
    } finally {
      setLoading(null);
    }
  };

  const handleExportData = async () => {
    try {
      setLoading('export');
      const loadingToast = showLoading('Preparing data export...');
      
      // Simulate export
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      showSuccess('Data export completed and downloaded');
    } catch (error) {
      showError('Failed to export data');
    } finally {
      setLoading(null);
    }
  };

  const quickActions: QuickAction[] = [
    {
      id: 'new-ticket',
      title: 'Create Ticket',
      description: 'Submit a new support ticket',
      icon: Plus,
      action: () => {},
      href: '/tickets/new',
      variant: 'default'
    },
    {
      id: 'bulk-process',
      title: 'Process All New',
      description: 'Run AI on all new tickets',
      icon: Bot,
      action: handleBulkProcess,
      variant: 'outline',
      badge: '5 new',
      disabled: loading === 'bulk'
    },
    {
      id: 'refresh-metrics',
      title: 'Refresh Data',
      description: 'Update dashboard metrics',
      icon: RefreshCw,
      action: handleRefreshMetrics,
      variant: 'outline',
      disabled: loading === 'refresh'
    },
    {
      id: 'connect-ai',
      title: 'Connect AI Agent',
      description: 'Establish real-time connection',
      icon: Zap,
      action: handleConnectWebSocket,
      variant: 'outline',
      disabled: connectionStatus === 'connected' || loading === 'connect',
      badge: connectionStatus === 'connected' ? 'Connected' : 'Disconnected'
    },
    {
      id: 'search',
      title: 'Search Tickets',
      description: 'Find tickets and knowledge',
      icon: Search,
      action: () => {},
      href: '/tickets',
      variant: 'outline'
    },
    {
      id: 'analytics',
      title: 'View Analytics',
      description: 'Performance insights',
      icon: BarChart3,
      action: () => {},
      href: '/analytics',
      variant: 'outline'
    },
    {
      id: 'export-data',
      title: 'Export Data',
      description: 'Download reports and data',
      icon: Download,
      action: handleExportData,
      variant: 'outline',
      disabled: loading === 'export'
    },
    {
      id: 'settings',
      title: 'Settings',
      description: 'Configure system settings',
      icon: Settings,
      action: () => {},
      href: '/settings',
      variant: 'outline'
    }
  ];

  const displayActions = quickActions.slice(0, maxActions);

  const ActionButton: React.FC<{ action: QuickAction }> = ({ action }) => {
    const Icon = action.icon;
    const isLoading = loading === action.id;

    const buttonContent = (
      <Button
        variant={action.variant || 'outline'}
        className="w-full h-auto p-4 flex flex-col items-center gap-2"
        onClick={action.href ? undefined : action.action}
        disabled={action.disabled || isLoading}
      >
        <div className="flex items-center justify-center w-8 h-8">
          <Icon className={cn("w-5 h-5", isLoading && "animate-spin")} />
        </div>
        <div className="text-center">
          <div className="font-medium text-sm">{action.title}</div>
          <div className="text-xs text-gray-600 mt-1">{action.description}</div>
          {action.badge && (
            <Badge variant="secondary" className="mt-2 text-xs">
              {action.badge}
            </Badge>
          )}
        </div>
      </Button>
    );

    if (action.href) {
      return (
        <Link to={action.href} className="block">
          {buttonContent}
        </Link>
      );
    }

    return buttonContent;
  };

  return (
    <Card className={className}>
      {showTitle && (
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-600" />
            Quick Actions
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={cn("grid gap-3", showTitle ? "" : "p-4")}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {displayActions.map((action) => (
            <ActionButton key={action.id} action={action} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};