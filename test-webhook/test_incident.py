from incident_webhook import IncidentWebhook

webhook = IncidentWebhook()  # Loads secret from .env

try:
    status, body = webhook.send(
        incident_id="INC-001",
        action="created",
        priority="HIGH",
        title="Database connection pool exhausted",
        description="Primary RDS instance hitting max connections",
        service="order-service",
        data={"region": "us-east-1", "db_instance": "prod-primary"},
    )
    print(f"✅ Success — Status: {status}\nResponse: {body}")
except Exception as e:
    print(f"❌ Failed — {e}")
