from datetime import datetime
from agent_framework import Message

def make_json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    return value

def normalize_messages(data_messages):
    return [Message(
        role=msg['role'],
        text=msg['content'][0]['text'] if msg.get('content') and msg['content'][0].get('text') else "",
        # Add other fields as needed, e.g. id, createdAt, attachments, metadata
        message_id=msg.get('id')
    ) for msg in data_messages]