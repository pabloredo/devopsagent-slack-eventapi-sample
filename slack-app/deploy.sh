#!/bin/bash
set -e

echo "Deploying Slack Event API Handler with CDK..."

# Check if SLACK_SIGNING_SECRET is set
if [ -z "$SLACK_SIGNING_SECRET" ]; then
    echo "Error: SLACK_SIGNING_SECRET environment variable is not set."
    echo "Set it with: export SLACK_SIGNING_SECRET='your-signing-secret'"
    exit 1
fi

# Check if SLACK_BOT_TOKEN is set
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "Error: SLACK_BOT_TOKEN environment variable is not set."
    echo "Set it with: export SLACK_BOT_TOKEN='your-bot-token'"
    exit 1
fi

# Check if WEBHOOK_SECRET is set
if [ -z "$WEBHOOK_SECRET" ]; then
    echo "Error: WEBHOOK_SECRET environment variable is not set."
    echo "Set it with: export WEBHOOK_SECRET='your-webhook-secret'"
    exit 1
fi

# Check if WEBHOOK_URL is set
if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: WEBHOOK_URL environment variable is not set."
    echo "Set it with: export WEBHOOK_URL='your-webhook-url'"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Bootstrap CDK if needed (only needs to be done once per account/region)
echo "Checking CDK bootstrap..."
cdk bootstrap || echo "Bootstrap already done or failed - continuing..."

# Deploy
echo "Synthesizing CDK stack..."
cdk synth

echo "Deploying to AWS..."
cdk deploy --require-approval never

echo ""
echo "Deployment complete!"
echo ""
echo "Your Slack Event API URL will be shown in the outputs above."
