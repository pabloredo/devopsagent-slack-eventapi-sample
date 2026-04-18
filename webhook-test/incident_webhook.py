import hashlib
import hmac
import json
import base64
import os
from datetime import datetime, timezone
from typing import Optional
import urllib.request

from dotenv import load_dotenv

load_dotenv()


class IncidentWebhook:
    def __init__(self, secret: Optional[str] = None, webhook_url: Optional[str] = None):
        self.secret = secret or os.environ["WEBHOOK_SECRET"]
        self.webhook_url = webhook_url or os.environ["WEBHOOK_URL"]

    def send(
        self,
        incident_id: str,
        action: str,
        priority: str,
        title: str,
        description: Optional[str] = None,
        timestamp: Optional[str] = None,
        service: Optional[str] = None,
        data: Optional[dict] = None,
    ):
        payload = {
            "eventType": "incident",
            "incidentId": incident_id,
            "action": action,
            "priority": priority,
            "title": title,
        }
        if description is not None:
            payload["description"] = description
        if timestamp is not None:
            payload["timestamp"] = timestamp
        if service is not None:
            payload["service"] = service
        if data is not None:
            payload["data"] = data

        ts = datetime.now(timezone.utc).isoformat()
        body = json.dumps(payload)
        signature = base64.b64encode(
            hmac.new(self.secret.encode(), f"{ts}:{body}".encode(), hashlib.sha256).digest()
        ).decode()

        req = urllib.request.Request(
            self.webhook_url,
            data=body.encode(),
            headers={
                "Content-Type": "application/json",
                "x-amzn-event-timestamp": ts,
                "x-amzn-event-signature": signature,
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
