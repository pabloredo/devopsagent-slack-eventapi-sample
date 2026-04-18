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

### `test-endpoint/`
Test scripts for validating the deployed Slack Event API endpoint.

**Purpose:** Comprehensive test suite to verify URL verification, event callbacks, and signature validation.

**Configuration:** Uses local `.env` file for Slack API URL and signing secret.

### `test-webhook/`
Test scripts for validating webhook connectivity with AgentCore.

**Purpose:** Test and verify webhook integration with the AgentCore system for incident management and automation workflows.

**Configuration:** Uses local `.env` file for webhook URL and secret.

---

## Slack App Setup

## Prerequisites

1. AWS CLI configured with credentials
2. Node.js and npm (for AWS CDK CLI)
3. Python 3.11+
4. AWS CDK CLI: `npm install -g aws-cdk`
5. A Slack app with Event Subscriptions enabled
6. Your Slack app's Signing Secret and Bot Token

## Setup

### 1. Get Your Slack Credentials

**Signing Secret:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Navigate to "Basic Information"
4. Copy the "Signing Secret"

**Bot Token:**
1. In your Slack app settings, navigate to "OAuth & Permissions"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
3. Ensure your bot has the following OAuth scopes:
   - `chat:write` - To send messages
   - `app_mentions:read` - To receive mention events

### 2. Deploy to AWS

```bash
# Set your Slack signing secret and bot token
export SLACK_SIGNING_SECRET='your-signing-secret-here'
export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'

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

The reference [amazon-interactive-slack-app-starter-kit](https://github.com/aws-samples/amazon-interactive-slack-app-starter-kit) includes:
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

## Testing

### Prerequisites for Testing

Install required Python packages:

```bash
pip install requests python-dotenv
```

### Endpoint Testing

The `test-endpoint/` directory contains scripts for testing the deployed Slack Event API.

**Setup:**

1. Copy `.env.template` to `.env` in the `test-endpoint/` directory:
   ```bash
   cd test-endpoint
   cp .env.template .env
   ```

2. Edit `.env` and add your configuration:
   ```
   SLACK_API_URL=https://your-api-gateway-url.amazonaws.com/prod/slack/events
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   ```

   Note: The bot token is only needed if you want to test message sending functionality.

**Run Tests:**

```bash
cd test-endpoint
python test_slack_endpoint.py
```

The test suite validates:
- URL verification challenge
- Event callback handling (app_mention, message)
- Request signature verification

### Webhook Testing

The `test-webhook/` directory contains utilities for testing webhook connectivity with AgentCore.

**Setup:**

1. Copy `.env.template` to `.env` in the `test-webhook/` directory:
   ```bash
   cd test-webhook
   cp .env.template .env
   ```

2. Edit `.env` and add your webhook configuration:
   ```
   WEBHOOK_SECRET=your-webhook-secret
   WEBHOOK_URL=https://your-webhook-url
   ```

**Run Tests:**

```bash
cd test-webhook
python test_incident.py
```

This verifies that your AgentCore webhook integration is working correctly before deploying to production.
