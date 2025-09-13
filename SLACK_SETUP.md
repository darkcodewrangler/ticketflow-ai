# Slack Integration Setup Guide

## Overview

TicketFlow AI includes comprehensive Slack integration that allows you to send notifications about ticket updates, system alerts, and other important events directly to your Slack channels.

## Features

✅ **Rich Message Formatting**: Ticket notifications include structured blocks with emojis and context  
✅ **Error Handling**: Comprehensive error handling with detailed logging  
✅ **Async Support**: Non-blocking async implementation  
✅ **Flexible Messaging**: Support for both simple text and rich formatted messages  

## Setup Instructions

### 1. Create a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter your app name (e.g., "TicketFlow AI")
5. Select your workspace

### 2. Configure Bot Permissions

In your Slack app settings:

1. Go to **OAuth & Permissions**
2. Under **Scopes** → **Bot Token Scopes**, add:
   - `chat:write` - Send messages
   - `chat:write.public` - Send messages to public channels
   - `channels:read` - View basic information about public channels

### 3. Install App to Workspace

1. In **OAuth & Permissions**, click **Install to Workspace**
2. Authorize the app
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 4. Configure Environment

Add to your `.env` file:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
```

**Important**: Make sure you're using a Bot Token (`xoxb-`) not an App Token (`xapp-`) or User Token (`xoxp-`).

### 5. Invite Bot to Channels

For each channel you want to send notifications to:
1. Go to the channel
2. Type `/invite @YourBotName`
3. Or mention the bot: `@YourBotName`

## Usage Examples

### Simple Notification
```python
from ticketflow.external_tools_manager import ExternalToolsManager

tools_manager = ExternalToolsManager()

result = await tools_manager.send_slack_notification(
    channel="#general",
    message="System maintenance completed successfully!"
)
```

### Ticket Update Notification
```python
result = await tools_manager.send_slack_notification(
    channel="#support",
    message="Customer provided additional information about the login issue.",
    ticket_id=12345
)
```

## Message Formats

### Simple Messages
- Prefixed with 🤖 TicketFlow AI emoji
- Plain text format

### Ticket Messages
- Rich block format with 🎫 ticket emoji
- Includes ticket ID in header
- Context footer with ticket ID and system name
- Structured layout for better readability

## Error Handling

The integration includes comprehensive error handling:

- **Configuration errors**: Returns `{"status": "disabled"}` if not configured
- **API errors**: Returns detailed Slack API error information
- **Network errors**: Returns generic error with exception details
- **Logging**: All errors are logged with appropriate log levels

## Testing

Run the test script to verify your integration:

```bash
python test_slack_integration.py
```

This will:
- Check if Slack is properly configured
- Test simple notifications
- Test rich ticket notifications
- Display detailed results and error information

## Troubleshooting

### Common Issues

**"not_allowed_token_type" Error**
- You're using an App Token (`xapp-`) instead of a Bot Token (`xoxb-`)
- Solution: Use the Bot User OAuth Token from OAuth & Permissions

**"channel_not_found" Error**
- The bot hasn't been invited to the channel
- Solution: Invite the bot to the channel using `/invite @BotName`

**"missing_scope" Error**
- Bot doesn't have required permissions
- Solution: Add `chat:write` and `chat:write.public` scopes

**"invalid_auth" Error**
- Token is invalid or expired
- Solution: Regenerate the bot token in Slack app settings

### Debug Mode

Enable debug logging in your `.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Security Notes

- Never commit your Slack bot token to version control
- Use environment variables for all sensitive configuration
- Regularly rotate your bot tokens
- Monitor bot usage in Slack app analytics

## Integration with TicketFlow AI

The Slack integration is automatically used by the AI agent for:
- Ticket status updates
- Priority escalations
- System notifications
- Customer communication summaries

Configure notification preferences in your agent settings to control when Slack notifications are sent.