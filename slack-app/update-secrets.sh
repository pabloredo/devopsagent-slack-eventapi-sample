#!/bin/bash
set -e

echo "Updating Slack App Secrets in AWS Secrets Manager..."

# Check if required environment variables are set
if [ -z "$SLACK_SIGNING_SECRET" ]; then
    echo "Error: SLACK_SIGNING_SECRET environment variable is not set."
    exit 1
fi

if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "Error: SLACK_BOT_TOKEN environment variable is not set."
    exit 1
fi

if [ -z "$WEBHOOK_SECRET" ]; then
    echo "Error: WEBHOOK_SECRET environment variable is not set."
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: WEBHOOK_URL environment variable is not set."
    exit 1
fi

SECRET_NAME="slack-app/credentials"

# Create JSON secret string
SECRET_STRING=$(cat <<EOF
{
  "SLACK_SIGNING_SECRET": "$SLACK_SIGNING_SECRET",
  "SLACK_BOT_TOKEN": "$SLACK_BOT_TOKEN",
  "WEBHOOK_SECRET": "$WEBHOOK_SECRET",
  "WEBHOOK_URL": "$WEBHOOK_URL"
}
EOF
)

# Try to create the secret, if it exists, update it
echo "Creating or updating secret: $SECRET_NAME"

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" 2>/dev/null; then
    echo "Secret exists, updating..."
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$SECRET_STRING"
    echo "✅ Secret updated successfully"
else
    echo "Secret does not exist, creating..."
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Slack app and webhook credentials" \
        --secret-string "$SECRET_STRING"
    echo "✅ Secret created successfully"
fi

echo ""
echo "Secret ARN:"
aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --query 'ARN' --output text
