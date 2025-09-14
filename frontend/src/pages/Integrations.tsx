import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  Plus, 
  Settings, 
  Check, 
  X, 
  ExternalLink,
  Webhook,
  Mail,
  MessageSquare,
  Database,
  Cloud,
  Zap,
  Shield,
  AlertTriangle,
  Info
} from "lucide-react";
import { showSuccess, showError, showLoading } from "@/utils/toast";

interface Integration {
  id: string;
  name: string;
  description: string;
  category: 'communication' | 'database' | 'monitoring' | 'automation' | 'security';
  status: 'connected' | 'disconnected' | 'error';
  icon: React.ComponentType<{ className?: string }>;
  config: Record<string, any>;
  lastSync?: string;
  features: string[];
}

const availableIntegrations: Integration[] = [
  {
    id: 'slack',
    name: 'Slack',
    description: 'Send notifications and updates to Slack channels',
    category: 'communication',
    status: 'connected',
    icon: MessageSquare,
    config: {
      webhook_url: 'https://hooks.slack.com/services/...',
      channel: '#support',
      enabled: true
    },
    lastSync: '2024-01-15T12:30:00Z',
    features: ['Real-time notifications', 'Ticket updates', 'Alert management']
  },
  {
    id: 'email',
    name: 'Email SMTP',
    description: 'Send email notifications to customers and staff',
    category: 'communication',
    status: 'connected',
    icon: Mail,
    config: {
      smtp_host: 'smtp.gmail.com',
      smtp_port: 587,
      username: 'support@company.com',
      enabled: true
    },
    lastSync: '2024-01-15T12:25:00Z',
    features: ['Customer notifications', 'Staff alerts', 'Ticket updates']
  },
  {
    id: 'webhook',
    name: 'Custom Webhooks',
    description: 'Send HTTP requests to external systems',
    category: 'automation',
    status: 'disconnected',
    icon: Webhook,
    config: {
      endpoints: [],
      enabled: false
    },
    features: ['Custom integrations', 'Real-time data sync', 'Event triggers']
  },
  {
    id: 'database',
    name: 'External Database',
    description: 'Connect to external databases for data sync',
    category: 'database',
    status: 'error',
    icon: Database,
    config: {
      host: '',
      port: 5432,
      database: '',
      enabled: false
    },
    features: ['Data synchronization', 'Custom queries', 'Backup integration']
  },
  {
    id: 'monitoring',
    name: 'System Monitoring',
    description: 'Monitor system health and performance',
    category: 'monitoring',
    status: 'disconnected',
    icon: Cloud,
    config: {
      api_key: '',
      enabled: false
    },
    features: ['Performance metrics', 'Health checks', 'Alert management']
  },
  {
    id: 'zapier',
    name: 'Zapier',
    description: 'Connect with 5000+ apps through Zapier',
    category: 'automation',
    status: 'disconnected',
    icon: Zap,
    config: {
      api_key: '',
      enabled: false
    },
    features: ['App connections', 'Workflow automation', 'Data sync']
  }
];

const categoryIcons = {
  communication: MessageSquare,
  database: Database,
  monitoring: Cloud,
  automation: Zap,
  security: Shield
};

const categoryColors = {
  communication: 'bg-blue-100 text-blue-800',
  database: 'bg-green-100 text-green-800',
  monitoring: 'bg-purple-100 text-purple-800',
  automation: 'bg-yellow-100 text-yellow-800',
  security: 'bg-red-100 text-red-800'
};

export default function Integrations() {
  const [integrations, setIntegrations] = useState<Integration[]>(availableIntegrations);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [loading, setLoading] = useState(false);

  const filteredIntegrations = integrations.filter(integration => 
    selectedCategory === 'all' || integration.category === selectedCategory
  );

  const handleToggleIntegration = async (integrationId: string) => {
    try {
      setLoading(true);
      const integration = integrations.find(i => i.id === integrationId);
      if (!integration) return;

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newStatus = integration.status === 'connected' ? 'disconnected' : 'connected';
      
      setIntegrations(prev => prev.map(i => 
        i.id === integrationId 
          ? { ...i, status: newStatus, config: { ...i.config, enabled: newStatus === 'connected' } }
          : i
      ));

      showSuccess(`${integration.name} ${newStatus === 'connected' ? 'connected' : 'disconnected'} successfully`);
    } catch (error) {
      showError('Failed to update integration');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigureIntegration = (integration: Integration) => {
    setSelectedIntegration(integration);
    setConfigDialogOpen(true);
  };

  const handleSaveConfig = async () => {
    if (!selectedIntegration) return;

    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      setIntegrations(prev => prev.map(i => 
        i.id === selectedIntegration.id 
          ? { ...i, config: selectedIntegration.config }
          : i
      ));

      setConfigDialogOpen(false);
      showSuccess('Configuration saved successfully');
    } catch (error) {
      showError('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (integrationId: string) => {
    try {
      setLoading(true);
      const integration = integrations.find(i => i.id === integrationId);
      if (!integration) return;

      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Random success/failure for demo
      const success = Math.random() > 0.3;
      
      if (success) {
        showSuccess(`${integration.name} connection test successful`);
        setIntegrations(prev => prev.map(i => 
          i.id === integrationId 
            ? { ...i, status: 'connected', lastSync: new Date().toISOString() }
            : i
        ));
      } else {
        showError(`${integration.name} connection test failed`);
        setIntegrations(prev => prev.map(i => 
          i.id === integrationId 
            ? { ...i, status: 'error' }
            : i
        ));
      }
    } catch (error) {
      showError('Connection test failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: Integration['status']) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: Integration['status']) => {
    switch (status) {
      case 'connected':
        return <Check className="w-4 h-4" />;
      case 'error':
        return <X className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
          <p className="text-gray-600 mt-1">
            Connect TicketFlow with your favorite tools and services
          </p>
        </div>
        
        <Button className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Custom Integration
        </Button>
      </div>

      {/* Category Filter */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList>
          <TabsTrigger value="all">All Integrations</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="automation">Automation</TabsTrigger>
          <TabsTrigger value="database">Database</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredIntegrations.map((integration) => {
          const Icon = integration.icon;
          const CategoryIcon = categoryIcons[integration.category];
          
          return (
            <Card key={integration.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Icon className="w-6 h-6 text-gray-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{integration.name}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className={categoryColors[integration.category]}>
                          <CategoryIcon className="w-3 h-3 mr-1" />
                          {integration.category}
                        </Badge>
                        <Badge variant="outline" className={getStatusColor(integration.status)}>
                          {getStatusIcon(integration.status)}
                          <span className="ml-1">{integration.status}</span>
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600">{integration.description}</p>
                
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-gray-500">FEATURES</Label>
                  <div className="flex flex-wrap gap-1">
                    {integration.features.slice(0, 2).map((feature) => (
                      <Badge key={feature} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                    {integration.features.length > 2 && (
                      <Badge variant="secondary" className="text-xs">
                        +{integration.features.length - 2} more
                      </Badge>
                    )}
                  </div>
                </div>

                {integration.lastSync && (
                  <p className="text-xs text-gray-500">
                    Last sync: {new Date(integration.lastSync).toLocaleString()}
                  </p>
                )}

                <div className="flex items-center gap-2 pt-2">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={integration.status === 'connected'}
                      onCheckedChange={() => handleToggleIntegration(integration.id)}
                      disabled={loading}
                    />
                    <span className="text-sm">
                      {integration.status === 'connected' ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  
                  <div className="flex-1" />
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleConfigureIntegration(integration)}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestConnection(integration.id)}
                    disabled={loading}
                  >
                    Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedIntegration && (
                <>
                  <selectedIntegration.icon className="w-5 h-5" />
                  Configure {selectedIntegration.name}
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {selectedIntegration && (
            <div className="space-y-6">
              {/* Status Alert */}
              {selectedIntegration.status === 'error' && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-red-900">Connection Error</h4>
                      <p className="text-sm text-red-800 mt-1">
                        There was an issue connecting to {selectedIntegration.name}. 
                        Please check your configuration and try again.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Configuration Form */}
              <div className="space-y-4">
                {selectedIntegration.id === 'slack' && (
                  <>
                    <div>
                      <Label htmlFor="webhook_url">Webhook URL</Label>
                      <Input
                        id="webhook_url"
                        value={selectedIntegration.config.webhook_url || ''}
                        onChange={(e) => setSelectedIntegration({
                          ...selectedIntegration,
                          config: { ...selectedIntegration.config, webhook_url: e.target.value }
                        })}
                        placeholder="https://hooks.slack.com/services/..."
                      />
                    </div>
                    <div>
                      <Label htmlFor="channel">Default Channel</Label>
                      <Input
                        id="channel"
                        value={selectedIntegration.config.channel || ''}
                        onChange={(e) => setSelectedIntegration({
                          ...selectedIntegration,
                          config: { ...selectedIntegration.config, channel: e.target.value }
                        })}
                        placeholder="#support"
                      />
                    </div>
                  </>
                )}

                {selectedIntegration.id === 'email' && (
                  <>
                    <div>
                      <Label htmlFor="smtp_host">SMTP Host</Label>
                      <Input
                        id="smtp_host"
                        value={selectedIntegration.config.smtp_host || ''}
                        onChange={(e) => setSelectedIntegration({
                          ...selectedIntegration,
                          config: { ...selectedIntegration.config, smtp_host: e.target.value }
                        })}
                        placeholder="smtp.gmail.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="smtp_port">SMTP Port</Label>
                      <Input
                        id="smtp_port"
                        type="number"
                        value={selectedIntegration.config.smtp_port || ''}
                        onChange={(e) => setSelectedIntegration({
                          ...selectedIntegration,
                          config: { ...selectedIntegration.config, smtp_port: parseInt(e.target.value) }
                        })}
                        placeholder="587"
                      />
                    </div>
                    <div>
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={selectedIntegration.config.username || ''}
                        onChange={(e) => setSelectedIntegration({
                          ...selectedIntegration,
                          config: { ...selectedIntegration.config, username: e.target.value }
                        })}
                        placeholder="support@company.com"
                      />
                    </div>
                  </>
                )}

                {/* Generic API Key field for other integrations */}
                {!['slack', 'email'].includes(selectedIntegration.id) && (
                  <div>
                    <Label htmlFor="api_key">API Key</Label>
                    <Input
                      id="api_key"
                      type="password"
                      value={selectedIntegration.config.api_key || ''}
                      onChange={(e) => setSelectedIntegration({
                        ...selectedIntegration,
                        config: { ...selectedIntegration.config, api_key: e.target.value }
                      })}
                      placeholder="Enter your API key"
                    />
                  </div>
                )}
              </div>

              {/* Features List */}
              <div>
                <Label className="text-sm font-medium">Available Features</Label>
                <div className="mt-2 space-y-2">
                  {selectedIntegration.features.map((feature) => (
                    <div key={feature} className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-4 border-t">
                <Button onClick={handleSaveConfig} disabled={loading}>
                  {loading ? 'Saving...' : 'Save Configuration'}
                </Button>
                <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => handleTestConnection(selectedIntegration.id)}
                  disabled={loading}
                >
                  Test Connection
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Integration Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Integrations</p>
                <p className="text-2xl font-bold">{integrations.length}</p>
              </div>
              <Zap className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Connected</p>
                <p className="text-2xl font-bold text-green-600">
                  {integrations.filter(i => i.status === 'connected').length}
                </p>
              </div>
              <Check className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Errors</p>
                <p className="text-2xl font-bold text-red-600">
                  {integrations.filter(i => i.status === 'error').length}
                </p>
              </div>
              <X className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Categories</p>
                <p className="text-2xl font-bold">
                  {new Set(integrations.map(i => i.category)).size}
                </p>
              </div>
              <Settings className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}