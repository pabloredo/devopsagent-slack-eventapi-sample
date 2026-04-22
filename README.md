# DevOps Agent

A sample integration of Slack with AWS DevOps Agent webhooks to trigger the execution of an incident.

**Note:** Incident response communication is already available natively in AWS DevOps Agent. See the [official documentation](https://docs.aws.amazon.com/devopsagent/latest/userguide/connecting-to-ticketing-and-chat-connecting-slack.html) for native Slack integration.

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
┌─────────────────────────────────────────────────────────────────────┐
│                              Slack                                  │
│  • /investigate command                                             │
│  • @mentions                                                        │
│  • Event callbacks                                                  │
└──────────────────┬──────────────────────────────────────────────────┘
                   │ HTTPS POST (signed request)
                   ▼
         ┌─────────────────────┐
         │   API Gateway       │
         │   /slack/events     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────────────────────────────┐
         │        Lambda Function                   │
         │  • Verify Slack signature                │
         │  • Handle events & commands              │
         │  • Generate incident IDs                 │
         └────┬────────────────┬────────────────────┘
              │                │
              │ IAM            │ HTTPS POST           Slack API
              │ GetSecret      │ (signed webhook)     chat.postMessage
              ▼                ▼                      ▼
    ┌──────────────────┐  ┌────────────────────--┐  ┌─────────────────┐
    │  Secrets Manager │  │  DevOpsAgent Webhook │  │  Slack Channel  │
    │  • Bot Token     │  │  • Incident          │  │  (confirmation) │
    │  • Signing Key   │  │    creation          │  └─────────────────┘
    │  • Webhook URL   │  │  • Investigation     │
    │  • Webhook Secret│  │    queue             │
    └──────────────────┘  └───────────────────--─┘
```

**Workflow:**
1. User runs `/investigate` command in Slack
2. Lambda receives the slash command
3. Lambda generates an incident ID
4. Lambda sends incident to AWS DevOps Agent webhook
5. Lambda posts confirmation message back to Slack channel
6. AWS DevOps Agent processes the investigation

### `test-endpoint/`
Test scripts for validating the deployed Slack Event API endpoint.

**Purpose:** Comprehensive test suite to verify URL verification, event callbacks, and signature validation.

**Configuration:** Uses local `.env` file for Slack API URL and signing secret.

### `test-webhook/`
Test scripts for validating webhook connectivity with DevOpsAgent.

**Purpose:** Test and verify webhook integration with the DevOpsAgent system for incident management and automation workflows.

**Configuration:** Uses local `.env` file for webhook URL and secret.

---

## Slack App Setup

## Prerequisites

1. AWS CLI configured with credentials
2. Node.js and npm (for AWS CDK CLI)
3. Python 3.11+
4. AWS CDK CLI: `npm install -g aws-cdk`
5. A Slack app with Event Subscriptions and Slash Commands enabled
6. Your Slack app's Signing Secret and Bot Token
7. AWS DevOps Agent webhook URL and secret (for investigation automation)

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

**Webhook Credentials (for AWS DevOps Agent):**
1. Get your webhook URL from AWS DevOps Agent
2. Get your webhook secret for request signing
3. These credentials enable the Lambda to trigger investigations in AWS DevOps Agent

### 2. Deploy to AWS

The deployment process automatically stores all credentials securely in AWS Secrets Manager:

```bash
# Set your Slack credentials
export SLACK_SIGNING_SECRET='your-signing-secret-here'
export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'

# Set your webhook credentials for AWS DevOps Agent integration
export WEBHOOK_SECRET='your-webhook-secret'
export WEBHOOK_URL='https://your-webhook-url'

# Make the deploy script executable
chmod +x deploy.sh

# Deploy (this will automatically update AWS Secrets Manager)
./deploy.sh
```

**Security Note:** Credentials are stored in AWS Secrets Manager, not as plain text environment variables in the Lambda. The Lambda retrieves secrets at runtime using IAM permissions.

**Timeout Configuration:** All HTTP requests (Slack API, webhook) use a configurable timeout (default: 15 seconds) to prevent hanging connections. This can be adjusted via the `HTTP_TIMEOUT` environment variable in Lambda or test scripts.

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

### 4. Invite the Bot to Your Channel

**Important:** The bot must be invited to any channel where you want it to respond.

1. Open the Slack channel where you want the bot to work (e.g., `#aws-DevOpsAgent`)
2. Type the following command:
   ```
   /invite @your-bot-name
   ```
   (Replace `your-bot-name` with your actual bot name, e.g., `@awsdevopsagent`)
3. Press Enter

The bot will now be able to read messages and respond in that channel.

### 5. Test the Bot

**Using Slash Commands (triggers investigation):**
```
/investigate Lambda performance issues in production
```

The bot will:
1. Create an incident ID (e.g., `SLACK-1776703420`)
2. Send the incident to AWS DevOps Agent webhook
3. Post a confirmation message with the incident ID

**Using @mentions:**
```
@your-bot-name hello
```

The bot should respond with:
> "I received your request. Working on the investigation..."

### 6. Configure Interactive Components (Optional)

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

## Updating Secrets

If you need to update credentials without redeploying:

```bash
# Set your updated credentials
export SLACK_SIGNING_SECRET='your-signing-secret-here'
export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'
export WEBHOOK_SECRET='your-webhook-secret'
export WEBHOOK_URL='https://your-webhook-url'

# Update secrets in AWS Secrets Manager
cd slack-app
chmod +x update-secrets.sh
./update-secrets.sh
```

The Lambda will automatically use the updated credentials on the next invocation (secrets are cached per Lambda instance).

## Cleanup

Remove all resources:

```bash
cdk destroy

# Optionally, delete the secrets from Secrets Manager
aws secretsmanager delete-secret --secret-id slack-app/credentials --force-delete-without-recovery
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
pip install requests python-dotenv certifi
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

**Test Bot Message Posting Locally:**

Before deploying or if you encounter issues, test that the bot can post messages:

```bash
cd test-endpoint
python3 test_post_message.py CHANNEL_ID
```

To get your channel ID:
- Right-click on the channel in Slack
- Click "View channel details"
- Scroll down and copy the Channel ID (starts with `C`)

Example:
```bash
python3 test_post_message.py C0123456789
```

**Common errors:**
- `not_in_channel`: The bot needs to be invited to the channel first using `/invite @your-bot-name`
- `invalid_auth`: The bot token is invalid or expired - get a new one from Slack app settings
- `missing_scope`: Add the `chat:write` OAuth scope in your Slack app settings

### Webhook Testing

The `test-webhook/` directory contains utilities for testing webhook connectivity with DevOpsAgent.

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

This verifies that your DevOpsAgent webhook integration is working correctly before deploying to production.

---

## Troubleshooting

### Bot Not Responding in Slack

If the bot doesn't respond when mentioned:

1. **Check if the bot is in the channel:**
   - The bot must be invited to the channel using `/invite @your-bot-name`

2. **Verify bot token is correct:**
   - Run `python3 test_post_message.py CHANNEL_ID` in the `test-endpoint/` directory
   - If authentication fails, get a new bot token from Slack app settings

3. **Check Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/SlackAppStack-SlackEventFunction93C02593-b63WSAE4Pun4 --follow
   ```
   Look for error messages in the logs

4. **Verify Event Subscriptions:**
   - Make sure `app_mentions:read` event is subscribed in Slack app settings
   - Verify the Request URL matches your deployed Lambda URL

### `invalid_auth` Error

This usually means:
- Bot token is invalid or has been regenerated
- Bot token doesn't have the required OAuth scopes (`chat:write`, `app_mentions:read`)
- Redeploy with the correct bot token:
  ```bash
  export SLACK_BOT_TOKEN='xoxb-your-new-token'
  cd slack-app
  ./deploy.sh
  ```

### `not_in_channel` Error

The bot needs to be added to the channel:
```
/invite @your-bot-name
```
