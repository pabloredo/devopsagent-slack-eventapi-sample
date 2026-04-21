#!/usr/bin/env python3
"""
Simple script to test posting a message to a Slack channel
Usage: python3 test_post_message.py CHANNEL_ID
"""

import os
import sys
import json
import ssl
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))  # Default 15 seconds

# Create secure SSL context with proper certificate verification
try:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    # Fall back to default context if certifi is not available
    ssl_context = ssl.create_default_context()

def post_message(channel_id, message="Test message from local script"):
    """Post a message to the specified channel"""

    if not SLACK_BOT_TOKEN:
        print("❌ ERROR: SLACK_BOT_TOKEN not found in .env file")
        return False

    print(f"Bot Token: {SLACK_BOT_TOKEN[:15]}...")
    print(f"Channel: {channel_id}")
    print(f"Message: {message}\n")

    payload = {
        'channel': channel_id,
        'text': message
    }

    try:
        req = urllib.request.Request(
            'https://slack.com/api/chat.postMessage',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
            },
            method='POST'
        )

        with urllib.request.urlopen(req, context=ssl_context, timeout=HTTP_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))

            print("API Response:")
            print(json.dumps(result, indent=2))

            if result.get('ok'):
                print(f"\n✅ Message posted successfully!")
                return True
            else:
                error = result.get('error')
                print(f"\n❌ Failed: {error}")

                if error == 'invalid_auth':
                    print("\nThe token is invalid. This usually means:")
                    print("- Token has been regenerated in Slack")
                    print("- Token is from a different workspace")
                    print("- Token has been revoked")
                elif error == 'not_in_channel':
                    print("\nThe bot is not in this channel.")
                    print("Add it with: /invite @awsdevopsagent")
                elif error == 'channel_not_found':
                    print("\nChannel ID not found. Make sure it's correct.")
                elif error == 'missing_scope':
                    print("\nMissing OAuth scope. Add 'chat:write' in Slack app settings.")

                return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_post_message.py CHANNEL_ID [MESSAGE]")
        print("Example: python3 test_post_message.py C0123456789")
        print("\nYou can find the channel ID in Slack:")
        print("  Right-click channel → View channel details → Copy ID")
        sys.exit(1)

    channel_id = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else "Test message from local bot verification"

    success = post_message(channel_id, message)
    sys.exit(0 if success else 1)
