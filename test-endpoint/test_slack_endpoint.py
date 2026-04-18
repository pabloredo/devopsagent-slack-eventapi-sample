#!/usr/bin/env python3
"""
Test script for Slack Event API endpoint
Tests URL verification and event callback handling
"""

import requests
import json
import hashlib
import hmac
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Configuration
API_URL = os.getenv("SLACK_API_URL")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

if not API_URL or not SLACK_SIGNING_SECRET:
    raise ValueError(
        "Missing required environment variables. "
        "Please set SLACK_API_URL and SLACK_SIGNING_SECRET in .env file"
    )


def generate_slack_signature(timestamp: str, body: str) -> str:
    """Generate Slack request signature for verification"""
    sig_basestring = f"v0:{timestamp}:{body}"
    signature = hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"v0={signature}"


def test_url_verification():
    """Test URL verification challenge"""
    print("\n=== Testing URL Verification ===")

    challenge = "test_challenge_value_12345"
    payload = {
        "type": "url_verification",
        "challenge": challenge
    }

    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = generate_slack_signature(timestamp, body)

    headers = {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature
    }

    try:
        response = requests.post(API_URL, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("challenge") == challenge:
                print("✅ URL verification test PASSED")
                return True
            else:
                print("❌ URL verification test FAILED - challenge mismatch")
                return False
        else:
            print("❌ URL verification test FAILED - non-200 status")
            return False
    except Exception as e:
        print(f"❌ URL verification test FAILED - {e}")
        return False


def test_app_mention_event():
    """Test app_mention event callback"""
    print("\n=== Testing app_mention Event ===")

    payload = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "user": "U123456",
            "text": "<@U987654> Hello bot!",
            "ts": "1234567890.123456",
            "channel": "C123456",
            "event_ts": "1234567890.123456"
        },
        "event_id": "Ev123456",
        "event_time": 1234567890
    }

    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = generate_slack_signature(timestamp, body)

    headers = {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature
    }

    try:
        response = requests.post(API_URL, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ app_mention event test PASSED")
            return True
        else:
            print("❌ app_mention event test FAILED")
            return False
    except Exception as e:
        print(f"❌ app_mention event test FAILED - {e}")
        return False


def test_message_event():
    """Test message event callback"""
    print("\n=== Testing message Event ===")

    payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "user": "U123456",
            "text": "Hello channel!",
            "ts": "1234567890.123456",
            "channel": "C123456",
            "event_ts": "1234567890.123456"
        },
        "event_id": "Ev123457",
        "event_time": 1234567890
    }

    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = generate_slack_signature(timestamp, body)

    headers = {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature
    }

    try:
        response = requests.post(API_URL, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ message event test PASSED")
            return True
        else:
            print("❌ message event test FAILED")
            return False
    except Exception as e:
        print(f"❌ message event test FAILED - {e}")
        return False


def test_invalid_signature():
    """Test request with invalid signature (should fail)"""
    print("\n=== Testing Invalid Signature (should fail) ===")

    payload = {
        "type": "url_verification",
        "challenge": "test_challenge"
    }

    body = json.dumps(payload)
    timestamp = str(int(time.time()))

    headers = {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": "v0=invalid_signature"
    }

    try:
        response = requests.post(API_URL, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 401 or response.status_code == 403:
            print("✅ Invalid signature test PASSED (correctly rejected)")
            return True
        else:
            print("❌ Invalid signature test FAILED (should have been rejected)")
            return False
    except Exception as e:
        print(f"❌ Invalid signature test FAILED - {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Slack Event API Endpoint Tests")
    print(f"Testing endpoint: {API_URL}")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("URL Verification", test_url_verification()))
    results.append(("app_mention Event", test_app_mention_event()))
    results.append(("message Event", test_message_event()))
    results.append(("Invalid Signature", test_invalid_signature()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
