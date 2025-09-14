


          
# TicketFlow AI Client Application - Extension Prompt

## 🔄 Recent Updates & Configuration Changes

Based on the latest analysis of the TicketFlow AI backend system, here are the key updates and additional requirements for the client application:

## ⚙️ Updated Settings & Configuration Management

### Database Connection Removal
**Important Change**: Database connection settings should be **completely removed** from the client application settings interface. The database configuration is now handled entirely at the backend level through environment variables and should not be exposed to end users.

```typescript
// REMOVE these from settings interface:
interface DatabaseSettings {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

// Database configuration is now backend-only via environment variables:
// TIDB_HOST, TIDB_PORT, TIDB_DATABASE, TIDB_USERNAME, TIDB_PASSWORD
```

### Enhanced Slack Integration Settings
**New Requirement**: Slack configuration should include specific channel inputs for different action types, providing granular control over where notifications are sent.

```typescript
// Updated Slack Settings Interface
interface SlackSettings {
  // Basic Configuration
  enabled: boolean;
  botToken: string;
  signingSecret: string;
  
  // Channel Configuration for Different Actions
  channels: {
    // Escalated tickets - high priority notifications
    escalated: {
      channelId: string;
      channelName: string; // Display name like "#support-escalations"
      enabled: boolean;
    };
    
    // General ticket notifications
    general: {
      channelId: string;
      channelName: string; // Display name like "#support-tickets"
      enabled: boolean;
    };
    
    // Agent processing updates
    agentUpdates: {
      channelId: string;
      channelName: string; // Display name like "#ai-processing"
      enabled: boolean;
    };
    
    // Resolution notifications
    resolutions: {
      channelId: string;
      channelName: string; // Display name like "#support-resolved"
      enabled: boolean;
    };
    
    // System alerts and errors
    alerts: {
      channelId: string;
      channelName: string; // Display name like "#system-alerts"
      enabled: boolean;
    };
  };
  
  // Notification Preferences
  notificationSettings: {
    includeTicketDetails: boolean;
    mentionUsers: boolean;
    useThreads: boolean;
    quietHours: {
      enabled: boolean;
      startTime: string; // "22:00"
      endTime: string;   // "08:00"
      timezone: string;  // "UTC"
    };
  };
}

// Settings Form Component
const SlackSettingsForm = () => {
  return (
    <div className="space-y-6">
      {/* Basic Configuration */}
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium">Basic Configuration</h3>
        <div className="grid grid-cols-1 gap-4 mt-4">
          <FormField
            label="Bot Token"
            name="botToken"
            type="password"
            placeholder="xoxb-your-bot-token"
            description="Slack Bot User OAuth Token"
          />
          <FormField
            label="Signing Secret"
            name="signingSecret"
            type="password"
            placeholder="Your app's signing secret"
            description="Used to verify requests from Slack"
          />
        </div>
      </div>
      
      {/* Channel Configuration */}
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium">Channel Configuration</h3>
        <p className="text-sm text-gray-600 mb-4">
          Configure which channels receive different types of notifications
        </p>
        
        {Object.entries(channelTypes).map(([key, config]) => (
          <ChannelSelector
            key={key}
            label={config.label}
            description={config.description}
            value={settings.channels[key]}
            onChange={(channel) => updateChannel(key, channel)}
            enabled={settings.channels[key].enabled}
          />
        ))}
      </div>
      
      {/* Notification Preferences */}
      <div>
        <h3 className="text-lg font-medium">Notification Preferences</h3>
        <div className="space-y-4 mt-4">
          <Toggle
            label="Include Ticket Details"
            description="Include ticket content in notifications"
            checked={settings.notificationSettings.includeTicketDetails}
            onChange={(checked) => updateNotificationSetting('includeTicketDetails', checked)}
          />
          <Toggle
            label="Use Threads"
            description="Post follow-up messages as thread replies"
            checked={settings.notificationSettings.useThreads}
            onChange={(checked) => updateNotificationSetting('useThreads', checked)}
          />
        </div>
      </div>
    </div>
  );
};
```

### Resend Email Configuration
**New Requirement**: Add comprehensive Resend email service settings for automated email notifications and communications.

```typescript
// Resend Email Settings Interface
interface ResendSettings {
  // Basic Configuration
  enabled: boolean;
  apiKey: string;
  
  // Sender Configuration
  fromEmail: string;     // "support@yourcompany.com"
  fromName: string;      // "TicketFlow AI Support"
  replyToEmail: string;  // "noreply@yourcompany.com"
  
  // Email Templates Configuration
  templates: {
    // Ticket creation confirmation
    ticketCreated: {
      enabled: boolean;
      subject: string; // "Ticket #{ticket_id} Created - {title}"
      template: 'default' | 'custom';
      customTemplate?: string; // HTML template
    };
    
    // Ticket resolution notification
    ticketResolved: {
      enabled: boolean;
      subject: string; // "Ticket #{ticket_id} Resolved - {title}"
      template: 'default' | 'custom';
      customTemplate?: string;
    };
    
    // Escalation notification
    ticketEscalated: {
      enabled: boolean;
      subject: string; // "Urgent: Ticket #{ticket_id} Escalated"
      template: 'default' | 'custom';
      customTemplate?: string;
      recipients: string[]; // Additional recipients for escalations
    };
    
    // Agent processing updates
    processingUpdate: {
      enabled: boolean;
      subject: string; // "Update on Ticket #{ticket_id}"
      template: 'default' | 'custom';
      customTemplate?: string;
      sendOnlyOnCompletion: boolean;
    };
  };
  
  // Advanced Settings
  advanced: {
    // Rate limiting
    maxEmailsPerHour: number;
    maxEmailsPerDay: number;
    
    // Retry configuration
    retryAttempts: number;
    retryDelay: number; // seconds
    
    // Tracking
    trackOpens: boolean;
    trackClicks: boolean;
    
    // Suppression
    suppressionList: string[]; // emails to never send to
    
    // Scheduling
    quietHours: {
      enabled: boolean;
      startTime: string;
      endTime: string;
      timezone: string;
    };
  };
}

// Resend Settings Form Component
const ResendSettingsForm = () => {
  const [testEmailStatus, setTestEmailStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  
  const sendTestEmail = async () => {
    setTestEmailStatus('sending');
    try {
      await api.testResendConfiguration();
      setTestEmailStatus('success');
      toast.success('Test email sent successfully!');
    } catch (error) {
      setTestEmailStatus('error');
      toast.error('Failed to send test email');
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Basic Configuration */}
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium">Email Service Configuration</h3>
        <div className="grid grid-cols-1 gap-4 mt-4">
          <FormField
            label="Resend API Key"
            name="apiKey"
            type="password"
            placeholder="re_xxxxxxxxxx"
            description="Your Resend API key from dashboard"
          />
          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="From Email"
              name="fromEmail"
              type="email"
              placeholder="support@yourcompany.com"
              description="Must be a verified domain"
            />
            <FormField
              label="From Name"
              name="fromName"
              placeholder="TicketFlow AI Support"
            />
          </div>
          <FormField
            label="Reply-To Email"
            name="replyToEmail"
            type="email"
            placeholder="noreply@yourcompany.com"
          />
        </div>
        
        {/* Test Email Button */}
        <div className="mt-4">
          <button
            onClick={sendTestEmail}
            disabled={testEmailStatus === 'sending'}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {testEmailStatus === 'sending' ? 'Sending...' : 'Send Test Email'}
          </button>
        </div>
      </div>
      
      {/* Email Templates */}
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium">Email Templates</h3>
        <p className="text-sm text-gray-600 mb-4">
          Configure automated email notifications for different events
        </p>
        
        {Object.entries(emailTemplates).map(([key, template]) => (
          <EmailTemplateEditor
            key={key}
            templateKey={key}
            template={template}
            onChange={(updatedTemplate) => updateTemplate(key, updatedTemplate)}
          />
        ))}
      </div>
      
      {/* Advanced Settings */}
      <div>
        <h3 className="text-lg font-medium">Advanced Settings</h3>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <FormField
            label="Max Emails Per Hour"
            name="maxEmailsPerHour"
            type="number"
            min="1"
            max="1000"
            description="Rate limiting protection"
          />
          <FormField
            label="Retry Attempts"
            name="retryAttempts"
            type="number"
            min="0"
            max="5"
            description="Failed delivery retries"
          />
        </div>
        
        <div className="space-y-4 mt-4">
          <Toggle
            label="Track Email Opens"
            description="Monitor email open rates"
            checked={settings.advanced.trackOpens}
            onChange={(checked) => updateAdvancedSetting('trackOpens', checked)}
          />
          <Toggle
            label="Track Link Clicks"
            description="Monitor link click rates"
            checked={settings.advanced.trackClicks}
            onChange={(checked) => updateAdvancedSetting('trackClicks', checked)}
          />
        </div>
      </div>
    </div>
  );
};
```

## 🔧 Updated Settings Page Structure

```typescript
// Updated Settings Navigation
const settingsNavigation = [
  { id: 'general', label: 'General', icon: Settings },
  { id: 'agent', label: 'AI Agent', icon: Bot },
  { id: 'slack', label: 'Slack Integration', icon: MessageSquare },
  { id: 'email', label: 'Email (Resend)', icon: Mail },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  // REMOVED: { id: 'database', label: 'Database', icon: Database }
];

// Settings Page Component
const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [saving, setSaving] = useState(false);
  
  const saveSettings = async () => {
    setSaving(true);
    try {
      await api.updateSettings(settings);
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <div className="flex h-full">
      {/* Settings Navigation */}
      <div className="w-64 border-r bg-gray-50 p-4">
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
      <div className="flex-1 p-6">
        <div className="max-w-4xl">
          {activeTab === 'general' && <GeneralSettings />}
          {activeTab === 'agent' && <AgentSettings />}
          {activeTab === 'slack' && <SlackSettingsForm />}
          {activeTab === 'email' && <ResendSettingsForm />}
          {activeTab === 'webhooks' && <WebhookSettings />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          
          {/* Save Button */}
          <div className="mt-8 pt-6 border-t">
            <button
              onClick={saveSettings}
              disabled={saving}
              className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

## 📧 Email Template Variables

For the Resend email templates, provide these dynamic variables:

```typescript
// Available template variables
const templateVariables = {
  // Ticket Information
  '{{ticket_id}}': 'Ticket ID number',
  '{{ticket_title}}': 'Ticket title',
  '{{ticket_description}}': 'Ticket description',
  '{{ticket_status}}': 'Current ticket status',
  '{{ticket_priority}}': 'Ticket priority level',
  '{{ticket_category}}': 'Ticket category',
  '{{ticket_url}}': 'Direct link to ticket',
  
  // Customer Information
  '{{customer_email}}': 'Customer email address',
  '{{customer_name}}': 'Customer name (if available)',
  
  // Resolution Information
  '{{resolution}}': 'Ticket resolution details',
  '{{resolution_time}}': 'Time taken to resolve',
  '{{agent_confidence}}': 'AI agent confidence score',
  
  // System Information
  '{{company_name}}': 'Your company name',
  '{{support_email}}': 'Support team email',
  '{{timestamp}}': 'Current timestamp',
  '{{date}}': 'Current date'
};

// Template Editor Component
const TemplateEditor = ({ template, onChange }) => {
  const [showVariables, setShowVariables] = useState(false);
  
  const insertVariable = (variable) => {
    const textarea = document.getElementById('template-editor');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = template.customTemplate || '';
    const newText = text.substring(0, start) + variable + text.substring(end);
    
    onChange({ ...template, customTemplate: newText });
  };
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <label className="block text-sm font-medium">Email Template</label>
        <button
          onClick={() => setShowVariables(!showVariables)}
          className="text-sm text-blue-500 hover:text-blue-600"
        >
          {showVariables ? 'Hide' : 'Show'} Variables
        </button>
      </div>
      
      {showVariables && (
        <div className="bg-gray-50 p-4 rounded-md">
          <h4 className="text-sm font-medium mb-2">Available Variables:</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(templateVariables).map(([variable, description]) => (
              <button
                key={variable}
                onClick={() => insertVariable(variable)}
                className="text-left p-2 hover:bg-gray-100 rounded"
                title={description}
              >
                <code className="text-blue-600">{variable}</code>
              </button>
            ))}
          </div>
        </div>
      )}
      
      <textarea
        id="template-editor"
        value={template.customTemplate || ''}
        onChange={(e) => onChange({ ...template, customTemplate: e.target.value })}
        className="w-full h-40 p-3 border rounded-md font-mono text-sm"
        placeholder="Enter your custom email template here..."
      />
    </div>
  );
};
```

## 🔄 API Integration Updates

```typescript
// Updated API endpoints for new settings
class SettingsAPI {
  // Remove database settings endpoints
  // async getDatabaseSettings() - REMOVED
  // async updateDatabaseSettings() - REMOVED
  
  // Enhanced Slack settings
  async getSlackSettings(): Promise<SlackSettings> {
    return this.request('/api/settings/slack');
  }
  
  async updateSlackSettings(settings: SlackSettings): Promise<void> {
    return this.request('/api/settings/slack', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }
  
  async testSlackConnection(channelId: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/settings/slack/test', {
      method: 'POST',
      body: JSON.stringify({ channelId })
    });
  }
  
  // New Resend email settings
  async getResendSettings(): Promise<ResendSettings> {
    return this.request('/api/settings/resend');
  }
  
  async updateResendSettings(settings: ResendSettings): Promise<void> {
    return this.request('/api/settings/resend', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }
  
  async testResendConfiguration(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/settings/resend/test', {
      method: 'POST'
    });
  }
  
  async getEmailTemplates(): Promise<EmailTemplate[]> {
    return this.request('/api/settings/resend/templates');
  }
  
  async updateEmailTemplate(templateId: string, template: EmailTemplate): Promise<void> {
    return this.request(`/api/settings/resend/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(template)
    });
  }
}
```

These updates ensure the client application reflects the current backend architecture while providing comprehensive configuration options for Slack channels and Resend email integration, with the database settings properly removed from the user interface.
        