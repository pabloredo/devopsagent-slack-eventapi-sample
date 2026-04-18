# DevOps Agent

A project for testing and integrating DevOps automation with Slack and AgentCore webhooks.

## License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute this code. However, this software is provided "as is", **without warranty of any kind**. Use at your own responsibility.

See the [MIT License](https://opensource.org/licenses/MIT) for full details.

## Project Structure

### `slack-app/`
A minimal AWS Lambda function with API Gateway for receiving Slack Event API requests.

**Features:**
- ✅ URL verification handling
- ✅ Request signature verification
- ✅ Event callbacks (app_mention, messages, etc.)
- ✅ Interactive events (buttons, modals, etc.)
- ✅ Slash commands
- 🚀 Simple single-Lambda architecture
- 📦 Easy deployment with AWS CDK (Python)

**Architecture:**
```
Slack → API Gateway → Lambda Function
```

### `webhook-test/`
Test scripts for validating webhook connectivity with AgentCore.

**Purpose:** Test and verify webhook integration with the AgentCore system for incident management and automation workflows.

---

## Slack App Setup

## Prerequisites

1. AWS CLI configured with credentials
2. Node.js and npm (for AWS CDK CLI)
3. Python 3.11+
4. AWS CDK CLI: `npm install -g aws-cdk`
5. A Slack app with Event Subscriptions enabled
6. Your Slack app's Signing Secret

## Setup

### 1. Get Your Slack Signing Secret

1. Go to https://api.slack.com/apps
2. Select your app
3. Navigate to "Basic Information"
4. Copy the "Signing Secret"

### 2. Deploy to AWS

```bash
# Set your Slack signing secret
export SLACK_SIGNING_SECRET='your-signing-secret-here'

# Make the deploy script executable
chmod +x deploy.sh

# Deploy
./deploy.sh
```

### 3. Configure Slack Event Subscriptions

1. After deployment, the API URL will be shown in the CDK outputs
   You can also retrieve it with:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name SlackAppStack \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
     --output text
   ```

2. In your Slack app settings, go to "Event Subscriptions"
3. Enable Events and enter your API URL
4. Subscribe to the events you need (e.g., `app_mention`, `message.channels`)
5. Save changes

### 4. Configure Interactive Components (Optional)

If you want to handle button clicks, modals, etc.:

1. Go to "Interactivity & Shortcuts" in your Slack app settings
2. Enable Interactivity
3. Enter the same API URL as your Request URL
4. Save changes

## Local Testing

You can test the Lambda function locally by importing and calling it directly in Python, or by using AWS SAM CLI if you have it installed.

## Customization

Edit `lambda_function.py` to add your event handling logic:

```python
# Handle event callbacks
if payload.get('type') == 'event_callback':
    event_data = payload.get('event', {})
    event_type = event_data.get('type')

    if event_type == 'app_mention':
        # Your logic here
        pass
```

## Monitoring

View logs in CloudWatch:

```bash
# Get the function name from CDK outputs, then:
aws logs tail /aws/lambda/<function-name> --follow
```

## Cleanup

Remove all resources:

```bash
cdk destroy
```

## What's Different from the Reference App?

The reference `amazon-interactive-slack-app-starter-kit` includes:
- Step Functions for workflow orchestration
- DynamoDB for user management
- EventBridge for event routing
- Complex authorization and channel validation
- Multiple Lambda functions

This simplified version:
- ✅ Single Lambda function
- ✅ Direct event handling
- ✅ No database required
- ✅ Minimal dependencies
- ✅ Easy to understand and extend

Perfect for simple bots, webhooks, or as a starting point for more complex apps.

---

## Webhook Testing

The `webhook-test/` directory contains utilities for testing webhook connectivity with AgentCore:

- `incident_webhook.py` - Webhook handler implementation
- `test_incident.py` - Test script for validating webhook functionality

Use these to verify that your AgentCore webhook integration is working correctly before deploying to production.
