import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { SlackSettingsForm } from "@/components/settings/SlackSettingsForm";
import { ResendSettingsForm } from "@/components/settings/ResendSettingsForm";
import { 
  Settings as SettingsIcon, 
  Bot, 
  Mail, 
  Shield, 
  Bell, 
  Save,
  RefreshCw,
  TestTube,
  AlertTriangle,
  CheckCircle,
  Info,
  MessageSquare,
  Webhook,
  User
} from "lucide-react";
import { AppSettings, AgentSettings, GeneralSettings, WebhookSettings, SecuritySettings, NotificationSettings } from "@/types";
import { api } from "@/services/api";
import { showSuccess, showError, showLoading } from "@/utils/toast";

const settingsNavigation = [
  { id: 'general', label: 'General', icon: SettingsIcon },
  { id: 'agent', label: 'AI Agent', icon: Bot },
  { id: 'slack', label: 'Slack Integration', icon: MessageSquare },
  { id: 'email', label: 'Email (Resend)', icon: Mail },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
];

const defaultSettings: AppSettings = {
  general: {
    companyName: "TicketFlow AI",
    supportEmail: "support@ticketflow.ai",
    timezone: "UTC",
    dateFormat: "MM/DD/YYYY",
    language: "en"
  },
  agent: {
    autoResolveThreshold: 0.85,
    enableExternalActions: true,
    maxSimilarCases: 5,
    kbSearchLimit: 10,
    confidenceThreshold: 0.8,
    escalationThreshold: 0.3,
    processingTimeout: 300
  },
  slack: {
    enabled: false,
    botToken: "",
    signingSecret: "",
    channels: {
      escalated: { channelId: "", channelName: "", enabled: false },
      general: { channelId: "", channelName: "", enabled: false },
      agentUpdates: { channelId: "", channelName: "", enabled: false },
      resolutions: { channelId: "", channelName: "", enabled: false },
      alerts: { channelId: "", channelName: "", enabled: false }
    },
    notificationSettings: {
      includeTicketDetails: true,
      mentionUsers: false,
      useThreads: true,
      quietHours: {
        enabled: false,
        startTime: "22:00",
        endTime: "08:00",
        timezone: "UTC"
      }
    }
  },
  resend: {
    enabled: false,
    apiKey: "",
    fromEmail: "",
    fromName: "TicketFlow AI Support",
    replyToEmail: "",
    templates: {
      ticketCreated: {
        enabled: true,
        subject: "Ticket #{{ticket_id}} Created - {{ticket_title}}",
        template: "default"
      },
      ticketResolved: {
        enabled: true,
        subject: "Ticket #{{ticket_id}} Resolved - {{ticket_title}}",
        template: "default"
      },
      ticketEscalated: {
        enabled: true,
        subject: "Urgent: Ticket #{{ticket_id}} Escalated",
        template: "default",
        recipients: []
      },
      processingUpdate: {
        enabled: false,
        subject: "Update on Ticket #{{ticket_id}}",
        template: "default",
        sendOnlyOnCompletion: true
      }
    },
    advanced: {
      maxEmailsPerHour: 100,
      maxEmailsPerDay: 1000,
      retryAttempts: 3,
      retryDelay: 60,
      trackOpens: true,
      trackClicks: true,
      suppressionList: [],
      quietHours: {
        enabled: false,
        startTime: "22:00",
        endTime: "08:00",
        timezone: "UTC"
      }
    }
  },
  webhooks: {
    enabled: false,
    endpoints: []
  },
  security: {
    twoFactorAuth: false,
    sessionTimeout: 3600,
    ipWhitelist: [],
    auditLogging: true
  },
  notifications: {
    emailNotifications: true,
    slackNotifications: false,
    webhookNotifications: false,
    notifyOnResolution: true,
    notifyOnEscalation: true,
    notifyOnFailure: true
  }
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await api.getSettings();
      if (response.success) {
        setSettings({ ...defaultSettings, ...response.data });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      showError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      await api.updateSettings(settings);
      showSuccess('Settings saved successfully!');
    } catch (error) {
      showError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateGeneralSettings = (updates: Partial<GeneralSettings>) => {
    setSettings(prev => ({
      ...prev,
      general: { ...prev.general, ...updates }
    }));
  };

  const updateAgentSettings = (updates: Partial<AgentSettings>) => {
    setSettings(prev => ({
      ...prev,
      agent: { ...prev.agent, ...updates }
    }));
  };

  const GeneralSettingsForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-gray-600" />
          General Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="company-name">Company Name</Label>
            <Input
              id="company-name"
              value={settings.general.companyName}
              onChange={(e) => updateGeneralSettings({ companyName: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="support-email">Support Email</Label>
            <Input
              id="support-email"
              type="email"
              value={settings.general.supportEmail}
              onChange={(e) => updateGeneralSettings({ supportEmail: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="timezone">Timezone</Label>
            <Select value={settings.general.timezone} onValueChange={(value) => updateGeneralSettings({ timezone: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="UTC">UTC</SelectItem>
                <SelectItem value="America/New_York">Eastern Time</SelectItem>
                <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                <SelectItem value="Europe/London">London</SelectItem>
                <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="date-format">Date Format</Label>
            <Select value={settings.general.dateFormat} onValueChange={(value) => updateGeneralSettings({ dateFormat: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="language">Language</Label>
            <Select value={settings.general.language} onValueChange={(value) => updateGeneralSettings({ language: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
                <SelectItem value="fr">French</SelectItem>
                <SelectItem value="de">German</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const AgentSettingsForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-600" />
          AI Agent Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <Label>Auto-Resolve Confidence Threshold</Label>
              <div className="mt-2">
                <Slider
                  value={[settings.agent.autoResolveThreshold]}
                  onValueChange={(value) => updateAgentSettings({ autoResolveThreshold: value[0] })}
                  max={1}
                  min={0.5}
                  step={0.05}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-500 mt-1">
                  <span>50%</span>
                  <span className="font-medium">{(settings.agent.autoResolveThreshold * 100).toFixed(0)}%</span>
                  <span>100%</span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Minimum confidence required for automatic resolution
              </p>
            </div>

            <div>
              <Label>Escalation Threshold</Label>
              <div className="mt-2">
                <Slider
                  value={[settings.agent.escalationThreshold]}
                  onValueChange={(value) => updateAgentSettings({ escalationThreshold: value[0] })}
                  max={0.8}
                  min={0.1}
                  step={0.05}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-500 mt-1">
                  <span>10%</span>
                  <span className="font-medium">{(settings.agent.escalationThreshold * 100).toFixed(0)}%</span>
                  <span>80%</span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Below this confidence, tickets are escalated to humans
              </p>
            </div>

            <div>
              <Label htmlFor="max-similar">Max Similar Cases to Analyze</Label>
              <Input
                id="max-similar"
                type="number"
                min="1"
                max="20"
                value={settings.agent.maxSimilarCases}
                onChange={(e) => updateAgentSettings({ maxSimilarCases: parseInt(e.target.value) })}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="kb-limit">Knowledge Base Search Limit</Label>
              <Input
                id="kb-limit"
                type="number"
                min="1"
                max="50"
                value={settings.agent.kbSearchLimit}
                onChange={(e) => updateAgentSettings({ kbSearchLimit: parseInt(e.target.value) })}
              />
            </div>

            <div>
              <Label htmlFor="timeout">Processing Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                min="60"
                max="600"
                value={settings.agent.processingTimeout}
                onChange={(e) => updateAgentSettings({ processingTimeout: parseInt(e.target.value) })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Enable External Actions</Label>
                <p className="text-sm text-gray-600">
                  Allow agent to perform external API calls
                </p>
              </div>
              <Switch
                checked={settings.agent.enableExternalActions}
                onCheckedChange={(checked) => updateAgentSettings({ enableExternalActions: checked })}
              />
            </div>
          </div>
        </div>

        <div className="p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Performance Impact</h4>
              <p className="text-sm text-blue-800 mt-1">
                Higher thresholds improve accuracy but may reduce automation rate. 
                Lower thresholds increase automation but may reduce quality.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const SecuritySettingsForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-red-600" />
          Security Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="p-4 bg-yellow-50 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900">Security Notice</h4>
              <p className="text-sm text-yellow-800 mt-1">
                Security settings require administrator privileges. Changes will be logged and audited.
              </p>
            </div>
          </div>
        </div>

        <div className="text-center py-8">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Security Configuration</h3>
          <p className="text-gray-600 mb-4">
            Advanced security settings are available in the enterprise version
          </p>
          <Button variant="outline">
            Learn More
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Configure AI agent behavior and system preferences
          </p>
        </div>
      </div>

      <div className="flex h-full">
        {/* Settings Navigation */}
        <div className="w-64 border-r bg-gray-50 p-4 rounded-l-lg">
          <nav className="space-y-2">
            {settingsNavigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center px-3 py-2 text-left rounded-md transition-colors ${
                  activeTab === item.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="flex-1 p-6 bg-white rounded-r-lg">
          <div className="max-w-4xl">
            {activeTab === 'general' && <GeneralSettingsForm />}
            {activeTab === 'agent' && <AgentSettingsForm />}
            {activeTab === 'slack' && (
              <SlackSettingsForm
                settings={settings.slack}
                onSettingsChange={(slackSettings) => setSettings(prev => ({ ...prev, slack: slackSettings }))}
              />
            )}
            {activeTab === 'email' && (
              <ResendSettingsForm
                settings={settings.resend}
                onSettingsChange={(resendSettings) => setSettings(prev => ({ ...prev, resend: resendSettings }))}
              />
            )}
            {activeTab === 'webhooks' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Webhook className="w-5 h-5 text-purple-600" />
                    Webhook Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <Webhook className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Webhook Integration</h3>
                    <p className="text-gray-600 mb-4">
                      Configure webhooks to send real-time notifications to external systems
                    </p>
                    <Button variant="outline">
                      Coming Soon
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
            {activeTab === 'security' && <SecuritySettingsForm />}
            {activeTab === 'notifications' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bell className="w-5 h-5 text-green-600" />
                    Notification Preferences
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Email Notifications</Label>
                        <p className="text-sm text-gray-600">Receive email alerts for important events</p>
                      </div>
                      <Switch
                        checked={settings.notifications.emailNotifications}
                        onCheckedChange={(checked) => setSettings(prev => ({
                          ...prev,
                          notifications: { ...prev.notifications, emailNotifications: checked }
                        }))}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Slack Notifications</Label>
                        <p className="text-sm text-gray-600">Send notifications to Slack channels</p>
                      </div>
                      <Switch
                        checked={settings.notifications.slackNotifications}
                        onCheckedChange={(checked) => setSettings(prev => ({
                          ...prev,
                          notifications: { ...prev.notifications, slackNotifications: checked }
                        }))}
                      />
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <h4 className="font-medium">Event Notifications</h4>
                      
                      <div className="flex items-center justify-between">
                        <Label>Ticket Resolutions</Label>
                        <Switch
                          checked={settings.notifications.notifyOnResolution}
                          onCheckedChange={(checked) => setSettings(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, notifyOnResolution: checked }
                          }))}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label>Ticket Escalations</Label>
                        <Switch
                          checked={settings.notifications.notifyOnEscalation}
                          onCheckedChange={(checked) => setSettings(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, notifyOnEscalation: checked }
                          }))}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label>Processing Failures</Label>
                        <Switch
                          checked={settings.notifications.notifyOnFailure}
                          onCheckedChange={(checked) => setSettings(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, notifyOnFailure: checked }
                          }))}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Save Button */}
            <div className="mt-8 pt-6 border-t">
              <div className="flex items-center gap-3">
                <Button onClick={saveSettings} disabled={saving}>
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Settings'}
                </Button>
                <Button variant="outline" onClick={loadSettings} disabled={loading}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reset Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}