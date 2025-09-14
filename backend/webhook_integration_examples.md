# Webhook Integration Examples

This document provides examples of how to integrate external platforms with TicketFlow AI using the webhook endpoint.

## Endpoint Information

- **URL**: `POST /api/integrations/webhook`
- **Content-Type**: `application/json`
- **Response**: Created ticket data in TicketFlow format

## Supported Platforms

The webhook endpoint supports flexible field mapping for various platforms:

- **Zendesk**: `subject`, `description`, `priority`, `customer_email`
- **Freshdesk**: `title`, `body`, `category`, `user_email`
- **Jira**: `title`, `description`, `platform`, `user_id`
- **ServiceNow**: `title`, `description`, `priority`, `user_email`
- **Custom platforms**: Any combination of supported fields

## Field Mapping

The webhook automatically maps external fields to internal TicketFlow fields:

| External Field                   | Internal Field    | Description                             |
| -------------------------------- | ----------------- | --------------------------------------- |
| `subject` or `title`             | `title`           | Ticket title                            |
| `description` or `body`          | `description`     | Ticket description                      |
| `category`                       | `category`        | Ticket category (default: "general")    |
| `priority`                       | `priority`        | Priority level (low/medium/high/urgent) |
| `customer_email` or `user_email` | `user_email`      | Customer email address                  |
| `user_id`                        | `user_id`         | User identifier                         |
| `id`                             | `external_id`     | External ticket ID (stored in metadata) |
| `platform`                       | `platform`        | Source platform (stored in metadata)    |
| `metadata`                       | `ticket_metadata` | Additional metadata                     |

## Example Integrations

### 1. Zendesk Integration

```python
import requests

# Zendesk webhook payload
zendesk_data = {
    "subject": "Password reset not working",
    "description": "I've tried resetting my password multiple times but never receive the email.",
    "priority": "high",
    "customer_email": "user@example.com",
    "platform": "zendesk"
}

response = requests.post(
    "http://localhost:8000/api/integrations/webhook",
    json=zendesk_data
)

if response.status_code == 200:
    ticket = response.json()
    print(f"Created ticket {ticket['id']}: {ticket['title']}")
```

### 2. Freshdesk Integration

```python
# Freshdesk webhook payload
freshdesk_data = {
    "title": "API integration failing",
    "body": "Our API calls are returning 500 errors since this morning.",
    "category": "technical",
    "priority": "urgent",
    "user_email": "dev@company.com",
    "platform": "freshdesk"
}

response = requests.post(
    "http://localhost:8000/api/integrations/webhook",
    json=freshdesk_data
)
```

### 3. Jira Integration

```python
# Jira webhook payload
jira_data = {
    "title": "Feature request: Dark mode",
    "description": "Users are requesting a dark mode option for the dashboard.",
    "category": "feature_request",
    "priority": "medium",
    "user_id": "jira-12345",
    "platform": "jira"
}

response = requests.post(
    "http://localhost:8000/api/integrations/webhook",
    json=jira_data
)
```

### 4. Custom Platform Integration

```python
# Custom platform webhook payload
custom_data = {
    "title": "Billing inquiry",
    "description": "Question about monthly subscription charges",
    "category": "billing",
    "priority": "low",
    "customer_email": "billing@customer.com",
    "id": "ext-789",
    "platform": "custom_system",
    "metadata": {
        "source_url": "https://custom-system.com/ticket/789",
        "department": "finance",
        "custom_field": "value"
    }
}

response = requests.post(
    "http://localhost:8000/api/integrations/webhook",
    json=custom_data
)
```

## Batch Processing

For platforms that send multiple tickets at once, use the batch endpoint:

```python
# Batch webhook payload
batch_data = [
    {
        "title": "Ticket 1",
        "description": "Description 1",
        "priority": "high",
        "user_email": "user1@example.com"
    },
    {
        "title": "Ticket 2",
        "description": "Description 2",
        "priority": "medium",
        "user_email": "user2@example.com"
    }
]

response = requests.post(
    "http://localhost:8000/api/integrations/webhook/batch",
    json=batch_data
)

result = response.json()
print(f"Created {result['created_count']} tickets")
print(f"Failed {result['failed_count']} tickets")
```

## Error Handling

The webhook endpoint returns appropriate HTTP status codes:

- **200**: Ticket created successfully
- **400**: Invalid request data (missing required fields)
- **500**: Internal server error

Example error response:

```json
{
  "detail": "Title or subject is required"
}
```

## Health Check

Check if the webhook endpoint is available:

```python
response = requests.get("http://localhost:8000/api/integrations/webhook/health")
print(response.json())
```

Response:

```json
{
  "status": "healthy",
  "endpoint": "webhook",
  "supported_platforms": [
    "zendesk",
    "freshdesk",
    "jira",
    "servicenow",
    "custom"
  ],
  "features": [
    "flexible_field_mapping",
    "automatic_validation",
    "batch_processing",
    "metadata_preservation"
  ]
}
```

## Security Considerations

1. **Authentication**: Add API key validation for production use
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **IP Whitelisting**: Restrict access to known external platform IPs
4. **Data Validation**: The endpoint validates all incoming data
5. **Logging**: All webhook requests are logged for audit purposes

## Testing

Use the provided test script to verify webhook functionality:

```bash
python test_webhook_endpoint.py
```

This will test various platform formats and verify the webhook works correctly.
