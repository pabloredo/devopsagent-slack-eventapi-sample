#!/usr/bin/env python3
import os
import aws_cdk as cdk
from slack_app_stack import SlackAppStack

app = cdk.App()

SlackAppStack(
    app,
    "SlackAppStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    )
)

app.synth()
