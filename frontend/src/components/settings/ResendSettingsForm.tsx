import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Mail, 
  TestTube, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Clock,
  Eye,
  MousePointer,
  Shield,
  Send
} from "lucide-react";
import { ResendSettings, EmailTemplate } from "@/types";
import { api } from "@/services/api";
import { showSuccess, showError, showLoading } from "@/utils/toast";

interface ResendSettingsFormProps {
  settings: ResendSettings;
  onSettingsChange: (settings: ResendSettings) => void;
}

const templateVariables = {
  '{{ticket_id}}': 'Ticket ID number',
  '{{ticket_title}}': 'Ticket title',
  '{{ticket_description}}': 'Ticket description',
  '{{ticket_status}}': 'Current ticket status',
  '{{ticket_priority}}': 'Ticket priority level',
  '{{ticket_category}}': 'Ticket category',
  '{{ticket_url}}': 'Direct link to ticket',
  '{{customer_email}}': 'Customer email address',
  '{{customer_name}}': 'Customer name (if available)',
  '{{resolution}}': 'Ticket resolution details',
  '{{resolution_time}}': 'Time taken to resolve',
  '{{agent_confidence}}': 'AI agent confidence score',
  '{{company_name}}': 'Your company name',
  '{{support_email}}': 'Support team email',
  '{{timestamp}}': 'Current timestamp',
  '{{date}}': 'Current date'
};

const emailTemplateTypes = {
  ticketCreated: {
    label: "Ticket Created",
    description: "Sent when a new ticket is created",
    defaultSubject: "Ticket #{{ticket_id}} Created - {{ticket_title}}",
    icon: Mail
  },
  ticketResolved: {
    label: "Ticket Resolved",
    description: "Sent when a ticket is resolved",
    defaultSubject: "Ticket #{{ticket_id}} Resolved - {{ticket_title}}",
    icon: CheckCircle
  },
  ticketEscalated: {
    label: "Ticket Escalated",
    description: "Sent when a ticket is escalated",
    defaultSubject: "Urgent: Ticket #{{ticket_id}} Escalated",
    icon: AlertTriangle
  },
  processingUpdate: {
    label: "Processing Update",
    description: "Sent during AI processing",
    defaultSubject: "Update on Ticket #{{ticket_id}}",
    icon: Info
  }
};

const timezones = [
  "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", 
  "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
];

export const ResendSettingsForm: React.FC<ResendSettingsFormProps> = ({
  settings,
  onSettingsChange
}) => {
  const [testEmailStatus, setTestEmailStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  const [testEmailAddress, setTestEmailAddress] = useState('');
  const [showVariables, setShowVariables] = useState<string | null>(null);

  const updateSettings = (updates: Partial<ResendSettings>) => {
    onSettingsChange({ ...settings, ...updates });
  };

  const updateTemplate = (templateKey: keyof ResendSettings['templates'], template: Partial<EmailTemplate>) => {
    const updatedTemplates = {
      ...settings.templates,
      [templateKey]: { ...settings.templates[templateKey], ...template }
    };
    updateSettings({ templates: updatedTemplates });
  };

  const updateAdvancedSetting = (key: string, value: any) => {
    const updatedAdvanced = {
      ...settings.advanced,
      [key]: value
    };
    updateSettings({ advanced: updatedAdvanced });
  };

  const updateQuietHours = (key: string, value: any) => {
    const updatedQuietHours = {
      ...settings.advanced.quietHours,
      [key]: value
    };
    updateAdvancedSetting('quietHours', updatedQuietHours);
  };

  const sendTestEmail = async () => {
    if (!testEmailAddress) {
      showError("Please enter a test email address");
      return;
    }

    try {
      setTestEmailStatus('sending');
      const response = await api.testResendConfiguration();
      
      if (response.success) {
        setTestEmailStatus('success');
        showSuccess('Test email sent successfully!');
      } else {
        setTestEmailStatus('error');
        showError(response.data.message || 'Failed to send test email');
      }
    } catch (error) {
      setTestEmailStatus('error');
      showError('Failed to send test email');
    }
  };

  const insertVariable = (templateKey: string, variable: string) => {
    const template = settings.templates[templateKey as keyof ResendSettings['templates']];
    const textarea = document.getElementById(`template-${templateKey}`) as HTMLTextAreaElement;
    
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = template.customTemplate || '';
      const newText = text.substring(0, start) + variable + text.substring(end);
      
      updateTemplate(templateKey as keyof ResendSettings['templates'], { customTemplate: newText });
      
      // Restore cursor position
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + variable.length, start + variable.length);
      }, 0);
    }
  };

  const TemplateEditor: React.FC<{
    templateKey: keyof ResendSettings['templates'];
    templateConfig: typeof emailTemplateTypes[keyof typeof emailTemplateTypes];
  }> = ({ templateKey, templateConfig }) => {
    const template = settings.templates[templateKey];
    const Icon = templateConfig.icon;

    return (
      <Card className="mb-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-5 h-5 text-blue-600" />
              <div>
                <CardTitle className="text-lg">{templateConfig.label}</CardTitle>
                <p className="text-sm text-gray-600">{templateConfig.description}</p>
              </div>
            </div>
            <Switch
              checked={template.enabled}
              onCheckedChange={(enabled) => updateTemplate(templateKey, { enabled })}
            />
          </div>
        </CardHeader>

        {template.enabled && (
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor={`subject-${templateKey}`}>Email Subject</Label>
              <Input
                id={`subject-${templateKey}`}
                value={template.subject}
                onChange={(e) => updateTemplate(templateKey, { subject: e.target.value })}
                placeholder={templateConfig.defaultSubject}
              />
            </div>

            <div>
              <Label>Template Type</Label>
              <Select
                value={template.template}
                onValueChange={(value: 'default' | 'custom') => updateTemplate(templateKey, { template: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default Template</SelectItem>
                  <SelectItem value="custom">Custom Template</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {template.template === 'custom' && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor={`template-${templateKey}`}>Custom Template</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowVariables(showVariables === templateKey ? null : templateKey)}
                  >
                    {showVariables === templateKey ? 'Hide' : 'Show'} Variables
                  </Button>
                </div>

                {showVariables === templateKey && (
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium mb-2">Available Variables:</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(templateVariables).map(([variable, description]) => (
                        <button
                          key={variable}
                          onClick={() => insertVariable(templateKey, variable)}
                          className="text-left p-2 hover:bg-gray-100 rounded"
                          title={description}
                        >
                          <code className="text-blue-600">{variable}</code>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <Textarea
                  id={`template-${templateKey}`}
                  value={template.customTemplate || ''}
                  onChange={(e) => updateTemplate(templateKey, { customTemplate: e.target.value })}
                  className="font-mono text-sm"
                  rows={8}
                  placeholder="Enter your custom email template here..."
                />
              </div>
            )}

            {/* Special settings for specific templates */}
            {templateKey === 'ticketEscalated' && (
              <div>
                <Label htmlFor={`recipients-${templateKey}`}>Additional Recipients</Label>
                <Input
                  id={`recipients-${templateKey}`}
                  value={(template as any).recipients?.join(', ') || ''}
                  onChange={(e) => updateTemplate(templateKey, { 
                    recipients: e.target.value.split(',').map(email => email.trim()).filter(Boolean) 
                  } as any)}
                  placeholder="manager@company.com, escalation@company.com"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Comma-separated list of additional email addresses for escalations
                </p>
              </div>
            )}

            {templateKey === 'processingUpdate' && (
              <div className="flex items-center justify-between">
                <div>
                  <Label>Send Only on Completion</Label>
                  <p className="text-sm text-gray-600">Only send when processing is complete</p>
                </div>
                <Switch
                  checked={(template as any).sendOnlyOnCompletion || false}
                  onCheckedChange={(checked) => updateTemplate(templateKey, { sendOnlyOnCompletion: checked } as any)}
                />
              </div>
            )}
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Basic Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-blue-600" />
            Resend Email Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable Email Notifications</Label>
              <p className="text-sm text-gray-600">Send automated email notifications</p>
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
                  <Label htmlFor="api-key">Resend API Key *</Label>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="re_xxxxxxxxxx"
                    value={settings.apiKey}
                    onChange={(e) => updateSettings({ apiKey: e.target.value })}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your Resend API key from the dashboard
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="from-email">From Email *</Label>
                    <Input
                      id="from-email"
                      type="email"
                      placeholder="support@yourcompany.com"
                      value={settings.fromEmail}
                      onChange={(e) => updateSettings({ fromEmail: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Must be a verified domain
                    </p>
                  </div>
                  <div>
                    <Label htmlFor="from-name">From Name</Label>
                    <Input
                      id="from-name"
                      placeholder="TicketFlow AI Support"
                      value={settings.fromName}
                      onChange={(e) => updateSettings({ fromName: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="reply-to">Reply-To Email</Label>
                  <Input
                    id="reply-to"
                    type="email"
                    placeholder="noreply@yourcompany.com"
                    value={settings.replyToEmail}
                    onChange={(e) => updateSettings({ replyToEmail: e.target.value })}
                  />
                </div>
              </div>

              {/* Test Email */}
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <Label htmlFor="test-email">Test Email Address</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="test-email"
                    type="email"
                    placeholder="test@example.com"
                    value={testEmailAddress}
                    onChange={(e) => setTestEmailAddress(e.target.value)}
                  />
                  <Button
                    onClick={sendTestEmail}
                    disabled={testEmailStatus === 'sending' || !testEmailAddress}
                    variant="outline"
                  >
                    <TestTube className="w-4 h-4 mr-2" />
                    {testEmailStatus === 'sending' ? 'Sending...' : 'Send Test'}
                  </Button>
                </div>
                {testEmailStatus === 'success' && (
                  <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    Test email sent successfully!
                  </p>
                )}
                {testEmailStatus === 'error' && (
                  <p className="text-sm text-red-600 mt-2 flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4" />
                    Failed to send test email
                  </p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Email Templates */}
      {settings.enabled && (
        <Card>
          <CardHeader>
            <CardTitle>Email Templates</CardTitle>
            <p className="text-sm text-gray-600">
              Configure automated email notifications for different events
            </p>
          </CardHeader>
          <CardContent>
            {Object.entries(emailTemplateTypes).map(([templateKey, templateConfig]) => (
              <TemplateEditor
                key={templateKey}
                templateKey={templateKey as keyof ResendSettings['templates']}
                templateConfig={templateConfig}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Advanced Settings */}
      {settings.enabled && (
        <Card>
          <CardHeader>
            <CardTitle>Advanced Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="limits" className="space-y-4">
              <TabsList>
                <TabsTrigger value="limits">Rate Limits</TabsTrigger>
                <TabsTrigger value="tracking">Tracking</TabsTrigger>
                <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
                <TabsTrigger value="suppression">Suppression</TabsTrigger>
              </TabsList>

              <TabsContent value="limits" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="max-hourly">Max Emails Per Hour</Label>
                    <Input
                      id="max-hourly"
                      type="number"
                      min="1"
                      max="1000"
                      value={settings.advanced.maxEmailsPerHour}
                      onChange={(e) => updateAdvancedSetting('maxEmailsPerHour', parseInt(e.target.value))}
                    />
                    <p className="text-xs text-gray-500 mt-1">Rate limiting protection</p>
                  </div>
                  <div>
                    <Label htmlFor="max-daily">Max Emails Per Day</Label>
                    <Input
                      id="max-daily"
                      type="number"
                      min="1"
                      max="10000"
                      value={settings.advanced.maxEmailsPerDay}
                      onChange={(e) => updateAdvancedSetting('maxEmailsPerDay', parseInt(e.target.value))}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="retry-attempts">Retry Attempts</Label>
                    <Input
                      id="retry-attempts"
                      type="number"
                      min="0"
                      max="5"
                      value={settings.advanced.retryAttempts}
                      onChange={(e) => updateAdvancedSetting('retryAttempts', parseInt(e.target.value))}
                    />
                    <p className="text-xs text-gray-500 mt-1">Failed delivery retries</p>
                  </div>
                  <div>
                    <Label htmlFor="retry-delay">Retry Delay (seconds)</Label>
                    <Input
                      id="retry-delay"
                      type="number"
                      min="1"
                      max="300"
                      value={settings.advanced.retryDelay}
                      onChange={(e) => updateAdvancedSetting('retryDelay', parseInt(e.target.value))}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="tracking" className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-gray-500" />
                      <div>
                        <Label>Track Email Opens</Label>
                        <p className="text-sm text-gray-600">Monitor email open rates</p>
                      </div>
                    </div>
                    <Switch
                      checked={settings.advanced.trackOpens}
                      onCheckedChange={(checked) => updateAdvancedSetting('trackOpens', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MousePointer className="w-4 h-4 text-gray-500" />
                      <div>
                        <Label>Track Link Clicks</Label>
                        <p className="text-sm text-gray-600">Monitor link click rates</p>
                      </div>
                    </div>
                    <Switch
                      checked={settings.advanced.trackClicks}
                      onCheckedChange={(checked) => updateAdvancedSetting('trackClicks', checked)}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="scheduling" className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <Label>Quiet Hours</Label>
                  </div>
                  <Switch
                    checked={settings.advanced.quietHours.enabled}
                    onCheckedChange={(enabled) => updateQuietHours('enabled', enabled)}
                  />
                </div>

                {settings.advanced.quietHours.enabled && (
                  <div className="grid grid-cols-3 gap-4 ml-6">
                    <div>
                      <Label htmlFor="quiet-start">Start Time</Label>
                      <Input
                        id="quiet-start"
                        type="time"
                        value={settings.advanced.quietHours.startTime}
                        onChange={(e) => updateQuietHours('startTime', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="quiet-end">End Time</Label>
                      <Input
                        id="quiet-end"
                        type="time"
                        value={settings.advanced.quietHours.endTime}
                        onChange={(e) => updateQuietHours('endTime', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="quiet-timezone">Timezone</Label>
                      <Select
                        value={settings.advanced.quietHours.timezone}
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
              </TabsContent>

              <TabsContent value="suppression" className="space-y-4">
                <div>
                  <Label htmlFor="suppression-list">Suppression List</Label>
                  <Textarea
                    id="suppression-list"
                    placeholder="email1@example.com&#10;email2@example.com"
                    value={settings.advanced.suppressionList.join('\n')}
                    onChange={(e) => updateAdvancedSetting('suppressionList', 
                      e.target.value.split('\n').map(email => email.trim()).filter(Boolean)
                    )}
                    rows={4}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    One email address per line. These addresses will never receive emails.
                  </p>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Setup Instructions */}
      {settings.enabled && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Info className="w-5 h-5" />
              Resend Setup Instructions
            </CardTitle>
          </CardHeader>
          <CardContent className="text-blue-800">
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Create a Resend account at <code>resend.com</code></li>
              <li>Verify your sending domain in the Resend dashboard</li>
              <li>Generate an API key with send permissions</li>
              <li>Configure your DNS records for domain verification</li>
              <li>Test your configuration with the test email feature above</li>
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
};