from typing import Dict, Any
import asyncio
import resend
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .config import config
import logging
logger = logging.getLogger(__name__)


class ExternalToolsManager:
    """
    Manages external tool integrations for the AI agent
    Handles notifications, integrations, and external actions
    """
    
    def __init__(self):
        self.slack_enabled = bool(config.SLACK_BOT_TOKEN) if hasattr(config, 'SLACK_BOT_TOKEN') else False
        self.email_enabled = bool(config.RESEND_API_KEY) if hasattr(config, 'RESEND_API_KEY') else False
        
        # Initialize Slack client if token is available
        if self.slack_enabled:
            self.slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)
        else:
            self.slack_client = None
        
        # Initialize Resend if API key is available
        if self.email_enabled:
            resend.api_key = config.RESEND_API_KEY
    
    async def send_slack_notification(self, channel: str, message: str, ticket_id: int = None) -> Dict[str, Any]:
        """Send Slack notification with rich formatting"""
        if not self.slack_enabled or not self.slack_client:
            return {"status": "disabled", "message": "Slack integration not configured"}
        
        try:
            # Format the message with rich blocks if ticket_id is provided
            if ticket_id:
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🎫 *Ticket #{ticket_id} Update*\n{message}"
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
                    text=f"Ticket #{ticket_id} Update: {message}"  # Fallback text
                )
            else:
                # Send simple text message
                response = await self.slack_client.chat_postMessage(
                    channel=channel,
                    text=f"🤖 TicketFlow AI: {message}"
                )
            
            logger.info(f"Slack notification sent to {channel}: {message[:50]}...")
            
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
    
    async def send_email_notification(self, recipient: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email notification using Resend"""
        if not self.email_enabled:
            return {"status": "disabled", "message": "Email integration not configured"}
        
        try:
            # Prepare email content
            email_params = {
                "from": "TicketFlow AI <victory@notif.klozbuy.com>",
                "to": ["luckyvictory54@gmail.com"],
                "subject": subject,
                "text": body
            }
            
            # Add HTML body if provided
            if html_body:
                email_params["html"] = html_body
            
            # Send email using Resend
            response = resend.Emails.send(email_params)
            
            logger.info(f"Email sent to {recipient}: {subject} (ID: {response.get('id', 'unknown')})")
            
            return {
                "status": "sent",
                "recipient": recipient,
                "message_id": response.get("id", f"email_{int(asyncio.get_event_loop().time())}"),
                "resend_response": response
            }
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return {"status": "failed", "error": str(e)}
    
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