#!/usr/bin/env python3
import os
import aws_cdk as cdk
from bedrock_kb_sync.bedrock_kb_sync_stack import BedrockKbSyncStack

app = cdk.App()

# Get configuration from context or use defaults
schedule_expression = app.node.try_get_context('schedule_expression') or 'cron(0 0 * * ? *)'
kb_ids_parameter_name = app.node.try_get_context('kb_ids_parameter_name') or '/bedrock/kb/autosync/ids'

BedrockKbSyncStack(
    app, 
    "BedrockKbSyncStack",
    schedule_expression=schedule_expression,
    kb_ids_parameter_name=kb_ids_parameter_name,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION")
    )
)

app.synth()
