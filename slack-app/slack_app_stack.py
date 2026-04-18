import os
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_logs as logs,
)
from constructs import Construct


class SlackAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get Slack signing secret from context or environment
        slack_signing_secret = self.node.try_get_context('slackSigningSecret') or \
                               os.getenv('SLACK_SIGNING_SECRET') or \
                               'REPLACE_WITH_YOUR_SIGNING_SECRET'

        # Lambda function for handling Slack events
        slack_event_function = _lambda.Function(
            self,
            "SlackEventFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(
                ".",
                exclude=[
                    "cdk.out",
                    "*.pyc",
                    "__pycache__",
                    ".pytest_cache",
                    ".venv",
                    "venv",
                    "*.md",
                    ".git*",
                    "*.yaml",
                    "*.toml",
                    "*.sh",
                    "app.py",
                    "slack_app_stack.py",
                    "requirements.txt"
                ]
            ),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                'SLACK_SIGNING_SECRET': slack_signing_secret,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # API Gateway
        api = apigateway.RestApi(
            self,
            "SlackEventApi",
            rest_api_name="Slack Event API",
            description="API Gateway for Slack Event API",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_burst_limit=100,
                throttling_rate_limit=50,
            ),
        )

        # Create /slack/events endpoint
        slack_resource = api.root.add_resource("slack")
        events_resource = slack_resource.add_resource("events")

        # Integrate Lambda with API Gateway
        integration = apigateway.LambdaIntegration(slack_event_function)
        events_resource.add_method("POST", integration)

        # Outputs
        CfnOutput(
            self,
            "ApiUrl",
            value=f"{api.url}slack/events",
            description="Slack Event API URL",
            export_name="SlackEventApiUrl",
        )

        CfnOutput(
            self,
            "FunctionName",
            value=slack_event_function.function_name,
            description="Lambda Function Name",
        )
