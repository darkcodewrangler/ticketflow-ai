import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  MessageSquare, 
  TestTube, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Hash,
  Clock,
  Users
} from "lucide-react";
import { SlackSettings, SlackChannelConfig } from "@/types";
import { api } from "@/services/api";
import { showSuccess, showError, showLoading } from "@/utils/toast";

interface SlackSettingsFormProps {
  settings: SlackSettings;
  onSettingsChange: (settings: SlackSettings) => void;
}

const channelTypes = {
  escalated: {
    label: "Escalated Tickets",
    description: "High priority notifications for escalated tickets",
    icon: AlertTriangle,
    color: "text-red-600"
  },
  general: {
    label: "General Tickets",
    description: "Standard ticket notifications",
    icon: MessageSquare,
    color: "text-blue-600"
  },
  agentUpdates: {
    label: "AI Processing Updates",
    description: "Real-time AI agent processing notifications",
    icon: CheckCircle,
    color: "text-green-600"
  },
  resolutions: {
    label: "Ticket Resolutions",
    description: "Notifications when tickets are resolved",
    icon: CheckCircle,
    color: "text-green-600"
  },
  alerts: {
    label: "System Alerts",
    description: "System errors and important alerts",
    icon: AlertTriangle,
    color: "text-orange-600"
  }
};

const timezones = [
  "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", 
  "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
];

export const SlackSettingsForm: React.FC<SlackSettingsFormProps> = ({
  settings,
  onSettingsChange
}) => {
  const [availableChannels, setAvailableChannels] = useState<Array<{ id: string; name: string }>>([]);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [loadingChannels, setLoadingChannels] = useState(false);

  useEffect(() => {
    if (settings.enabled && settings.botToken) {
      loadSlackChannels();
    }
  }, [settings.enabled, settings.botToken]);

  const loadSlackChannels = async () => {
    try {
      setLoadingChannels(true);
      const response = await api.getSlackChannels();
      if (response.success) {
        setAvailableChannels(response.data);
      }
    } catch (error) {
      console.error('Failed to load Slack channels:', error);
    } finally {
      setLoadingChannels(false);
    }
  };

  const updateSettings = (updates: Partial<SlackSettings>) => {
    onSettingsChange({ ...settings, ...updates });
  };

  const updateChannel = (channelType: keyof SlackSettings['channels'], channel: Partial<SlackChannelConfig>) => {
    const updatedChannels = {
      ...settings.channels,
      [channelType]: { ...settings.channels[channelType], ...channel }
    };
    updateSettings({ channels: updatedChannels });
  };

  const updateNotificationSetting = (key: string, value: any) => {
    const updatedSettings = {
      ...settings.notificationSettings,
      [key]: value
    };
    updateSettings({ notificationSettings: updatedSettings });
  };

  const updateQuietHours = (key: string, value: any) => {
    const updatedQuietHours = {
      ...settings.notificationSettings.quietHours,
      [key]: value
    };
    updateNotificationSetting('quietHours', updatedQuietHours);
  };

  const testChannelConnection = async (channelType: string, channelId: string) => {
    if (!channelId) {
      showError("Please select a channel first");
      return;
    }

    try {
      setTestingConnection(channelType);
      const response = await api.testSlackConnection(channelId);
      
      if (response.success) {
        showSuccess(`Test message sent to channel successfully!`);
      } else {
        showError(response.data.message || "Failed to send test message");
      }
    } catch (error) {
      showError("Failed to test channel connection");
    } finally {
      setTestingConnection(null);
    }
  };

  const ChannelSelector: React.FC<{
    channelType: keyof SlackSettings['channels'];
    config: typeof channelTypes[keyof typeof channelTypes];
  }> = ({ channelType, config }) => {
    const channel = settings.channels[channelType];
    const Icon = config.icon;

    return (
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <Icon className={`w-5 h-5 ${config.color}`} />
              <div>
                <h4 className="font-medium">{config.label}</h4>
                <p className="text-sm text-gray-600">{config.description}</p>
              </div>
            </div>
            <Switch
              checked={channel.enabled}
              onCheckedChange={(enabled) => updateChannel(channelType, { enabled })}
            />
          </div>

          {channel.enabled && (
            <div className="space-y-3">
              <div>
                <Label htmlFor={`channel-${channelType}`}>Slack Channel</Label>
                <div className="flex gap-2 mt-1">
                  <Select
                    value={channel.channelId}
                    onValueChange={(channelId) => {
                      const selectedChannel = availableChannels.find(ch => ch.id === channelId);
                      updateChannel(channelType, {
                        channelId,
                        channelName: selectedChannel ? `#${selectedChannel.name}` : ''
                      });
                    }}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select a channel" />
                    </SelectTrigger>
                    <SelectContent>
                      {loadingChannels ? (
                        <SelectItem value="" disabled>Loading channels...</SelectItem>
                      ) : (
                        availableChannels.map((ch) => (
                          <SelectItem key={ch.id} value={ch.id}>
                            <div className="flex items-center gap-2">
                              <Hash className="w-4 h-4" />
                              {ch.name}
                            </div>
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testChannelConnection(channelType, channel.channelId)}
                    disabled={!channel.channelId || testingConnection === channelType}
                  >
                    <TestTube className="w-4 h-4 mr-1" />
                    {testingConnection === channelType ? 'Testing...' : 'Test'}
                  </Button>
                </div>
                {channel.channelName && (
                  <p className="text-sm text-gray-500 mt-1">
                    Selected: {channel.channelName}
                  </p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Basic Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            Slack Integration Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable Slack Integration</Label>
              <p className="text-sm text-gray-600">Send notifications to Slack channels</p>
            </div>
            <Switch
              checked={settings.enabled}
              onCheckedChange={(enabled) => updateSettings({ enabled })}
            />
          </div>

          {settings.enabled && (
            <>
              <Separator />
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label htmlFor="bot-token">Bot Token *</Label>
                  <Input
                    id="bot-token"
                    type="password"
                    placeholder="xoxb-your-bot-token"
                    value={settings.botToken}
                    onChange={(e) => updateSettings({ botToken: e.target.value })}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Slack Bot User OAuth Token from your app settings
                  </p>
                </div>
                <div>
                  <Label htmlFor="signing-secret">Signing Secret *</Label>
                  <Input
                    id="signing-secret"
                    type="password"
                    placeholder="Your app's signing secret"
                    value={settings.signingSecret}
                    onChange={(e) => updateSettings({ signingSecret: e.target.value })}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Used to verify requests from Slack
                  </p>
                </div>
              </div>

              {settings.botToken && (
                <div className="mt-4">
                  <Button
                    variant="outline"
                    onClick={loadSlackChannels}
                    disabled={loadingChannels}
                  >
                    {loadingChannels ? 'Loading...' : 'Load Channels'}
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Channel Configuration */}
      {settings.enabled && (
        <Card>
          <CardHeader>
            <CardTitle>Channel Configuration</CardTitle>
            <p className="text-sm text-gray-600">
              Configure which channels receive different types of notifications
            </p>
          </CardHeader>
          <CardContent>
            {Object.entries(channelTypes).map(([channelType, config]) => (
              <ChannelSelector
                key={channelType}
                channelType={channelType as keyof SlackSettings['channels']}
                config={config}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Notification Preferences */}
      {settings.enabled && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              Notification Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Include Ticket Details</Label>
                <p className="text-sm text-gray-600">Include ticket content in notifications</p>
              </div>
              <Switch
                checked={settings.notificationSettings.includeTicketDetails}
                onCheckedChange={(checked) => updateNotificationSetting('includeTicketDetails', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Mention Users</Label>
                <p className="text-sm text-gray-600">@mention relevant users in notifications</p>
              </div>
              <Switch
                checked={settings.notificationSettings.mentionUsers}
                onCheckedChange={(checked) => updateNotificationSetting('mentionUsers', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Use Threads</Label>
                <p className="text-sm text-gray-600">Post follow-up messages as thread replies</p>
              </div>
              <Switch
                checked={settings.notificationSettings.useThreads}
                onCheckedChange={(checked) => updateNotificationSetting('useThreads', checked)}
              />
            </div>

            <Separator />

            {/* Quiet Hours */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <Label>Quiet Hours</Label>
                </div>
                <Switch
                  checked={settings.notificationSettings.quietHours.enabled}
                  onCheckedChange={(enabled) => updateQuietHours('enabled', enabled)}
                />
              </div>

              {settings.notificationSettings.quietHours.enabled && (
                <div className="grid grid-cols-3 gap-4 ml-6">
                  <div>
                    <Label htmlFor="start-time">Start Time</Label>
                    <Input
                      id="start-time"
                      type="time"
                      value={settings.notificationSettings.quietHours.startTime}
                      onChange={(e) => updateQuietHours('startTime', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="end-time">End Time</Label>
                    <Input
                      id="end-time"
                      type="time"
                      value={settings.notificationSettings.quietHours.endTime}
                      onChange={(e) => updateQuietHours('endTime', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="timezone">Timezone</Label>
                    <Select
                      value={settings.notificationSettings.quietHours.timezone}
                      onValueChange={(timezone) => updateQuietHours('timezone', timezone)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {timezones.map((tz) => (
                          <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Setup Instructions */}
      {settings.enabled && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Info className="w-5 h-5" />
              Slack App Setup Instructions
            </CardTitle>
          </CardHeader>
          <CardContent className="text-blue-800">
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Create a new Slack app at <code>api.slack.com/apps</code></li>
              <li>Add the following OAuth scopes: <code>chat:write</code>, <code>channels:read</code>, <code>groups:read</code></li>
              <li>Install the app to your workspace</li>
              <li>Copy the Bot User OAuth Token and Signing Secret</li>
              <li>Invite the bot to the channels you want to use</li>
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
};