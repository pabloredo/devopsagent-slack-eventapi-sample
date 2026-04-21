import json
import hashlib
import hmac
import time
import os
from urllib.parse import parse_qs
import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Configuration
HTTP_TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', '15'))  # Default 15 seconds

# Cache for secrets to avoid repeated API calls
_secrets_cache = None

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager"""
    global _secrets_cache

    # Return cached secrets if available
    if _secrets_cache is not None:
        return _secrets_cache

    secret_arn = os.environ.get('SECRET_ARN')
    if not secret_arn:
        raise ValueError("SECRET_ARN environment variable not set")

    print(f"Retrieving secrets from Secrets Manager: {secret_arn}")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
        secret_string = get_secret_value_response['SecretString']
        secrets = json.loads(secret_string)

        # Cache the secrets
        _secrets_cache = secrets
        print("✅ Secrets retrieved successfully")
        return secrets

    except ClientError as e:
        print(f"❌ Error retrieving secrets: {e}")
        raise e

def verify_slack_request(body, timestamp, signature):
    """Verify the request is from Slack using the signing secret."""
    secrets = get_secrets()
    signing_secret = secrets.get('SLACK_SIGNING_SECRET', '')

    # Check if timestamp is within 5 minutes
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False

    # Create the signature base string
    sig_basestring = f"v0:{timestamp}:{body}"

    # Calculate the expected signature
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(my_signature, signature)

def post_slack_message(channel, text, thread_ts=None):
    """Post a message to Slack using the Web API."""
    secrets = get_secrets()
    bot_token = secrets.get('SLACK_BOT_TOKEN', '')

    print(f"Attempting to post message to channel: {channel}")
    print(f"Message text: {text}")
    print(f"Thread ts: {thread_ts}")

    if not bot_token:
        print("ERROR: SLACK_BOT_TOKEN not configured in secrets")
        return False

    payload = {
        'channel': channel,
        'text': text
    }

    if thread_ts:
        payload['thread_ts'] = thread_ts

    print(f"Payload: {json.dumps(payload)}")
    print(f"Using bot token: {bot_token[:15]}... (truncated for security)")

    try:
        req = urllib.request.Request(
            'https://slack.com/api/chat.postMessage',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {bot_token}'
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Slack API Response: {json.dumps(result)}")

            if result.get('ok'):
                print(f"✅ Message posted successfully to channel {channel}")
                return True
            else:
                error = result.get('error')
                print(f"❌ Failed to post message. Error: {error}")
                if 'needed' in result:
                    print(f"Missing scopes: {result.get('needed')}")
                if 'provided' in result:
                    print(f"Provided scopes: {result.get('provided')}")
                return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error body'
        print(f"❌ HTTP error posting message: {e.code} - {e.reason}")
        print(f"Error body: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Exception posting message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_webhook_incident(incident_id, title, description=None, priority="MEDIUM", service=None):
    """Send incident to AWS DevOps Agent webhook"""
    secrets = get_secrets()
    webhook_secret = secrets.get('WEBHOOK_SECRET', '')
    webhook_url = secrets.get('WEBHOOK_URL', '')

    print(f"Sending incident to webhook: {incident_id}")
    print(f"Webhook URL: {webhook_url[:50]}..." if webhook_url else "No webhook URL configured")

    if not webhook_secret or not webhook_url:
        print("WARNING: WEBHOOK_SECRET or WEBHOOK_URL not configured in secrets")
        return False

    # Build incident payload
    payload = {
        "eventType": "incident",
        "incidentId": incident_id,
        "action": "created",
        "priority": priority,
        "title": title,
    }

    if description:
        payload["description"] = description
    if service:
        payload["service"] = service

    # Add timestamp and metadata
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    payload["data"] = {
        "source": "slack",
        "automated": True
    }

    # Generate signature
    ts = datetime.now(timezone.utc).isoformat()
    body = json.dumps(payload)
    signature = base64.b64encode(
        hmac.new(webhook_secret.encode(), f"{ts}:{body}".encode(), hashlib.sha256).digest()
    ).decode()

    print(f"Webhook payload: {body}")

    try:
        req = urllib.request.Request(
            webhook_url,
            data=body.encode(),
            headers={
                "Content-Type": "application/json",
                "x-amzn-event-timestamp": ts,
                "x-amzn-event-signature": signature,
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            status = resp.status
            response_body = resp.read().decode()
            print(f"✅ Webhook response: {status}")
            print(f"Response body: {response_body}")
            return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error body'
        print(f"❌ HTTP error sending webhook: {e.code} - {e.reason}")
        print(f"Error body: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Exception sending webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def lambda_handler(event, context):
    """
    Simple Lambda function to handle Slack Event API requests.
    Handles URL verification and event callbacks.
    """

    try:
        # Get the request body
        body = event.get('body', '')
        headers = event.get('headers', {})

        # Slack sends application/json for some events, application/x-www-form-urlencoded for others
        content_type = headers.get('content-type', headers.get('Content-Type', ''))

        if 'application/json' in content_type:
            # Parse JSON body
            if isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
        elif 'application/x-www-form-urlencoded' in content_type:
            # Parse form-encoded body
            parsed = parse_qs(body)
            if 'payload' in parsed:
                payload = json.loads(parsed['payload'][0])
            else:
                payload = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        else:
            payload = json.loads(body) if isinstance(body, str) else body

        # Verify request is from Slack
        timestamp = headers.get('x-slack-request-timestamp', headers.get('X-Slack-Request-Timestamp'))
        signature = headers.get('x-slack-signature', headers.get('X-Slack-Signature'))

        if not timestamp or not signature:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Missing signature headers'})
            }

        if not verify_slack_request(body, timestamp, signature):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }

        # Handle URL verification challenge
        if payload.get('type') == 'url_verification':
            return {
                'statusCode': 200,
                'body': json.dumps({'challenge': payload['challenge']})
            }

        # Handle event callbacks
        if payload.get('type') == 'event_callback':
            event_data = payload.get('event', {})
            event_type = event_data.get('type')

            print(f"Received event: {event_type}")
            print(f"Event data: {json.dumps(event_data, indent=2)}")

            # Handle app_mention events
            if event_type == 'app_mention':
                print("Processing app_mention event...")
                channel = event_data.get('channel')
                thread_ts = event_data.get('ts')

                print(f"Channel ID: {channel}")
                print(f"Thread timestamp: {thread_ts}")

                # Send a confirmation message
                message = "I received your request. Working on the investigation..."
                print(f"Calling post_slack_message...")
                result = post_slack_message(channel, message, thread_ts=thread_ts)
                print(f"post_slack_message returned: {result}")

            # Add your event handling logic here for other event types

            return {
                'statusCode': 200,
                'body': json.dumps({'ok': True})
            }

        # Handle interactive events (button clicks, etc.)
        if payload.get('type') in ['block_actions', 'view_submission', 'shortcut']:
            action_type = payload.get('type')
            print(f"Received interactive event: {action_type}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Add your interactive handling logic here

            return {
                'statusCode': 200,
                'body': json.dumps({'ok': True})
            }

        # Handle slash commands
        if payload.get('command'):
            command = payload.get('command')
            channel_id = payload.get('channel_id')
            user_id = payload.get('user_id')
            user_name = payload.get('user_name', 'unknown')
            text = payload.get('text', '')
            channel_name = payload.get('channel_name', 'unknown')

            print(f"Received slash command: {command}")
            print(f"Channel: {channel_id} ({channel_name})")
            print(f"User: {user_id} ({user_name})")
            print(f"Text: {text}")

            # Generate incident ID based on timestamp
            incident_id = f"SLACK-{int(time.time())}"

            # Send incident to webhook
            title = text if text else "Investigation requested via Slack"
            description = f"Investigation requested by {user_name} in #{channel_name}"

            print(f"Triggering investigation: {incident_id}")
            webhook_result = send_webhook_incident(
                incident_id=incident_id,
                title=title,
                description=description,
                priority="HIGH",
                service=channel_name
            )

            # Post confirmation message to the channel
            if webhook_result:
                message = f"🔍 Investigation started: {incident_id}\n\n*Issue:* {title}\n\nI'm working on this now..."
            else:
                message = f"⚠️ Investigation request received but webhook failed. Incident ID: {incident_id}"

            print(f"Calling post_slack_message for slash command...")
            post_result = post_slack_message(channel_id, message)
            print(f"post_slack_message returned: {post_result}")

            # Return immediate acknowledgment (this is required for slash commands)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': f'✅ Investigation {incident_id} initiated'
                })
            }

        # Default response for unknown event types
        print(f"Unknown event type: {payload.get('type')}")
        return {
            'statusCode': 200,
            'body': json.dumps({'ok': True})
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
