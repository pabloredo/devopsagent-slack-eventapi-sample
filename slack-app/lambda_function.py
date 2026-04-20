import json
import hashlib
import hmac
import time
import os
from urllib.parse import parse_qs
import urllib.request
import urllib.error

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

def post_slack_message(channel, text, thread_ts=None):
    """Post a message to Slack using the Web API."""
    bot_token = os.environ.get('SLACK_BOT_TOKEN', '')

    print(f"Attempting to post message to channel: {channel}")
    print(f"Message text: {text}")
    print(f"Thread ts: {thread_ts}")

    if not bot_token or bot_token == 'REPLACE_WITH_YOUR_BOT_TOKEN':
        print("ERROR: SLACK_BOT_TOKEN not configured")
        return False

    payload = {
        'channel': channel,
        'text': text
    }

    if thread_ts:
        payload['thread_ts'] = thread_ts

    print(f"Payload: {json.dumps(payload)}")

    try:
        req = urllib.request.Request(
            'https://slack.com/api/chat.postMessage',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {bot_token[:10]}...'  # Only log first 10 chars for security
            },
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
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
            text = payload.get('text', '')

            print(f"Received slash command: {command}")
            print(f"Channel: {channel_id}")
            print(f"User: {user_id}")
            print(f"Text: {text}")

            # Post confirmation message to the channel
            message = f"I received your request. Working on the investigation..."
            print(f"Calling post_slack_message for slash command...")
            result = post_slack_message(channel_id, message)
            print(f"post_slack_message returned: {result}")

            # Return immediate acknowledgment (this is required for slash commands)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': f'Investigation started for: {text}'
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
