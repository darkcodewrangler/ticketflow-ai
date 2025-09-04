from typing import Dict
from openai import OpenAI
from slack_sdk import WebClient as SlackClient
import resend
from .config import config

resend.api_key=config.RESEND_API_KEY

client=OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL
)
class ExternalToolsManager:
    """Handles all external integrations"""
    
    def __init__(self):
        self.slack_client = SlackClient()
        self.email_client = resend
        self.ai_client = client
        self.ticket_system = TicketSystemClient()
    
    async def resolve_ticket(self, ticket_id: str, resolution: str, confidence: float) -> Dict:
        """Mark ticket as resolved in the ticketing system"""
        return await self.ticket_system.update_ticket(
            ticket_id=ticket_id,
            status="resolved",
            resolution=resolution,
            resolved_by="smartsupport_agent",
            confidence_score=confidence
        )
    
    async def send_notification(self, team: str, message: str, ticket_id: str) -> Dict:
        """Send notification to relevant team via Slack"""
        channel = self._get_team_channel(team)
        return await self.slack_client.send_message(
            channel=channel,
            message=f"🎫 Ticket #{ticket_id}: {message}",
            attachments=[{
                "color": "warning",
                "fields": [
                    {"title": "Ticket ID", "value": ticket_id, "short": True},
                    {"title": "Team", "value": team, "short": True}
                ]
            }]
        )
