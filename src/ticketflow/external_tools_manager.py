from typing import Dict, Any, Optional
import asyncio
import resend
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .config import config
from .database.connection import db_manager
from .database import SettingsManager
import logging
logger = logging.getLogger(__name__)


class ExternalToolsManager:
    """
    Manages external tool integrations for the AI agent
    Handles notifications, integrations, and external actions
    Uses database settings for configuration with fallback to environment variables
    """
    
    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        self.settings_manager = settings_manager
        self.slack_client = None
        self.slack_enabled = False
        self.email_enabled = False
        
        # Initialize settings if not provided
        if not self.settings_manager:
            if db_manager._connected:
                self.settings_manager = SettingsManager(db_manager, config.ENCRYPTION_KEY)
            else:
                logger.warning("Database not connected for settings management")
    
    async def _initialize_integrations(self):
        """
        Initialize integrations based on database settings
        """
        try:
            # Check Slack settings
            slack_enabled = await self.settings_manager.get_setting_value('slack_notifications_enabled', False)
            slack_token = await self.settings_manager.get_setting_value('slack_bot_token', '')
            
            if slack_enabled and slack_token:
                self.slack_client = AsyncWebClient(token=slack_token)
                self.slack_enabled = True
                logger.info("Slack integration initialized from database settings")
            else:
                # Fallback to environment variables
                if hasattr(config, 'SLACK_BOT_TOKEN') and config.SLACK_BOT_TOKEN:
                    self.slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)
                    self.slack_enabled = True
                    logger.info("Slack integration initialized from environment variables")
                else:
                    logger.warning("Slack integration disabled - no token found")
            
            # Check Email settings
            email_enabled = await self.settings_manager.get_setting_value('email_notifications_enabled', False)
            
            if email_enabled:
                # For now, still use environment variable for Resend API key
                # TODO: Add resend_api_key to settings when needed
                if hasattr(config, 'RESEND_API_KEY') and config.RESEND_API_KEY:
                    resend.api_key = config.RESEND_API_KEY
                    self.email_enabled = True
                    logger.info("Email integration initialized")
                else:
                    logger.warning("Email integration disabled - no API key found")
            else:
                logger.info("Email notifications disabled in settings")
                
        except Exception as e:
            logger.error(f"Failed to initialize integrations from settings: {e}")
            # Fallback to environment variables
            if hasattr(config, 'SLACK_BOT_TOKEN') and config.SLACK_BOT_TOKEN:
                self.slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)
                self.slack_enabled = True
            if hasattr(config, 'RESEND_API_KEY') and config.RESEND_API_KEY:
                resend.api_key = config.RESEND_API_KEY
                self.email_enabled = True
    
    async def send_slack_notification(self, channel: str = None, message: str = "", ticket_id: int = None, notification_type: str = "general") -> Dict[str, Any]:
        """Send Slack notification with rich formatting"""
        # Initialize integrations if not done yet
        if not hasattr(self, '_initialized'):
            await self._initialize_integrations()
            self._initialized = True
            
        if not self.slack_enabled or not self.slack_client:
            return {"status": "disabled", "message": "Slack integration not configured"}
        
        try:
            # Determine channel from settings if not provided
            if not channel:
                if notification_type == "new_ticket":
                    channel = await self.settings_manager.get_setting_value('slack_new_ticket_channel', '#general')
                elif notification_type == "escalated_ticket":
                    channel = await self.settings_manager.get_setting_value('slack_escalated_ticket_channel', '#general')
                elif notification_type == "resolved_ticket":
                    channel = await self.settings_manager.get_setting_value('slack_resolved_ticket_channel', '#general')
                else:
                    channel = await self.settings_manager.get_setting_value('slack_default_channel', '#general')
            
            # Format the message with rich blocks if ticket_id is provided
            if ticket_id:
                if notification_type == "new_ticket":
                    emoji = "🆕"
                    title = f"New Ticket #{ticket_id}"
                elif notification_type == "escalated_ticket":
                    emoji = "🚨"
                    title = f"Escalated Ticket #{ticket_id}"
                elif notification_type == "resolved_ticket":
                    emoji = "✅"
                    title = f"Resolved Ticket #{ticket_id}"
                else:
                    emoji = "🎫"
                    title = f"Ticket #{ticket_id} Update"
                    
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *{title}*\n{message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Ticket ID: {ticket_id} | TicketFlow AI"
                            }
                        ]
                    }
                ]
                
                # Send message with blocks
                response = await self.slack_client.chat_postMessage(
                    channel=channel,
                    blocks=blocks,
                    text=f"{title}: {message}"  # Fallback text
                )
            else:
                # Send simple text message
                response = await self.slack_client.chat_postMessage(
                    channel=channel,
                    text=f"🤖 TicketFlow AI: {message}"
                )
            
            logger.info(f"Slack notification sent to {channel} for ticket {ticket_id} (type: {notification_type}): {message[:50]}...")
            
            return {
                "status": "sent",
                "channel": channel,
                "message_id": response["ts"],
                "ok": response["ok"]
            }
            
        except SlackApiError as e:
            error_msg = f"Slack API error: {e.response['error']}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "error_code": e.response['error']
            }
        except Exception as e:
            error_msg = f"Slack notification failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg
            }
    
    async def send_email_notification(self, to_email: str = None, subject: str = "", content: str = "", ticket_id: int = None, notification_type: str = "general") -> Dict[str, Any]:
        """
        Send an email notification
        
        Args:
            to_email: Recipient email address (optional, will use settings if not provided)
            subject: Email subject
            content: Email content (HTML supported)
            ticket_id: Optional ticket ID for context
            notification_type: Type of notification (new_ticket, escalated_ticket, resolved_ticket, general)
            
        Returns:
            Dict with success status and response data
        """
        # Initialize integrations if not done yet
        if not hasattr(self, '_initialized'):
            await self._initialize_integrations()
            self._initialized = True
            
        if not self.email_enabled:
            logger.warning("Email integration not enabled or configured")
            return {"success": False, "error": "Email not configured"}
        
        try:
            # Determine recipient from settings if not provided
            if not to_email:
                if notification_type == "new_ticket":
                    to_email = await self.settings_manager.get_setting_value('email_new_ticket_recipient', '')
                elif notification_type == "escalated_ticket":
                    to_email = await self.settings_manager.get_setting_value('email_escalated_ticket_recipient', '')
                elif notification_type == "resolved_ticket":
                    to_email = await self.settings_manager.get_setting_value('email_resolved_ticket_recipient', '')
                else:
                    to_email = await self.settings_manager.get_setting_value('email_default_recipient', '')
                
                if not to_email:
                    logger.warning(f"No email recipient configured for notification type: {notification_type}")
                    return {"success": False, "error": "No recipient configured"}
            
            # Get sender email from settings
            from_email = await self.settings_manager.get_setting_value('email_sender_address', 'noreply@ticketflow.ai')
            
            # Add ticket context to subject if provided
            if ticket_id:
                if notification_type == "new_ticket":
                    formatted_subject = f"[New Ticket #{ticket_id}] {subject}"
                elif notification_type == "escalated_ticket":
                    formatted_subject = f"[Escalated Ticket #{ticket_id}] {subject}"
                elif notification_type == "resolved_ticket":
                    formatted_subject = f"[Resolved Ticket #{ticket_id}] {subject}"
                else:
                    formatted_subject = f"[Ticket #{ticket_id}] {subject}"
            else:
                formatted_subject = subject
            
            # Send email using Resend
            response = resend.Emails.send({
                "from": from_email,
                "to": [to_email],
                "subject": formatted_subject,
                "html": content
            })
            
            logger.info(f"Email notification sent to {to_email} for ticket {ticket_id} (type: {notification_type})")
            return {
                "success": True,
                "email_id": response.get("id"),
                "recipient": to_email
            }
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {
                "success": False,
                "error": f"Email error: {str(e)}"
            }
    
    async def create_calendar_event(self, title: str, description: str, duration_hours: int = 1) -> Dict[str, Any]:
        """Create calendar event for follow-up"""
        try:
            # In a real implementation, this would integrate with Google Calendar, Outlook, etc.
            event_data = {
                "title": title,
                "description": description,
                "duration_hours": duration_hours,
                "created_at": asyncio.get_event_loop().time()
            }
            
            await asyncio.sleep(0.1)  # Simulate API call
            
            logger.info(f"Calendar event created: {title}")
            
            return {
                "status": "created",
                "event_id": f"cal_{int(asyncio.get_event_loop().time())}",
                "title": title
            }
            
        except Exception as e:
            logger.error(f"Calendar event creation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def update_external_ticket_system(self, external_id: str, status: str, resolution: str = None) -> Dict[str, Any]:
        """Update external ticketing system"""
        try:
            # In a real implementation, this would integrate with Zendesk, ServiceNow, etc.
            update_data = {
                "external_id": external_id,
                "status": status,
                "resolution": resolution,
                "updated_at": asyncio.get_event_loop().time()
            }
            
            await asyncio.sleep(0.15)  # Simulate API call
            
            logger.info(f"External ticket {external_id} updated to {status}")
            
            return {
                "status": "updated",
                "external_id": external_id,
                "new_status": status
            }
            
        except Exception as e:
            logger.error(f"External ticket update failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def log_to_monitoring(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log events to monitoring system"""
        try:
            # In a real implementation, this would send to DataDog, New Relic, etc.
            log_entry = {
                "event_type": event_type,
                "data": data,
                "timestamp": asyncio.get_event_loop().time(),
                "source": "ticketflow_agent"
            }
            
            await asyncio.sleep(0.05)  # Simulate logging
            
            logger.info(f"Monitoring event logged: {event_type}")
            
            return {
                "status": "logged",
                "event_type": event_type,
                "log_id": f"log_{int(asyncio.get_event_loop().time())}"
            }
            
        except Exception as e:
            logger.error(f"Monitoring log failed: {e}")
            return {"status": "failed", "error": str(e)}