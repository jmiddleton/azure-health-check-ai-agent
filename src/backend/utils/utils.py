from datetime import datetime
from agent_framework import ChatMessage

def make_json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    return value

def normalize_messages(data_messages):
    return [ChatMessage(
        role=msg['role'],
        text=msg['content'][0]['text'] if msg.get('content') and msg['content'][0].get('text') else "",
        # Add other fields as needed, e.g. id, createdAt, attachments, metadata
        id=msg.get('id'),
        created_at=msg.get('createdAt'),
        attachments=msg.get('attachments', []),
        metadata=msg.get('metadata', {})
    ) for msg in data_messages]