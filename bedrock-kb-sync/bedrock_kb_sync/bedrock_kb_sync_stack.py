from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
)
from constructs import Construct

class BedrockKbSyncStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, 
                 schedule_expression: str = None,
                 kb_ids_parameter_name: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Default schedule is daily at midnight UTC if not specified
        schedule_expression = schedule_expression or 'cron(0 0 * * ? *)'
        kb_ids_parameter_name = kb_ids_parameter_name or '/bedrock/kb/ids'
        
        # Create the Lambda function that will trigger the KB sync
        sync_lambda = lambda_.Function(
            self, 'BedrockKbSyncLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='kb_sync_handler.handler',
            code=lambda_.Code.from_asset('lambda/kb_sync'),
            environment={
                'KB_IDS_PARAMETER_NAME': kb_ids_parameter_name
            },
            timeout=Duration.minutes(5)
        )
        
        # Grant the Lambda function permission to read from SSM Parameter Store
        sync_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=['ssm:GetParameter'],
            resources=[
                f'arn:aws:ssm:{self.region}:{self.account}:parameter{kb_ids_parameter_name}'
            ]
        ))
        
        # Grant the Lambda function permission to start ingestion jobs
        sync_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                'bedrock:StartIngestionJob',
                'bedrock:GetIngestionJob'
            ],
            resources=['*']  # You can restrict this to specific knowledge bases if needed
        ))
        
        # Create the EventBridge rule to trigger the Lambda on schedule
        rule = events.Rule(
            self, 'BedrockKbSyncRule',
            schedule=events.Schedule.expression(schedule_expression),
            description='Triggers the Bedrock Knowledge Base sync on a schedule'
        )
        
        # Add the Lambda as a target for the rule
        rule.add_target(targets.LambdaFunction(sync_lambda))
