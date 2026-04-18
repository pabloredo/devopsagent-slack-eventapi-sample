#!/bin/bash
set -e

echo "Deploying Slack Event API Handler with CDK..."

# Check if SLACK_SIGNING_SECRET is set
if [ -z "$SLACK_SIGNING_SECRET" ]; then
    echo "Error: SLACK_SIGNING_SECRET environment variable is not set."
    echo "Set it with: export SLACK_SIGNING_SECRET='your-signing-secret'"
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
