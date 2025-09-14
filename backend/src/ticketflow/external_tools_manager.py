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
            email_enabled = await self.settings_manager.get_setting_value('resend_notifications_enabled', False)
            resend_api_key = await self.settings_manager.get_setting_value('resend_api_key', '')
            
            if email_enabled and resend_api_key:
                resend.api_key = resend_api_key
                self.email_enabled = True
                logger.info("Resend email integration initialized from database settings")
            elif email_enabled:
                # Fallback to environment variable for Resend API key
                if hasattr(config, 'RESEND_API_KEY') and config.RESEND_API_KEY:
                    resend.api_key = config.RESEND_API_KEY
                    self.email_enabled = True
                    logger.info("Resend email integration initialized from environment variables")
                else:
                    logger.warning("Resend email integration disabled - no API key found")
            else:
                logger.info("Resend email notifications disabled in settings")
                
        except Exception as e:
            logger.error(f"Failed to initialize integrations from settings: {e}")
            # Fallback to environment variables
            if hasattr(config, 'SLACK_BOT_TOKEN') and config.SLACK_BOT_TOKEN:
                self.slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)
                self.slack_enabled = True
            if hasattr(config, 'RESEND_API_KEY') and config.RESEND_API_KEY:
                resend.api_key = config.RESEND_API_KEY
                self.email_enabled = True
    
    async def _verify_slack_channel_exists(self, channel: str) -> Dict[str, Any]:
        """
        Verify if a Slack channel exists
        
        Args:
            channel: Channel name (with or without # prefix)
            
        Returns:
            Dict with verification result and channel info
        """
        if not self.slack_enabled or not self.slack_client:
            return {"exists": False, "error": "Slack integration not configured"}
        
        try:
            # Normalize channel name (remove # if present)
            channel_name = channel.lstrip('#')
            
            # Try to get channel info
            response = await self.slack_client.conversations_list(
                types="public_channel,private_channel",
                limit=1000
            )
            
            # Search for the channel
            for ch in response["channels"]:
                if ch["name"] == channel_name:
                    return {
                        "exists": True,
                        "channel_id": ch["id"],
                        "channel_name": ch["name"],
                        "is_private": ch["is_private"]
                    }
            
            return {"exists": False, "channel_name": channel_name}
            
        except SlackApiError as e:
            logger.error(f"Error verifying channel {channel}: {e.response['error']}")
            return {
                "exists": False,
                "error": f"Slack API error: {e.response['error']}",
                "error_code": e.response['error']
            }
        except Exception as e:
            logger.error(f"Unexpected error verifying channel {channel}: {str(e)}")
            return {"exists": False, "error": f"Verification failed: {str(e)}"}
    
    async def _check_channel_creation_permissions(self) -> Dict[str, Any]:
        """
        Check if the bot has permissions to create channels
        
        Returns:
            Dict with permission status and details
        """
        if not self.slack_enabled or not self.slack_client:
            return {"can_create": False, "error": "Slack integration not configured"}
        
        try:
            # Test bot permissions by checking auth info
            auth_response = await self.slack_client.auth_test()
            
            if not auth_response["ok"]:
                return {"can_create": False, "error": "Bot authentication failed"}
            
            # Check bot scopes - we need channels:write or conversations:write
            try:
                # Try to get bot info to check scopes
                bot_info = await self.slack_client.bots_info(bot=auth_response["bot_id"])
                
                if bot_info["ok"] and "bot" in bot_info:
                    scopes = bot_info["bot"].get("app_oauth_scopes", [])
                    required_scopes = ["channels:write", "conversations:write"]
                    
                    has_permission = any(scope in scopes for scope in required_scopes)
                    
                    return {
                        "can_create": has_permission,
                        "bot_id": auth_response["bot_id"],
                        "scopes": scopes,
                        "required_scopes": required_scopes
                    }
                else:
                    # Fallback: assume we can create if auth is successful
                    logger.warning("Could not verify bot scopes, assuming creation permissions")
                    return {"can_create": True, "bot_id": auth_response["bot_id"]}
                    
            except SlackApiError as scope_error:
                # If we can't check scopes, assume we have permission if auth works
                logger.warning(f"Could not check bot scopes: {scope_error.response['error']}")
                return {"can_create": True, "bot_id": auth_response["bot_id"]}
            
        except SlackApiError as e:
            logger.error(f"Error checking channel creation permissions: {e.response['error']}")
            return {
                "can_create": False,
                "error": f"Permission check failed: {e.response['error']}",
                "error_code": e.response['error']
            }
        except Exception as e:
            logger.error(f"Unexpected error checking permissions: {str(e)}")
            return {"can_create": False, "error": f"Permission check failed: {str(e)}"}
    
    async def _create_slack_channel(self, channel_name: str, is_private: bool = False) -> Dict[str, Any]:
        """
        Create a new Slack channel
        
        Args:
            channel_name: Name of the channel to create (without # prefix)
            is_private: Whether to create a private channel
            
        Returns:
            Dict with creation result and channel info
        """
        if not self.slack_enabled or not self.slack_client:
            return {"created": False, "error": "Slack integration not configured"}
        
        try:
            # Normalize channel name
            channel_name = channel_name.lstrip('#').lower()
            
            # Validate channel name format
            if not channel_name or len(channel_name) > 21:
                return {
                    "created": False,
                    "error": "Invalid channel name: must be 1-21 characters"
                }
            
            # Create the channel
            response = await self.slack_client.conversations_create(
                name=channel_name,
                is_private=is_private
            )
            
            if response["ok"]:
                channel_info = response["channel"]
                logger.info(f"Successfully created Slack channel: #{channel_name}")
                
                return {
                    "created": True,
                    "channel_id": channel_info["id"],
                    "channel_name": channel_info["name"],
                    "is_private": channel_info["is_private"]
                }
            else:
                return {
                    "created": False,
                    "error": "Channel creation failed: unknown error"
                }
                
        except SlackApiError as e:
            error_code = e.response['error']
            
            if error_code == "name_taken":
                error_msg = f"Channel #{channel_name} already exists"
            elif error_code == "invalid_name":
                error_msg = f"Invalid channel name: {channel_name}"
            elif error_code == "missing_scope":
                error_msg = "Insufficient permissions to create channels"
            else:
                error_msg = f"Slack API error: {error_code}"
            
            logger.error(f"Error creating channel #{channel_name}: {error_msg}")
            return {
                "created": False,
                "error": error_msg,
                "error_code": error_code
            }
        except Exception as e:
            logger.error(f"Unexpected error creating channel #{channel_name}: {str(e)}")
            return {"created": False, "error": f"Channel creation failed: {str(e)}"}
    
    async def send_slack_notification(self, channel: str = None, message: str = "", ticket_id: int = None, notification_type: str = "general") -> Dict[str, Any]:
        """Send Slack notification with rich formatting and automatic channel creation"""
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
                    channel = await self.settings_manager.get_setting_value('slack_new_ticket_channel', '#tickets')
                elif notification_type == "escalated_ticket":
                    channel = await self.settings_manager.get_setting_value('slack_escalation_channel', '#escalations')
                elif notification_type == "resolved_ticket":
                    channel = await self.settings_manager.get_setting_value('slack_resolution_channel', '#resolutions')
                elif notification_type == "agent_assignment":
                    channel = await self.settings_manager.get_setting_value('slack_agent_assignment_channel', '#assignments')
                else:
                    channel = await self.settings_manager.get_setting_value('slack_new_ticket_channel', '#tickets')
            
            # Verify channel exists before attempting to send message
            channel_verification = await self._verify_slack_channel_exists(channel)
            
            if not channel_verification["exists"]:
                # Channel doesn't exist, check if we can create it
                if "error" in channel_verification:
                    logger.error(f"Channel verification failed for {channel}: {channel_verification['error']}")
                    return {
                        "status": "failed",
                        "error": f"Channel verification failed: {channel_verification['error']}",
                        "channel": channel
                    }
                
                logger.info(f"Channel {channel} does not exist, checking creation permissions...")
                
                # Check if we have permissions to create the channel
                permission_check = await self._check_channel_creation_permissions()
                
                if not permission_check["can_create"]:
                    error_msg = f"Channel {channel} does not exist and insufficient permissions to create it"
                    if "error" in permission_check:
                        error_msg += f": {permission_check['error']}"
                    
                    logger.error(error_msg)
                    return {
                        "status": "failed",
                        "error": error_msg,
                        "channel": channel,
                        "permission_details": permission_check
                    }
                
                # Attempt to create the channel
                logger.info(f"Creating channel {channel}...")
                creation_result = await self._create_slack_channel(
                    channel_verification["channel_name"],
                    is_private=False  # Default to public channels
                )
                
                if not creation_result["created"]:
                    error_msg = f"Failed to create channel {channel}: {creation_result['error']}"
                    logger.error(error_msg)
                    return {
                        "status": "failed",
                        "error": error_msg,
                        "channel": channel,
                        "creation_details": creation_result
                    }
                
                logger.info(f"Successfully created channel {channel}")
                # Update channel reference to use the created channel ID or name
                channel = f"#{creation_result['channel_name']}"
            
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
            error_code = e.response['error']
            
            # Enhanced error handling with specific context
            if error_code == "channel_not_found":
                error_msg = f"Channel {channel} not found after verification - this should not happen"
                logger.error(f"{error_msg}. Channel verification may have failed.")
            elif error_code == "not_in_channel":
                error_msg = f"Bot is not a member of channel {channel}"
                logger.error(f"{error_msg}. Bot may need to be invited to the channel.")
            elif error_code == "is_archived":
                error_msg = f"Channel {channel} is archived"
                logger.error(f"{error_msg}. Channel needs to be unarchived before posting.")
            elif error_code == "msg_too_long":
                error_msg = f"Message too long for Slack (max 40,000 characters)"
                logger.error(f"{error_msg}. Message length: {len(message)} characters.")
            elif error_code == "rate_limited":
                error_msg = f"Slack API rate limit exceeded"
                logger.error(f"{error_msg}. Consider implementing retry logic with backoff.")
            else:
                error_msg = f"Slack API error: {error_code}"
                logger.error(f"{error_msg} for channel {channel}, ticket {ticket_id}, type {notification_type}")
            
            return {
                "status": "failed",
                "error": error_msg,
                "error_code": error_code,
                "channel": channel,
                "ticket_id": ticket_id,
                "notification_type": notification_type
            }
        except Exception as e:
            error_msg = f"Slack notification failed: {str(e)}"
            logger.error(f"{error_msg} for channel {channel}, ticket {ticket_id}, type {notification_type}")
            logger.exception("Full exception details:")
            return {
                "status": "failed",
                "error": error_msg,
                "channel": channel,
                "ticket_id": ticket_id,
                "notification_type": notification_type
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
                    to_email = await self.settings_manager.get_setting_value('resend_new_ticket_recipient', '')
                elif notification_type == "escalated_ticket":
                    to_email = await self.settings_manager.get_setting_value('resend_escalation_recipient', '')
                elif notification_type == "resolved_ticket":
                    to_email = await self.settings_manager.get_setting_value('resend_resolution_recipient', '')
                elif notification_type == "agent_assignment":
                    to_email = await self.settings_manager.get_setting_value('resend_agent_assignment_recipient', '')
                else:
                    to_email = await self.settings_manager.get_setting_value('resend_new_ticket_recipient', '')
                
                if not to_email:
                    logger.warning(f"No email recipient configured for notification type: {notification_type}")
                    return {"success": False, "error": "No recipient configured"}
            
            # Get sender email from settings
            from_email = await self.settings_manager.get_setting_value('resend_from_email', 'noreply@ticketflow.ai')
            from_name = await self.settings_manager.get_setting_value('resend_from_name', 'TicketFlow Support')
            reply_to = await self.settings_manager.get_setting_value('resend_reply_to_email', from_email)
            
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
            
            # Get tracking settings
            track_opens = await self.settings_manager.get_setting_value('resend_track_opens', True)
            track_clicks = await self.settings_manager.get_setting_value('resend_track_clicks', True)
            
            # Prepare email data
            email_data = {
                "from": f"{from_name} <{from_email}>",
                "to": [to_email],
                "subject": formatted_subject,
                "html": content
            }
            
            # Add reply-to if different from sender
            if reply_to and reply_to != from_email:
                email_data["reply_to"] = [reply_to]
            
            # Add tracking options
            if track_opens or track_clicks:
                email_data["tags"] = [
                    {"name": "notification_type", "value": notification_type},
                    {"name": "ticket_id", "value": str(ticket_id) if ticket_id else "none"}
                ]
            
            # Send email using Resend
            response = resend.Emails.send(email_data)
            
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