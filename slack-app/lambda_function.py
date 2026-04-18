import json
import hashlib
import hmac
import time
import os
from urllib.parse import parse_qs

def verify_slack_request(body, timestamp, signature):
    """Verify the request is from Slack using the signing secret."""
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET', '')

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

        # Verify request is from Slack (skip for URL verification)
        if payload.get('type') != 'url_verification':
            timestamp = headers.get('x-slack-request-timestamp', headers.get('X-Slack-Request-Timestamp'))
            signature = headers.get('x-slack-signature', headers.get('X-Slack-Signature'))

            if timestamp and signature:
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

            # Add your event handling logic here
            # Example: respond to app_mention, message, etc.

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
            print(f"Received slash command: {command}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Body: {body}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Add your command handling logic here

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': f'Received command: {command}'
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
